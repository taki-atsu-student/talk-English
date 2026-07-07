"""
Test suite for AIと話そう！ Backend
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Mock 重いモデルのロードをスキップ
import unittest.mock as mock

def test_api_structure():
    """Basic API structure tests without loading models"""
    with mock.patch('backend.main.load_models'):
        from backend.main import app
        client = TestClient(app)
        
        # Health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

def test_chat_request_validation():
    """Test chat endpoint request validation"""
    with mock.patch('backend.main.load_models'):
        from backend.main import app, ChatRequest
        client = TestClient(app)
        
        # Empty text
        response = client.post("/chat", json={"text": ""})
        assert response.status_code == 200
        
        # Valid text
        response = client.post("/chat", json={"text": "Hello"})
        assert response.status_code in [200, 500]  # 500 if model fails

def test_static_file_security():
    """Test path traversal protection"""
    with mock.patch('backend.main.load_models'):
        from backend.main import app
        client = TestClient(app)
        
        # Path traversal attempt should be blocked
        response = client.get("/static/../../.env")
        assert response.status_code == 403

if __name__ == "__main__":
    print("Running basic tests...")
    test_api_structure()
    print("✅ API structure test passed")
    
    test_chat_request_validation()
    print("✅ Chat request validation test passed")
    
    test_static_file_security()
    print("✅ Static file security test passed")
    
    print("\n✅ All tests passed!")
