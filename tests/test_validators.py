import io
from app.utils.validators import sanitize_text, validate_pdf_mime

def test_sanitize_text():
    """Verify text is correctly sanitized by stripping null bytes and non-printable controls."""
    # Standard text
    assert sanitize_text("Hello World") == "Hello World"
    
    # Null bytes
    assert sanitize_text("Hello\x00World") == "HelloWorld"
    
    # Control characters but keeping standard tabs and newlines
    dirty_text = "Line 1\nLine 2\t\x07Text\x1b"
    assert sanitize_text(dirty_text) == "Line 1\nLine 2\tText"
    
    # Empty cases
    assert sanitize_text("") == ""
    assert sanitize_text(None) == ""

def test_validate_pdf_mime_real_pdf():
    """Verify MIME checker correctly recognizes valid PDF signature headers."""
    # Real PDF files start with %PDF- signature
    valid_pdf_stream = io.BytesIO(b"%PDF-1.5\n%EOF")
    assert validate_pdf_mime(valid_pdf_stream) is True

def test_validate_pdf_mime_invalid():
    """Verify MIME checker correctly rejects spoofed plain text files."""
    spoofed_stream = io.BytesIO(b"Hello World, I am a plain text file")
    assert validate_pdf_mime(spoofed_stream) is False
