import logging
import io
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, current_app, request, jsonify
from flask_login import current_user
from app.extensions import limiter, db
from app.services.pdf_service import extract_text_from_pdf
from app.services.gemini_service import GeminiService
from app.utils.validators import validate_pdf_mime
from app.models import Analysis

logger = logging.getLogger(__name__)
parse_bp = Blueprint('parse', __name__)

# Initialize the Gemini service
gemini_service = GeminiService()


def ensure_gemini_configured():
    """Configure Gemini in the request thread before any worker threads run."""
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return False
    if not gemini_service._is_configured:
        gemini_service.configure(api_key)
    return gemini_service._is_configured


def parse_single_resume_object(filename, stream, jd_text):
    """
    Worker function executed in a concurrent thread.
    Performs PDF extraction and calls Gemini service safely.
    """
    try:
        # Validate MIME signature
        stream.seek(0)
        if not validate_pdf_mime(stream):
            return {"filename": filename, "error": "Invalid file content. Not a valid PDF."}
            
        stream.seek(0)
        resume_text = extract_text_from_pdf(stream)
        if not resume_text:
            return {"filename": filename, "error": "Failed to read or extract printable text from PDF."}
            
        # Call Gemini AI API
        extracted_data = gemini_service.analyze_resume(resume_text, jd_text)
        if not extracted_data:
            return {"filename": filename, "error": "AI model failed to analyze resume contents."}
            
        extracted_data["filename"] = filename
        return extracted_data
    except Exception as e:
        logger.error(f"Error parsing resume {filename}: {e}", exc_info=True)
        return {"filename": filename, "error": f"Internal parser error: {str(e)}"}


@parse_bp.route('/parse', methods=['POST'])
@limiter.limit("10 per minute")
def parse_resume():
    """
    Parses single or batch uploaded resumes against a job description.
    Supports up to 10 files concurrently using ThreadPoolExecutor.
    """
    try:
        if not ensure_gemini_configured():
            return jsonify({
                "error": "AI parser is not configured. Please set GEMINI_API_KEY in Render."
            }), 503

        # P1.1: File presence validation
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        files = request.files.getlist("resume")
        jd_text = request.form.get('job_description', '').strip()

        # P1.1: Enforce JD max character limit
        if len(jd_text) > 5000:
            return jsonify({"error": "Job description exceeds maximum allowed length of 5000 characters."}), 400

        # Read streams into memory buffers for thread safety
        file_payloads = []
        for file in files:
            if file and file.filename != '':
                if not file.filename.lower().endswith('.pdf'):
                    return jsonify({"error": f"Invalid format for '{file.filename}'. Only PDF files are accepted."}), 400
                
                # Buffer the stream in memory
                buffered_stream = io.BytesIO(file.read())
                file_payloads.append((file.filename, buffered_stream))

        if not file_payloads:
            return jsonify({"error": "No selected files detected"}), 400

        if len(file_payloads) > 10:
            return jsonify({"error": "Batch parsing is limited to a maximum of 10 resumes per scan."}), 400

        # Determine single vs batch execution path
        if len(file_payloads) == 1:
            filename, stream = file_payloads[0]
            result = parse_single_resume_object(filename, stream, jd_text)
            
            if "error" in result:
                return jsonify({"error": result["error"]}), 400
                
            # Sequentially save single record to database if authenticated
            if current_user.is_authenticated:
                try:
                    analysis = Analysis(
                        user_id=current_user.id,
                        candidate_name=result.get("name"),
                        detected_role=result.get("detected_role"),
                        match_percentage=result.get("match_percentage"),
                        email=result.get("email"),
                        phone=result.get("phone"),
                        github_url=result.get("github_url"),
                        linkedin_url=result.get("linkedin_url"),
                        education=result.get("education"),
                        skills=result.get("skills"),
                        missing_keywords=result.get("missing_keywords"),
                        profile_summary=result.get("profile_summary"),
                        scoring_reasoning=result.get("scoring_reasoning")
                    )
                    db.session.add(analysis)
                    db.session.commit()
                    result["db_id"] = analysis.id
                except Exception as db_err:
                    db.session.rollback()
                    logger.error(f"Database archive failed: {db_err}", exc_info=True)
            
            return jsonify(result)
            
        else:
            # Concurrently parse batch payloads using a bounded ThreadPoolExecutor
            completed_results = []
            with ThreadPoolExecutor(max_workers=min(len(file_payloads), 5)) as executor:
                futures = [
                    executor.submit(parse_single_resume_object, filename, stream, jd_text)
                    for filename, stream in file_payloads
                ]
                for future in futures:
                    completed_results.append(future.result())

            # Sequentially save successful analyses to the database in the main thread to avoid SQLite locking
            saved_count = 0
            if current_user.is_authenticated:
                for res in completed_results:
                    if "error" not in res:
                        try:
                            analysis = Analysis(
                                user_id=current_user.id,
                                candidate_name=res.get("name"),
                                detected_role=res.get("detected_role"),
                                match_percentage=res.get("match_percentage"),
                                email=res.get("email"),
                                phone=res.get("phone"),
                                github_url=res.get("github_url"),
                                linkedin_url=res.get("linkedin_url"),
                                education=res.get("education"),
                                skills=res.get("skills"),
                                missing_keywords=res.get("missing_keywords"),
                                profile_summary=res.get("profile_summary"),
                                scoring_reasoning=res.get("scoring_reasoning")
                            )
                            db.session.add(analysis)
                            db.session.commit()
                            res["db_id"] = analysis.id
                            saved_count += 1
                        except Exception as db_err:
                            db.session.rollback()
                            logger.error(f"Database archive failed during batch save: {db_err}", exc_info=True)

            # Sort batch results by match percentage descending (Ranked Leaderboard)
            successful_parses = [r for r in completed_results if "error" not in r]
            failed_parses = [r for r in completed_results if "error" in r]
            
            successful_parses.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
            
            # Form ranked list
            ranked_results = successful_parses + failed_parses

            return jsonify({
                "is_batch": True,
                "results": ranked_results,
                "total_processed": len(file_payloads),
                "successful_count": len(successful_parses),
                "failed_count": len(failed_parses)
            })

    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500
