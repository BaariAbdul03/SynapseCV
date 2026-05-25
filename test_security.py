import io
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_mime_spoofing():
    print("Testing MIME type spoofing validation...")
    # Construct a fake PDF (just a plain text file renamed to .pdf)
    fake_file_stream = io.BytesIO(b"Hello world, I am not a PDF file")
    files = {
        'resume': ('spoofed_pdf.pdf', fake_file_stream, 'application/pdf')
    }
    data = {
        'job_description': 'Software Engineer'
    }
    
    response = requests.post(f"{BASE_URL}/parse", files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "Invalid file content" in response.json().get("error", "")
    print("MIME spoofing validation PASSED!\n")

def test_oversized_job_description():
    print("Testing oversized job description validation...")
    # Construct a valid PDF signature, but send a massive JD
    valid_pdf_stream = io.BytesIO(b"%PDF-1.5\n%EOF\n" + b"A" * 100)
    files = {
        'resume': ('valid.pdf', valid_pdf_stream, 'application/pdf')
    }
    # 6,000 character job description
    data = {
        'job_description': 'A' * 6000
    }
    
    response = requests.post(f"{BASE_URL}/parse", files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400
    assert "Job description exceeds maximum allowed length" in response.json().get("error", "")
    print("Oversized JD validation PASSED!\n")

def test_security_headers():
    print("Testing HTTP security headers...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    
    # Obscured server signature check
    server_header = response.headers.get("Server")
    print(f"Server header: {server_header}")
    assert "SynapseCV" in server_header
    
    # Robots tag check
    robots_header = response.headers.get("X-Robots-Tag")
    print(f"X-Robots-Tag: {robots_header}")
    assert robots_header == "noindex, nofollow"
    
    print("HTTP security headers checking PASSED!\n")

if __name__ == "__main__":
    try:
        test_mime_spoofing()
        test_oversized_job_description()
        test_security_headers()
        print("ALL SECURITY VALIDATION TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"Test failed! Assertion error: {e}")
    except Exception as e:
        print(f"Test errored! Exception: {e}")
