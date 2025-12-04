"""
API route definitions.
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Optional

from app.models import HealthResponse, DocumentAnalysisResponse, ErrorResponse
from app.services.content_understanding import ContentUnderstandingService
from app.services.phenoml_construe import PhenoMLConstrueService

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
    content_understanding_service: ContentUnderstandingService = Depends(),
):
    """
    Upload and analyze a clinical trial protocol document.
    
    This endpoint accepts a document file and extracts structured data
    using Azure Content Understanding AI.
    
    Args:
        file: The document file to analyze (PDF, DOCX, etc.)
        content_understanding_service: Injected service instance
        
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
        
        # Process document
        result = await content_understanding_service.analyze_document(
            content=content,
            filename=file.filename or "unknown.pdf",
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze document: {str(e)}",
        )
    finally:
        await file.close()

