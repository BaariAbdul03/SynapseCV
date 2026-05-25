import re
import logging

logger = logging.getLogger(__name__)

# Make magic optional since OS-level libmagic is often missing in serverless/cloud environments
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic library could not find system libmagic. Falling back to native binary signature validation.")

def sanitize_text(text: str) -> str:
    """
    Sanitizes extracted PDF text before processing:
    - Strips null bytes
    - Strips control characters (except common whitespace like tabs, newlines, carriage returns)
    """
    if not text:
        return ""
    # Strip null bytes
    text = text.replace("\x00", "")
    # Strip control characters except whitespace (\t, \n, \r)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    return text.strip()

def validate_pdf_mime(file_stream) -> bool:
    """
    Validates a file stream's MIME type using magic number detection server-side.
    Avoids extension spoofing vulnerability.
    Uses native %PDF header check and falls back to python-magic if available.
    """
    try:
        # 1. High-speed, dependency-free binary header check
        header_4 = file_stream.read(4)
        file_stream.seek(0)  # Rewind the file stream immediately
        
        # Valid PDF files always start with %PDF
        if header_4 == b'%PDF':
            return True
            
        # 2. Fallback to magic check if the header is shifted or complex
        if HAS_MAGIC:
            header_2048 = file_stream.read(2048)
            file_stream.seek(0)  # Rewind
            mime = magic.from_buffer(header_2048, mime=True)
            logger.info(f"Magic detected MIME type: {mime}")
            return mime == 'application/pdf'
            
        logger.warning("Native signature mismatch and python-magic unavailable.")
        return False
    except Exception as e:
        logger.error(f"Error during MIME validation: {e}", exc_info=True)
        return False
