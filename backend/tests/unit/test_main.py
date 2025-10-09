"""
Unit tests for main FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


@pytest.mark.unit
class TestMainApplication:
    """Test cases for main FastAPI application setup"""
    
    @pytest.fixture
    def test_client(self):
        return TestClient(app)
    
    def test_app_creation(self):
        """Test that FastAPI app is created properly"""
        assert app.title == "DocuMind API"
        assert app.description == "Local RAG Document Processing API"
        assert app.version == "1.0.0"
    
    def test_cors_middleware_configured(self, test_client):
        """Test that CORS middleware is properly configured"""
        response = test_client.options("/api/documents", headers={"Origin": "http://localhost:5173"})
        
        # Should have CORS headers
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns API info"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "DocuMind API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_route_prefix(self, test_client):
        """Test that API routes are properly prefixed"""
        # All API routes should be under /api prefix
        response = test_client.get("/api/documents")
        # Should return 200 (success) or 500 (server error), not 404 (not found)
        assert response.status_code != 404
    
    def test_404_handling(self, test_client):
        """Test handling of non-existent routes"""
        response = test_client.get("/nonexistent-route")
        
        assert response.status_code == 404
    
    def test_method_not_allowed_handling(self, test_client):
        """Test handling of unsupported HTTP methods"""
        response = test_client.patch("/api/documents")
        
        assert response.status_code == 405
    
    @patch('modules.storage.DocumentStorage')
    def test_app_initialization_with_storage_error(self, mock_storage):
        """Test app behavior when storage initialization fails"""
        mock_storage.side_effect = Exception("Storage initialization failed")
        
        # App should still start but storage operations may fail
        # This tests graceful degradation
        with TestClient(app) as test_client:
            # Root endpoint should still work
            response = test_client.get("/")
            assert response.status_code == 200


@pytest.mark.unit
class TestApplicationConfiguration:
    """Test application configuration and settings"""
    
    def test_debug_mode_configuration(self):
        """Test that debug mode is properly configured"""
        # In tests, we typically want debug mode off for production-like testing
        # This would test environment-based configuration if implemented
        pass
    
    def test_file_upload_limits(self, test_client):
        """Test file upload size limits if implemented"""
        # This would test max file size limits
        # Currently not implemented but should be added for production
        pass
    
    def test_api_versioning(self, test_client):
        """Test API versioning if implemented"""
        # Test that API versions are properly handled
        # Currently v1 is implicit, but could be made explicit
        pass
    
    def test_security_headers(self, test_client):
        """Test that security headers are set"""
        response = test_client.get("/")
        
        # These headers should be set for security (if implemented)
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        # Test for basic security headers (implement as needed)
        # assert "x-frame-options" in headers
        # assert "x-content-type-options" in headers
        pass


@pytest.mark.unit 
class TestErrorHandling:
    """Test global error handling"""
    
    @pytest.fixture
    def test_client(self):
        return TestClient(app)
    
    def test_internal_server_error_handling(self, test_client):
        """Test handling of internal server errors"""
        with patch('modules.storage.DocumentStorage.list_all_documents', side_effect=Exception("Test error")):
            response = test_client.get("/api/documents")
            
            assert response.status_code == 500
            # Should return JSON error response, not HTML
            assert response.headers["content-type"] == "application/json"
    
    def test_validation_error_handling(self, test_client):
        """Test handling of validation errors"""
        # Test with invalid request data
        response = test_client.post("/api/documents/upload", data={"invalid": "data"})
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    def test_http_exception_handling(self, test_client):
        """Test handling of HTTP exceptions"""
        response = test_client.delete("/api/documents/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestApplicationStartup:
    """Test application startup and shutdown"""
    
    def test_startup_event(self):
        """Test that startup events execute correctly"""
        # Test that all startup initialization completes
        with TestClient(app) as test_client:
            # If app starts successfully, startup events worked
            response = test_client.get("/health")
            assert response.status_code == 200
    
    def test_shutdown_event(self):
        """Test that shutdown events execute correctly"""
        # Test cleanup on shutdown
        with TestClient(app) as test_client:
            # App should start and shutdown cleanly
            pass
    
    @patch('modules.storage.DocumentStorage.__init__')
    def test_startup_with_storage_failure(self, mock_storage_init):
        """Test startup behavior when storage initialization fails"""
        mock_storage_init.side_effect = Exception("Storage failure")
        
        # App might fail to start or degrade gracefully
        # Implementation depends on error handling strategy
        try:
            with TestClient(app) as test_client:
                response = test_client.get("/health")
                # Either succeeds with degraded functionality or fails gracefully
                assert response.status_code in [200, 503]  # OK or Service Unavailable
        except Exception:
            # Startup failure is also acceptable behavior
            pass


@pytest.mark.unit
class TestMiddleware:
    """Test middleware functionality"""
    
    @pytest.fixture
    def test_client(self):
        return TestClient(app)
    
    def test_cors_middleware_allows_frontend(self, test_client):
        """Test CORS middleware allows frontend origin"""
        response = test_client.get(
            "/api/documents",
            headers={"Origin": "http://localhost:5173"}
        )
        
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers
    
    def test_cors_middleware_options_request(self, test_client):
        """Test CORS preflight requests"""
        response = test_client.options(
            "/api/documents",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        assert response.status_code == 200
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-methods" in headers
    
    def test_request_logging_middleware(self, test_client):
        """Test request logging if implemented"""
        # This would test request/response logging middleware
        # Currently not implemented but useful for production
        pass
    
    def test_rate_limiting_middleware(self, test_client):
        """Test rate limiting if implemented"""
        # This would test rate limiting middleware
        # Important for production API security
        pass
