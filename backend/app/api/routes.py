"""
API route definitions.
"""

import logging
from typing import Optional

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile)

from app.models import DocumentAnalysisResponse, ErrorResponse, HealthResponse
from app.services.content_understanding import ContentUnderstandingService
from app.services.phenoml_construe import PhenoMLConstrueService
from app.services.storage import StorageService
from app.tasks import process_document_task

router = APIRouter()


@router.get(
    "/healthz",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
async def health_check():
    """
    Check if the API is running and healthy.

    Returns:
        HealthResponse: Status of the API
    """
    return HealthResponse(status="ok")


@router.post(
    "/api/v1/analyze",
    response_model=DocumentAnalysisResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["Analysis"],
    summary="Analyze a clinical trial protocol document",
)
async def analyze_document(
    file: UploadFile = File(..., description="Protocol document to analyze"),
    storage_service: StorageService = Depends(),
    content_understanding_service: ContentUnderstandingService = Depends(),
):
    """
    Upload and analyze a clinical trial protocol document.

    This endpoint:
    1. Uploads the file to BackBlaze B2 storage
    2. Sends the file URL to Azure Content Understanding
    3. Returns the extracted data

    Args:
        file: The document file to analyze (PDF, DOCX, etc.)
        storage_service: Injected storage service instance
        content_understanding_service: Injected content understanding service

    Returns:
        DocumentAnalysisResponse: Extracted fields and analysis results

    Raises:
        HTTPException: If the analysis fails
    """
    try:
        # Read file content
        print(f"📄 Received file upload: {file.filename}")
        print(f"📄 File content type: {file.content_type}")
        logging.info(f"Received file upload: {file.filename}")
        logging.info(f"File content type: {file.content_type}")

        content = await file.read()

        print(f"📄 Read {len(content)} bytes from uploaded file")
        logging.info(f"Read {len(content)} bytes from uploaded file")

        # Upload to BackBlaze B2
        print("☁️  Uploading file to BackBlaze B2...")
        logging.info("Uploading file to BackBlaze B2")

        file_id, public_url = await storage_service.upload_file(
            content,
            file.filename or "unknown.pdf",
            file.content_type or "application/octet-stream",
        )

        print(f"☁️  File uploaded: {public_url}")
        logging.info(f"File uploaded to B2: {public_url}")

        # Process document using the public URL
        result = await content_understanding_service.analyze_document_from_url(
            document_url=public_url,
            filename=file.filename or "unknown.pdf",
        )

        return result

    except Exception as e:
        logging.error(f"Error analyzing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {str(e)}",
        )
    finally:
        await file.close()


@router.post(
    "/api/v1/analyze/async",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["Analysis"],
    summary="Analyze a document asynchronously (background task)",
)
async def analyze_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Protocol document to analyze"),
):
    """
    Upload and analyze a clinical trial protocol document asynchronously.

    This endpoint queues the document for background processing and
    returns immediately with a document ID. The client should poll
    for results using the document ID.

    Args:
        background_tasks: FastAPI background tasks
        file: The document file to analyze (PDF, DOCX, etc.)

    Returns:
        Dict with document_id and status
    """
    import uuid

    try:
        # Generate document ID
        document_id = str(uuid.uuid4())

        # Read file content
        content = await file.read()
        filename = file.filename or "unknown.pdf"
        content_type = file.content_type or "application/octet-stream"

        logging.info(f"Queuing document for background processing: {document_id}")

        # Add background task
        background_tasks.add_task(
            process_document_task, document_id, content, filename, content_type
        )

        return {
            "document_id": document_id,
            "status": "queued",
            "message": "Document queued for processing. Check status using document_id.",
        }

    except Exception as e:
        logging.error(f"Error queuing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue document: {str(e)}",
        )
    finally:
        await file.close()
