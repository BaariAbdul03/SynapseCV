import json
from unittest.mock import MagicMock, patch
import pytest
from google.api_core.exceptions import GoogleAPIError
from app.services.gemini_service import GeminiService

@pytest.fixture
def gemini_service():
    """Create a test gemini service instance with mock setup."""
    svc = GeminiService(api_key="mock_key")
    svc._is_configured = True
    return svc

def test_analyze_resume_success(gemini_service):
    """Verify successful parsing returns parsed JSON dictionary."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1 234 567",
        "education": ["BS CS"],
        "skills": ["Python", "Flask"],
        "match_percentage": 85,
        "detected_role": "Full Stack Dev",
        "missing_keywords": ["SQL"],
        "profile_summary": "Summary...",
        "scoring_reasoning": "Reason..."
    })
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    with patch.object(gemini_service, "_get_model", return_value=mock_model):
        results = gemini_service.analyze_resume("Resume content...", "JD...")
        assert results["name"] == "Jane Doe"
        assert results["match_percentage"] == 85
        assert "jane@example.com" in results["email"]

def test_gemini_resiliency_backoff_success(gemini_service):
    """Verify service retries on transient errors and succeeds."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({"name": "Jane Doe", "match_percentage": 90})
    
    mock_model = MagicMock()
    # Mocking generate_content to throw GoogleAPIError twice, then return success on 3rd attempt
    mock_model.generate_content.side_effect = [
        GoogleAPIError("Quota exceeded"),
        GoogleAPIError("Temporary unavailable"),
        mock_response
    ]
    
    with patch.object(gemini_service, "_get_model", return_value=mock_model):
        with patch("app.services.gemini_service.time.sleep") as mock_sleep: # Fast mock sleep
            results = gemini_service.analyze_resume("Resume content...")
            assert results["name"] == "Jane Doe"
            assert mock_sleep.call_count == 2

def test_gemini_fallback_model(gemini_service):
    """Verify primary model total failure triggers the fallback lite model."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({"name": "Jane Doe", "match_percentage": 75})
    
    # Primary model throws exception continuously
    # Fallback model succeeds
    def mock_get_model(model_name):
        model = MagicMock()
        if model_name == gemini_service.PRIMARY_MODEL:
            model.generate_content.side_effect = GoogleAPIError("Unavailable")
        else:
            model.generate_content.return_value = mock_response
        return model

    with patch.object(gemini_service, "_get_model", side_effect=mock_get_model):
        with patch("app.services.gemini_service.time.sleep"):
            results = gemini_service.analyze_resume("Resume content...")
            assert results["name"] == "Jane Doe"
            assert results["match_percentage"] == 75
