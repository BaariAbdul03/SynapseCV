import json
import logging
import time
from flask import current_app, has_app_context
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

MAX_RESUME_TEXT_CHARS = 30000


class GeminiService:
    """Service to interact with Google Gemini models with resilience and structured analysis."""
    
    PRIMARY_MODEL = "gemini-2.5-flash"
    FALLBACK_MODEL = "gemini-2.0-flash-lite"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._is_configured = False
        if api_key:
            self.configure(api_key)
            
    def configure(self, api_key: str):
        """Configure the Gemini SDK."""
        try:
            genai.configure(api_key=api_key)
            self._is_configured = True
            logger.info("Gemini Service configured successfully.")
        except Exception as e:
            logger.error(f"Failed to configure Gemini Service: {e}", exc_info=True)
            self._is_configured = False

    def _get_model(self, model_name: str):
        """Returns the configured model instance."""
        if not self._is_configured:
            # Try loading from app config if dynamically loaded
            api_key = current_app.config.get("GEMINI_API_KEY")
            if api_key:
                self.configure(api_key)
            else:
                raise ValueError("Gemini Service is not configured. Missing API Key.")
        return genai.GenerativeModel(model_name)

    def _get_request_timeout(self) -> float:
        if has_app_context():
            return float(current_app.config.get("GEMINI_TIMEOUT", 25.0))
        return 25.0

    def _get_retry_count(self) -> int:
        if has_app_context():
            return int(current_app.config.get("GEMINI_RETRIES", 1))
        return 3

    def analyze_resume(self, resume_text: str, jd_text: str = "") -> dict:
        """
        Analyzes a resume against an optional job description using a strict penalty system.
        Retries with exponential backoff on transient errors and falls back to a lighter model if necessary.
        """
        scoring_logic = """
        SCORING ALGORITHM (STRICT PENALTY SYSTEM):
        1. **Start with a Base Score of 100.**
        2. **Detect the Target Role** (inferred from resume or provided JD).
        3. **Apply Deductions (The 'Deal Breakers'):**
           - **CRITICAL SKILL GAP (-25 points):** If the candidate is missing a FOUNDATIONAL skill for their specific role.
             * Example: 'Full Stack Dev' missing Databases (SQL/NoSQL).
             * Example: 'Data Scientist' missing Python/R.
             * Example: 'Marketer' missing SEO/Analytics.
           - **EXPERIENCE GAP (-10 points):** If bullet points are vague, generic, or lack quantifiable metrics (numbers/%).
           - **FORMATTING (-5 points):** If the layout is messy or missing basic contact info.
        4. **Final Calculation:** Score = 100 - Total Deductions. (Minimum 0).
        """

        context = (
            f"CONTEXT: Analyze the resume against this JOB DESCRIPTION: '{jd_text}'"
            if jd_text.strip()
            else "CONTEXT: No Job Description provided. INFER the target role from the resume content first."
        )

        truncated_resume_text = resume_text[:MAX_RESUME_TEXT_CHARS]
        if len(resume_text) > MAX_RESUME_TEXT_CHARS:
            truncated_resume_text += "\n\n[Resume text truncated for processing safety.]"

        prompt = f"""
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
        - "education": List of cleanly formatted strings. Format each entry as: "Degree — Field of Study (Score%), Institution, Year". Use proper spacing around dashes and commas. Example: ["B.Tech — Computer Science (82.13%), R.R. Institute, AKTU, 2022-2026", "Intermediate (12th Grade, I.S.C) — 69.8%, Spring Dale College, 2022"]
        - "skills": List of strings (All technical skills found)

        ---
        TASK 2: EVALUATION
        {scoring_logic}

        CRITICAL CONSISTENCY RULE: The "match_percentage" number in your JSON output MUST EXACTLY EQUAL the final score computed in your "scoring_reasoning" text. If your reasoning says "Final: 65", then match_percentage MUST be 65. Any mismatch is unacceptable.

        ---
        OUTPUT FORMAT (MANDATORY):
        Return ONLY a valid JSON object. Do not add markdown blocks.
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
        {truncated_resume_text}
        """

        return self._execute_with_retry(prompt)

    def _execute_with_retry(self, prompt: str, model_name: str = None) -> dict:
        """Helper to run request with exponential backoff and fallback model."""
        retries = self._get_retry_count()
        delay = 1.0
        current_model = model_name or self.PRIMARY_MODEL
        
        for attempt in range(retries + 1):
            try:
                logger.info(f"Sending prompt to Gemini using {current_model} (attempt {attempt + 1})...")
                model_inst = self._get_model(current_model)
                
                # Dynamic timeout handling
                # google-generativeai client supports a timeout via client options, but for ease,
                # we let the SDK call resolve or time out on standard system connection.
                response = model_inst.generate_content(
                    prompt, 
                    generation_config={"temperature": 0.0},
                    request_options={"timeout": self._get_request_timeout()}
                )
                
                if not response or not response.text:
                    raise GoogleAPIError("Empty response from Gemini API.")
                
                # Parse and clean response
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```"):
                    # Remove markdown JSON blocks if present
                    cleaned_text = cleaned_text.replace("```json", "", 1)
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()
                
                return json.loads(cleaned_text)
                
            except (GoogleAPIError, json.JSONDecodeError, Exception) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # If we've reached the last retry, raise the exception or try the fallback
                if attempt == retries:
                    if current_model == self.PRIMARY_MODEL:
                        logger.error("Primary model failed. Attempting fallback model...")
                        # Reset retry loop for fallback model by passing it forward
                        return self._execute_with_retry(prompt, model_name=self.FALLBACK_MODEL)
                    raise e
                
                # Exponential backoff
                time.sleep(delay)
                delay *= 2.0
                
        raise GoogleAPIError("Gemini call failed after retries.")
