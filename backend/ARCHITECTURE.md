# Architecture Documentation

## Overview

This FastAPI application provides an API for analyzing clinical trial protocol documents using Azure Content Understanding AI. The application follows best practices for production-ready REST APIs.

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py           # API endpoint definitions
│   ├── middleware/
│   │   └── logging.py          # Request/response logging middleware
│   ├── models.py               # Pydantic data models
│   ├── services/
│   │   ├── content_understanding.py  # Azure Content Understanding client
│   │   ├── storage.py          # BackBlaze B2 storage client
│   │   └── phenoml_construe.py # PhenoML integration (future)
│   ├── tasks/
│   │   └── document_processing.py  # Background task definitions
│   ├── config.py               # Application configuration
│   └── main.py                 # FastAPI application entry point
├── tests/
│   ├── conftest.py             # Pytest fixtures and configuration
│   ├── test_routes.py          # API endpoint tests
│   └── test_services.py        # Service layer tests
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pytest.ini                  # Pytest configuration
├── Makefile                    # Common development commands
└── .env.example                # Environment variable template
```

## Key Components

### 1. API Layer (`app/api/routes.py`)

Defines RESTful API endpoints:

- **`GET /healthz`** - Health check endpoint
- **`POST /api/v1/analyze`** - Synchronous document analysis
  - Uploads file to BackBlaze B2
  - Sends URL to Azure Content Understanding
  - Returns analysis results
- **`POST /api/v1/analyze/async`** - Asynchronous document analysis
  - Queues document for background processing
  - Returns document ID for status polling
  - Uses FastAPI BackgroundTasks

### 2. Middleware (`app/middleware/`)

- **LoggingMiddleware**: Logs all HTTP requests/responses with timing information
- Adds `X-Request-ID` and `X-Process-Time` headers to responses

### 3. Services (`app/services/`)

#### ContentUnderstandingService
- Interfaces with Azure Content Understanding API
- Handles document URL submission
- Polls for analysis completion
- Returns raw Azure response

#### StorageService
- Manages file uploads to BackBlaze B2
- Authenticates with B2 API
- Generates unique filenames
- Returns public URLs for uploaded files
- Supports file deletion

### 4. Background Tasks (`app/tasks/`)

- **process_document_task**: Async document processing workflow
  1. Upload to BackBlaze B2
  2. Submit to Azure Content Understanding
  3. Poll for results
  4. Store/return analysis data

### 5. Models (`app/models.py`)

Pydantic models for request/response validation:
- `HealthResponse`
- `DocumentAnalysisRequest`
- `DocumentAnalysisResponse`
- `ExtractedField`
- `ErrorResponse`

### 6. Configuration (`app/config.py`)

Environment-based configuration using Pydantic Settings:
- API settings (prefix, project name, CORS)
- Azure Content Understanding credentials
- BackBlaze B2 credentials
- PhenoML Construe settings

## Data Flow

### Synchronous Processing

```
1. Client uploads file → POST /api/v1/analyze
2. API reads file content
3. Upload file to BackBlaze B2 → Get public URL
4. Send URL to Azure Content Understanding → Get operation location
5. Poll operation location until analysis completes
6. Return raw Azure response to client
```

### Asynchronous Processing

```
1. Client uploads file → POST /api/v1/analyze/async
2. API reads file content
3. Queue background task with file content
4. Return document_id immediately
5. Background task:
   a. Upload to BackBlaze B2
   b. Submit to Azure Content Understanding
   c. Poll for completion
   d. Store results (future: database/cache)
```

## External Services

### Azure Content Understanding
- **Purpose**: Extract structured data from protocol documents
- **API Type**: REST API with async long-running operations
- **Authentication**: API key via `Ocp-Apim-Subscription-Key` header
- **Request Format**: JSON with `inputs` array containing document URLs
- **Response Format**: JSON with `analyzeResult.fields` containing extracted data

### BackBlaze B2
- **Purpose**: Store uploaded documents and generate public URLs
- **API Type**: REST API
- **Authentication**: Application Key ID + Application Key
- **Features**:
  - Bucket-based storage
  - Public URL generation
  - SHA1 integrity checking
  - File metadata support

## Testing Strategy

### Unit Tests
- Service layer logic (mocked external APIs)
- Model validation
- Configuration parsing

### Integration Tests
- API endpoint behavior
- Error handling
- File upload processing

### Test Fixtures
- `client`: TestClient for API testing
- `mock_content_understanding_service`: Mocked Azure service
- `sample_pdf_content`: Test file data
- `mock_azure_response`: Sample Azure API response

## Development Workflow

### Setup
```bash
make install-dev      # Install all dependencies
```

### Running Tests
```bash
make test             # Run all tests
make test-cov         # Run tests with coverage report
```

### Code Quality
```bash
make lint             # Run linters (flake8, mypy)
make format           # Format code (black, isort)
```

### Running Locally
```bash
make run              # Start development server with auto-reload
```

## Environment Variables

See `.env.example` for required configuration. Key variables:

- `AZURE_CONTENT_UNDERSTANDING_*`: Azure API credentials
- `B2_*`: BackBlaze B2 storage credentials
- `ALLOWED_ORIGINS`: CORS configuration

## Logging

Structured logging with multiple levels:
- **INFO**: Request/response logging, major operations
- **ERROR**: Failures, exceptions with stack traces
- **DEBUG**: Detailed debugging information (development only)

Log format:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Error Handling

- HTTP exceptions with appropriate status codes
- Detailed error messages in development
- Structured error responses via `ErrorResponse` model
- Exception logging with stack traces

## Future Enhancements

1. **Database Integration**: Store analysis results and document metadata
2. **Caching**: Redis for operation status and results
3. **Webhooks**: Notify clients when async processing completes
4. **Authentication**: API key or OAuth2 authentication
5. **Rate Limiting**: Prevent API abuse
6. **Observability**: Metrics, distributed tracing (Sentry, OpenTelemetry)
7. **PhenoML Integration**: Connect extracted data to PhenoML Construe

