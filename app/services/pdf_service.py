import logging
import pdfplumber
from app.utils.validators import sanitize_text

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_stream) -> str:
    """
    Safely extracts text from a PDF file stream, then sanitizes it.
    Also extracts hyperlink URLs from PDF annotations (e.g., clickable
    "LinkedIn" / "GitHub" text) since pdfplumber only yields visible text.
    Returns:
        str: Cleaned text from the PDF, or empty string on failure.
    """
    try:
        raw_text = []
        link_urls = set()  # Collect unique hyperlink URLs from annotations
        
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text.append(page_text)
                
                # Extract hyperlink annotations (URI actions)
                if page.annots:
                    for annot in page.annots:
                        uri = annot.get("uri")
                        if uri and isinstance(uri, str):
                            link_urls.add(uri)
        
        full_text = "\n".join(raw_text)
        
        # Append discovered hyperlink URLs that aren't already in the text
        if link_urls:
            urls_to_append = [url for url in link_urls if url not in full_text]
            if urls_to_append:
                full_text += "\n\nEXTRACTED HYPERLINKS:\n" + "\n".join(urls_to_append)
        
        return sanitize_text(full_text)
    except Exception as e:
        logger.error(f"Error during PDF extraction: {e}", exc_info=True)
        return ""

