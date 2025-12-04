"""
Tests for API routes.
"""

from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest

from app.models import DocumentAnalysisResponse


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Content Understanding API"
    assert data["version"] == "0.1.0"
    assert "docs" in data


@pytest.mark.asyncio
async def test_analyze_document_success(
    client, sample_pdf_content, mock_azure_response
):
    """Test successful document analysis."""
    with patch("app.api.routes.ContentUnderstandingService") as mock_service_class:
        # Setup mock
        mock_service = mock_service_class.return_value
        mock_service.analyze_document = AsyncMock(
            return_value=DocumentAnalysisResponse(
                document_id="test-doc-123",
                fields=[],
                status="success",
                raw_result=mock_azure_response,
            )
        )

        # Create file upload
        files = {"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")}

        # Make request
        response = client.post("/api/v1/analyze", files=files)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["document_id"] == "test-doc-123"
        assert "raw_result" in data


def test_analyze_document_no_file(client):
    """Test document analysis without file."""
    response = client.post("/api/v1/analyze")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_document_processing_error(client, sample_pdf_content):
    """Test document analysis with processing error."""
    with patch("app.api.routes.ContentUnderstandingService") as mock_service_class:
        # Setup mock to raise exception
        mock_service = mock_service_class.return_value
        mock_service.analyze_document = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        # Create file upload
        files = {"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")}

        # Make request
        response = client.post("/api/v1/analyze", files=files)

        # Assertions
        assert response.status_code == 500
        assert "Failed to analyze document" in response.json()["detail"]
