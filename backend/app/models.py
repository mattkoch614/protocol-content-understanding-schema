"""
Pydantic models for request/response schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Health status of the API")


class ExtractedField(BaseModel):
    """Represents an extracted field from a document."""
    
    field_name: str = Field(..., description="Name of the extracted field")
    value: Any = Field(..., description="Extracted value")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")


class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis."""
    
    document_url: Optional[str] = Field(None, description="URL of the document to analyze")
    document_name: Optional[str] = Field(None, description="Name of the uploaded document")


class DocumentAnalysisResponse(BaseModel):
    """Response model for document analysis."""
    
    document_id: str = Field(..., description="Unique identifier for the analyzed document")
    fields: List[ExtractedField] = Field(default_factory=list, description="Extracted fields")
    status: str = Field(..., description="Analysis status")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    raw_result: Optional[Dict[str, Any]] = Field(None, description="Raw response from Azure Content Understanding")


class ProtocolMetadata(BaseModel):
    """Clinical trial protocol metadata extracted from documents."""
    
    protocol_number: Optional[str] = Field(None, description="Protocol identifier")
    protocol_title: Optional[str] = Field(None, description="Protocol title")
    sponsor_name: Optional[str] = Field(None, description="Sponsor organization name")
    protocol_version: Optional[str] = Field(None, description="Version number")
    protocol_date: Optional[date] = Field(None, description="Protocol date")
    amendment_number: Optional[str] = Field(None, description="Amendment number if applicable")
    indication: Optional[str] = Field(None, description="Medical indication/condition")
    phase: Optional[str] = Field(None, description="Clinical trial phase")
    study_design: Optional[str] = Field(None, description="Study design description")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

