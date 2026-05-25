from unittest.mock import MagicMock, patch
from app.services.pdf_service import extract_text_from_pdf

def test_extract_text_from_pdf_success():
    """Verify standard extraction works seamlessly when pages have valid text."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Candidate details: Jane Doe\nSkills: Python, Go"
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    
    with patch("pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        extracted = extract_text_from_pdf("mock_stream")
        assert "Jane Doe" in extracted
        assert "Python" in extracted

def test_extract_text_from_pdf_failure():
    """Verify the extraction returns an empty string cleanly on plumber exception."""
    with patch("pdfplumber.open", side_effect=Exception("Corrupt file")):
        extracted = extract_text_from_pdf("mock_stream")
        assert extracted == ""
