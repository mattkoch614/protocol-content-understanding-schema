"""
Background tasks for document processing.
"""

import logging
from typing import Any, Dict

from app.services.content_understanding import ContentUnderstandingService
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


async def process_document_task(
    document_id: str, file_content: bytes, filename: str, content_type: str
) -> Dict[str, Any]:
    """
    Background task to process uploaded document.

    This task:
    1. Uploads file to BackBlaze B2
    2. Sends document URL to Azure Content Understanding
    3. Polls for results
    4. Returns extracted data

    Args:
        document_id: Unique identifier for this document
        file_content: Binary content of the uploaded file
        filename: Original filename
        content_type: MIME type of the file

    Returns:
        Dict containing processing results
    """
    logger.info(f"Starting background processing for document: {document_id}")

    try:
        # Step 1: Upload to BackBlaze B2
        logger.info(f"Uploading {filename} to BackBlaze B2...")
        storage_service = StorageService()
        file_id, public_url = await storage_service.upload_file(
            file_content, filename, content_type
        )
        logger.info(f"File uploaded successfully: {public_url}")

        # Step 2: Send to Azure Content Understanding
        logger.info(f"Sending document to Azure Content Understanding...")
        cu_service = ContentUnderstandingService()
        result = await cu_service.analyze_document_from_url(
            document_url=public_url, filename=filename
        )
        logger.info(f"Analysis complete for document: {document_id}")

        return {
            "document_id": document_id,
            "file_id": file_id,
            "file_url": public_url,
            "analysis_result": result,
            "status": "completed",
        }

    except Exception as e:
        logger.error(
            f"Error processing document {document_id}: {str(e)}", exc_info=True
        )
        return {"document_id": document_id, "status": "failed", "error": str(e)}
