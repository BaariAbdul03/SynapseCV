import re
import logging
import magic

logger = logging.getLogger(__name__)

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
    """
    try:
        # Read the first 2048 bytes for signature checking
        header = file_stream.read(2048)
        file_stream.seek(0)  # Rewind the file stream immediately
        
        # Check MIME type
        mime = magic.from_buffer(header, mime=True)
        logger.info(f"Magic detected MIME type: {mime}")
        
        return mime == 'application/pdf'
    except Exception as e:
        logger.error(f"Error during MIME validation: {e}", exc_info=True)
        return False
