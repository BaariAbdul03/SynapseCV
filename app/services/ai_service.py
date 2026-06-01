"""
Unified AI Resume Analysis Service
====================================
3-Tier resilient AI pipeline:
  1. Groq (Llama 4 Scout)      – Primary   – Free, fast, generous limits
  2. Gemini 2.5 Flash           – Secondary – Fallback if Groq unavailable
  3. Gemini 2.0 Flash           – Tertiary  – Last resort

The service automatically cascades down the chain on quota errors (429),
connection failures, or invalid JSON responses.
"""

import json
import logging
import time
import re

from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

MAX_RESUME_TEXT_CHARS = 30_000


# ---------------------------------------------------------------------------
# Shared prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(resume_text: str, jd_text: str) -> str:
    scoring_logic = """
    SCORING ALGORITHM (STRICT PENALTY SYSTEM):
    1. Start with a Base Score of 100.
    2. Detect the Target Role (inferred from resume or provided JD).
    3. Apply Deductions:
       - CRITICAL SKILL GAP (-25 pts): Missing a FOUNDATIONAL skill for the role.
           e.g. Full Stack Dev missing SQL; Data Scientist missing Python.
       - EXPERIENCE GAP (-10 pts): Bullet points vague, generic, or lack quantifiable metrics.
       - FORMATTING (-5 pts): Layout messy or missing basic contact info.
    4. Final Score = 100 - Total Deductions. (Minimum 0.)
    """

    context = (
        f"CONTEXT: Analyse the resume against this JOB DESCRIPTION: '{jd_text}'"
        if jd_text.strip()
        else "CONTEXT: No Job Description provided. INFER the target role from the resume content first."
    )

    truncated = resume_text[:MAX_RESUME_TEXT_CHARS]
    if len(resume_text) > MAX_RESUME_TEXT_CHARS:
        truncated += "\n\n[Resume text truncated for processing safety.]"

    return f"""
You are a ruthless, industry-standard AI Resume Parser.
You have TWO mandatory tasks.

{context}

---
TASK 1: EXTRACTION
Extract these exact details. Return "Not Found" if missing.
- "name": Full Name
- "email": Email Address
- "phone": Phone Number
- "github_url": GitHub profile URL (e.g. https://github.com/username). Return "Not Found" if not present.
- "linkedin_url": LinkedIn profile URL (e.g. https://linkedin.com/in/username). Return "Not Found" if not present.
- "education": List of cleanly formatted strings. Format: "Degree — Field (Score%), Institution, Year"
- "skills": List of strings (all technical skills found)

---
TASK 2: EVALUATION
{scoring_logic}

CRITICAL CONSISTENCY RULE: The "match_percentage" number in your JSON output MUST EXACTLY EQUAL
the final score computed in your "scoring_reasoning" text. Any mismatch is unacceptable.

---
OUTPUT FORMAT (MANDATORY):
Return ONLY a valid JSON object. Do NOT wrap it in markdown code blocks.
{{
    "name": "...",
    "email": "...",
    "phone": "...",
    "github_url": "...",
    "linkedin_url": "...",
    "education": ["..."],
    "skills": ["..."],
    "match_percentage": 0,
    "detected_role": "...",
    "missing_keywords": ["..."],
    "profile_summary": "...",
    "scoring_reasoning": "Started at 100. Deducted 25 for missing SQL. Deducted 10 for vague metrics. Final: 65."
}}

---
RESUME TEXT:
{truncated}
""".strip()


def _clean_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON robustly."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# Tier 1 – Groq (Llama)
# ---------------------------------------------------------------------------

class GroqService:
    """Groq-backed resume analysis using Llama 4 Scout with JSON mode."""

    PRIMARY_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
    FALLBACK_MODEL = "llama3-70b-8192"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client:
            return self._client
        try:
            from groq import Groq  # lazy import — only needed if Groq is configured
        except ImportError:
            raise RuntimeError("groq package is not installed. Add 'groq' to requirements.txt.")

        api_key = None
        if has_app_context():
            api_key = current_app.config.get("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self._client = Groq(api_key=api_key)
        return self._client

    def _call(self, prompt: str, model: str) -> dict:
        client = self._get_client()
        logger.info(f"[Groq] Calling model={model}")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI resume parser. "
                        "Always respond with a single valid JSON object matching the schema given by the user. "
                        "Never add commentary, markdown, or extra text outside the JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        raw = response.choices[0].message.content
        return _clean_json_response(raw)

    def analyze(self, resume_text: str, jd_text: str) -> dict:
        prompt = _build_prompt(resume_text, jd_text)
        try:
            return self._call(prompt, self.PRIMARY_MODEL)
        except Exception as e:
            logger.warning(f"[Groq] Primary model failed ({e}). Trying fallback.")
            return self._call(prompt, self.FALLBACK_MODEL)


# ---------------------------------------------------------------------------
# Tier 2 & 3 – Gemini
# ---------------------------------------------------------------------------

class GeminiService:
    """Gemini-backed resume analysis (secondary / tertiary fallback)."""

    PRIMARY_MODEL = "gemini-2.5-flash-preview-05-20"
    FALLBACK_MODEL = "gemini-2.0-flash"

    def __init__(self):
        self._configured = False

    def _ensure_configured(self):
        if self._configured:
            return
        try:
            import google.generativeai as genai  # noqa
        except ImportError:
            raise RuntimeError("google-generativeai is not installed.")

        api_key = None
        if has_app_context():
            api_key = current_app.config.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._configured = True

    def _call(self, prompt: str, model_name: str) -> dict:
        import google.generativeai as genai
        self._ensure_configured()
        logger.info(f"[Gemini] Calling model={model_name}")

        timeout = 30.0
        if has_app_context():
            timeout = float(current_app.config.get("GEMINI_TIMEOUT", 30.0))

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.0},
            request_options={"timeout": timeout},
        )
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API.")
        return _clean_json_response(response.text)

    def analyze(self, resume_text: str, jd_text: str, model_name: str = None) -> dict:
        model = model_name or self.PRIMARY_MODEL
        prompt = _build_prompt(resume_text, jd_text)
        retries = 2
        delay = 1.0
        last_error = None

        for attempt in range(retries + 1):
            try:
                return self._call(prompt, model)
            except Exception as e:
                last_error = e
                logger.warning(f"[Gemini] model={model} attempt {attempt + 1} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
                    delay *= 2.0

        # Try fallback Gemini model if primary failed
        if model == self.PRIMARY_MODEL:
            logger.warning(f"[Gemini] Switching to fallback model {self.FALLBACK_MODEL}")
            return self.analyze(resume_text, jd_text, model_name=self.FALLBACK_MODEL)

        raise last_error


# ---------------------------------------------------------------------------
# Unified Facade  ← this is what the rest of the app imports
# ---------------------------------------------------------------------------

class AIService:
    """
    3-Tier AI facade:
      Tier 1 → Groq (Llama 4 Scout)     [primary, fastest, free quota]
      Tier 2 → Gemini 2.5 Flash          [secondary]
      Tier 3 → Gemini 2.0 Flash          [last resort]

    Falls back automatically on any error.
    """

    def __init__(self):
        self._groq = GroqService()
        self._gemini = GeminiService()

    def analyze_resume(self, resume_text: str, jd_text: str = "") -> dict:
        """Public entry point — tries Groq first, cascades to Gemini on failure."""

        # ── Tier 1: Groq ────────────────────────────────────────────────────
        try:
            result = self._groq.analyze(resume_text, jd_text)
            logger.info("[AIService] Analysis completed via Groq (Tier 1).")
            return result
        except Exception as groq_err:
            logger.warning(f"[AIService] Groq unavailable: {groq_err}. Falling back to Gemini.")

        # ── Tier 2 + 3: Gemini (handles its own internal fallback) ──────────
        try:
            result = self._gemini.analyze(resume_text, jd_text)
            logger.info("[AIService] Analysis completed via Gemini (Tier 2/3).")
            return result
        except Exception as gemini_err:
            logger.error(f"[AIService] All AI providers exhausted. Final error: {gemini_err}", exc_info=True)
            raise RuntimeError(
                f"All AI providers are currently unavailable. Please try again later. "
                f"Last error: {gemini_err}"
            )
