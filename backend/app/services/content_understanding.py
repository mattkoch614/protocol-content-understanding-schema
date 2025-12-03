"""
Service for interacting with Azure Content Understanding AI.
"""
import logging
import uuid
import asyncio
from typing import Dict, Any
import httpx

from app.config import settings
from app.models import DocumentAnalysisResponse, ExtractedField


class ContentUnderstandingService:
    """Service for document analysis using Azure Content Understanding."""
    
    def __init__(self):
        self.endpoint = settings.AZURE_CONTENT_UNDERSTANDING_ENDPOINT
        self.api_key = settings.AZURE_CONTENT_UNDERSTANDING_KEY
        self.api_version = settings.AZURE_CONTENT_UNDERSTANDING_API_VERSION
        self.analyzer_name = settings.AZURE_CONTENT_UNDERSTANDING_ANALYZER_NAME
        
    async def analyze_document(
        self,
        content: bytes,
        filename: str,
    ) -> DocumentAnalysisResponse:
        """
        Analyze a document using Azure Content Understanding AI.
        
        Args:
            content: Document content as bytes
            filename: Name of the document file
            
        Returns:
            DocumentAnalysisResponse: Analysis results with extracted fields
            
        Raises:
            Exception: If the API call fails
        """
        document_id = str(uuid.uuid4())
        
        # Check if credentials are configured
        if not all([self.endpoint, self.api_key, self.api_version, self.analyzer_name]):
            return DocumentAnalysisResponse(
                document_id=document_id,
                fields=[],
                status="not_configured",
                error_message="Azure Content Understanding credentials not fully configured. Please check AZURE_CONTENT_UNDERSTANDING_ENDPOINT, AZURE_CONTENT_UNDERSTANDING_KEY, AZURE_CONTENT_UNDERSTANDING_API_VERSION, and AZURE_CONTENT_UNDERSTANDING_ANALYZER_NAME.",
            )
        
        try:
            # Build the analyze URL
            print(f"🔗 Endpoint: '{self.endpoint}'")
            print(f"🔗 Analyzer: '{self.analyzer_name}'")
            print(f"🔗 API Version: '{self.api_version}'")
            logging.info(f"Endpoint: '{self.endpoint}'")
            logging.info(f"Analyzer: '{self.analyzer_name}'")
            logging.info(f"API Version: '{self.api_version}'")
            
            analyze_url = f"{self.endpoint}/{self.analyzer_name}:analyze?api-version={self.api_version}"
            
            print(f"🔗 Full Analyze URL: '{analyze_url}'")
            print(f"📄 Filename: '{filename}'")
            print(f"📄 Content size: {len(content)} bytes")
            logging.info(f"Full Analyze URL: '{analyze_url}'")
            logging.info(f"Filename: '{filename}'")
            logging.info(f"Content size: {len(content)} bytes")
            
            # TODO: For now, hardcode test URL. Later, upload file to Azure Blob Storage and get URL
            # Azure Content Understanding expects JSON body with file URL, not binary content
            test_file_url = "https://saprotocolextractions.blob.core.windows.net/container/labelingProjects/337f5cd0-eae9-4cc0-a252-fd0a8ddfdf35/test/Pfizer-1_split.pdf"
            
            request_body = {
                "inputs": [
                    {
                        "url": test_file_url
                    }
                ]
            }
            
            print(f"📤 Request body: {request_body}")
            logging.info(f"Request body: {request_body}")
            
            # Start the analysis operation
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Submit document for analysis
                # Azure Content Understanding expects JSON with file URL
                print(f"🚀 Sending POST request to Azure...")
                
                response = await client.post(
                    analyze_url,
                    headers={
                        "Ocp-Apim-Subscription-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                )
                
                print(f"✅ Response status: {response.status_code}")
                print(f"✅ Response headers: {dict(response.headers)}")
                logging.info(f"Response status: {response.status_code}")
                logging.info(f"Response headers: {dict(response.headers)}")
                
                # Log response body for debugging
                if response.status_code != 202:
                    try:
                        error_body = response.text
                        print(f"❌ Error response body: {error_body}")
                        logging.error(f"Error response body: {error_body}")
                    except Exception:
                        pass
                
                response.raise_for_status()
                
                # Azure returns 202 Accepted with an Operation-Location header
                operation_location = response.headers.get("Operation-Location")
                if not operation_location:
                    raise Exception("No Operation-Location header in response")
                
                # Poll for results
                result = await self._poll_for_result(client, operation_location)
                
                # Parse and return the extracted fields
                return self._parse_analysis_result(document_id, result)
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
            return DocumentAnalysisResponse(
                document_id=document_id,
                fields=[],
                status="error",
                error_message=f"HTTP {e.response.status_code}: {error_detail}",
            )
        except Exception as e:
            return DocumentAnalysisResponse(
                document_id=document_id,
                fields=[],
                status="error",
                error_message=str(e),
            )
    
    async def _poll_for_result(
        self,
        client: httpx.AsyncClient,
        operation_location: str,
        max_retries: int = 60,
        retry_interval: int = 2,
    ) -> Dict[Any, Any]:
        """
        Poll the operation location until the analysis is complete.
        
        Args:
            client: HTTP client to use
            operation_location: URL to poll for results
            max_retries: Maximum number of polling attempts
            retry_interval: Seconds to wait between polls
            
        Returns:
            Dict containing the analysis result
            
        Raises:
            Exception: If polling fails or times out
        """
        for attempt in range(max_retries):
            response = await client.get(
                operation_location,
                headers={"Ocp-Apim-Subscription-Key": self.api_key},
            )
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status", "").lower()
            
            if status == "succeeded":
                return result
            elif status in ["failed", "cancelled"]:
                error = result.get("error", {})
                error_message = error.get("message", "Analysis failed")
                raise Exception(f"Analysis {status}: {error_message}")
            elif status in ["notstarted", "running"]:
                # Still processing, wait and retry
                await asyncio.sleep(retry_interval)
            else:
                raise Exception(f"Unknown status: {status}")
        
        raise Exception(f"Analysis timed out after {max_retries * retry_interval} seconds")
    
    def _parse_analysis_result(
        self,
        document_id: str,
        result: Dict[Any, Any],
    ) -> DocumentAnalysisResponse:
        """
        Parse the Azure Content Understanding result into our response model.
        
        Args:
            document_id: Document identifier
            result: Raw result from Azure API
            
        Returns:
            DocumentAnalysisResponse with extracted fields
        """
        extracted_fields = []
        
        # Azure Content Understanding returns fields in analyzeResult.fields
        analyze_result = result.get("analyzeResult", {})
        fields_data = analyze_result.get("fields", {})
        
        for field_name, field_data in fields_data.items():
            if field_data is None:
                continue
                
            # Extract value and confidence
            value = field_data.get("value") or field_data.get("content")
            confidence = field_data.get("confidence")
            
            if value is not None:
                extracted_fields.append(
                    ExtractedField(
                        field_name=field_name,
                        value=value,
                        confidence=confidence,
                    )
                )
        
        return DocumentAnalysisResponse(
            document_id=document_id,
            fields=extracted_fields,
            status="success",
        )

