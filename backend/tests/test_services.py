"""
Tests for service layer.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.models import DocumentAnalysisResponse
from app.services.content_understanding import ContentUnderstandingService


@pytest.fixture
def service():
    """Create ContentUnderstandingService instance with test config."""
    with patch("app.services.content_understanding.settings") as mock_settings:
        mock_settings.AZURE_CONTENT_UNDERSTANDING_ENDPOINT = (
            "https://test.azure.com/analyzers"
        )
        mock_settings.AZURE_CONTENT_UNDERSTANDING_KEY = "test-key"
        mock_settings.AZURE_CONTENT_UNDERSTANDING_API_VERSION = "2025-11-01"
        mock_settings.AZURE_CONTENT_UNDERSTANDING_ANALYZER_NAME = "test-analyzer"
        return ContentUnderstandingService()


@pytest.mark.asyncio
async def test_analyze_document_not_configured():
    """Test analyze_document with missing configuration."""
    with patch("app.services.content_understanding.settings") as mock_settings:
        mock_settings.AZURE_CONTENT_UNDERSTANDING_ENDPOINT = ""
        mock_settings.AZURE_CONTENT_UNDERSTANDING_KEY = ""
        mock_settings.AZURE_CONTENT_UNDERSTANDING_API_VERSION = ""
        mock_settings.AZURE_CONTENT_UNDERSTANDING_ANALYZER_NAME = ""

        service = ContentUnderstandingService()
        result = await service.analyze_document(b"test content", "test.pdf")

        assert result.status == "not_configured"
        assert "not fully configured" in result.error_message


@pytest.mark.asyncio
async def test_analyze_document_success(
    service, mock_azure_response, mock_operation_location
):
    """Test successful document analysis."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock client
        mock_client = mock_client_class.return_value.__aenter__.return_value

        # Mock POST response (initial submission)
        mock_post_response = Mock()
        mock_post_response.status_code = 202
        mock_post_response.headers = {"Operation-Location": mock_operation_location}
        mock_client.post = AsyncMock(return_value=mock_post_response)

        # Mock GET response (polling)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = mock_azure_response
        mock_client.get = AsyncMock(return_value=mock_get_response)

        # Execute
        result = await service.analyze_document(b"test content", "test.pdf")

        # Assertions
        assert result.status == "success"
        assert result.raw_result == mock_azure_response
        assert mock_client.post.called
        assert mock_client.get.called


@pytest.mark.asyncio
async def test_analyze_document_http_error(service):
    """Test document analysis with HTTP error."""
    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock client to raise HTTP error
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        http_error = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )
        mock_client.post = AsyncMock(side_effect=http_error)

        # Execute
        result = await service.analyze_document(b"test content", "test.pdf")

        # Assertions
        assert result.status == "error"
        assert "HTTP 400" in result.error_message


@pytest.mark.asyncio
async def test_poll_for_result_timeout(service, mock_operation_location):
    """Test polling timeout."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value

        # Mock response that stays "running"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "running"}
        mock_client.get = AsyncMock(return_value=mock_response)

        # Execute with very low retry count
        with pytest.raises(Exception, match="timed out"):
            await service._poll_for_result(
                mock_client, mock_operation_location, max_retries=2, retry_interval=0
            )
