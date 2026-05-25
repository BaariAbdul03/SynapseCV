import io
import unittest
import hashlib
from app import create_app
from app.extensions import db
from app.models import User, ApiKey

class TestSynapseCVAPI(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a test recruiter user
            self.test_user = User(email="recruiter@synapsecv.io")
            self.test_user.set_password("SecurePassword123")
            db.session.add(self.test_user)
            db.session.commit()
            
            # Generate a Stripe-style test API key
            self.plaintext_key = "scv_live_testtoken1234567890"
            key_hash = hashlib.sha256(self.plaintext_key.encode()).hexdigest()
            
            self.api_key = ApiKey(
                user_id=self.test_user.id,
                name="Test Dev Key",
                key_prefix="scv_live_test",
                key_hash=key_hash
            )
            db.session.add(self.api_key)
            db.session.commit()
            
            self.user_id = self.test_user.id

    def tearDown(self):
        """Clean up database."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_unauthorized_access(self):
        """Test API endpoints return 401 when no credentials are provided."""
        response = self.client.post('/api/v1/parse')
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.get_json()['error'])

    def test_invalid_key_access(self):
        """Test API endpoints return 401 with incorrect keys."""
        headers = {
            'Authorization': 'Bearer scv_live_wrongtoken'
        }
        response = self.client.post('/api/v1/parse', headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_x_api_key_header_authorization(self):
        """Test authorized request using X-API-Key header."""
        headers = {
            'X-API-Key': self.plaintext_key
        }
        fake_pdf = io.BytesIO(b"Plain text is not valid PDF")
        data = {
            'resume': (fake_pdf, 'test.pdf'),
            'job_description': 'Senior Developer'
        }
        
        response = self.client.post('/api/v1/parse', headers=headers, data=data, content_type='multipart/form-data')
        # Expecting 400 Bad Request due to PDF signature validation (not 401 Unauthorized)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file content", response.get_json()['error'])

    def test_bearer_authorization_header(self):
        """Test authorized request using Bearer Authorization header."""
        headers = {
            'Authorization': f'Bearer {self.plaintext_key}'
        }
        fake_pdf = io.BytesIO(b"Plain text is not valid PDF")
        data = {
            'resume': (fake_pdf, 'test.pdf'),
            'job_description': 'Senior Developer'
        }
        
        response = self.client.post('/api/v1/parse', headers=headers, data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid file content", response.get_json()['error'])

if __name__ == '__main__':
    unittest.main()
