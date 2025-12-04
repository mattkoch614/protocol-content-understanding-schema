"""
Pytest configuration and fixtures for testing.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.content_understanding import ContentUnderstandingService


@pytest.fixture
def client():
    """Test client for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_content_understanding_service():
    """Mock ContentUnderstandingService for testing."""
    service = Mock(spec=ContentUnderstandingService)
    service.analyze_document = AsyncMock()
    return service


@pytest.fixture
def sample_pdf_content():
    """Sample PDF file content for testing."""
    # Simple PDF header bytes
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nSample PDF content for testing"


@pytest.fixture
def mock_azure_response():
    """Mock Azure Content Understanding API response."""
    return {
        "status": "succeeded",
        "analyzeResult": {
            "fields": {
                "ProtocolNumber": {"value": "ABC-1234-001", "confidence": 0.95},
                "ProtocolTitle": {"value": "Test Protocol Title", "confidence": 0.92},
                "SponsorName": {"value": "Test Sponsor Inc.", "confidence": 0.89},
            }
        },
    }


@pytest.fixture
def mock_operation_location():
    """Mock operation location URL from Azure."""
    return "https://test-endpoint.azure.com/operation/12345"
