.PHONY: run test test-cov stop install install-dev lint format clean

# Detect OS and set Python/pytest paths
ifeq ($(OS),Windows_NT)
    PYTHON := .venv\Scripts\python.exe
    PYTEST := .venv\Scripts\pytest.exe
    UVICORN := .venv\Scripts\uvicorn.exe
    KILL := taskkill //F //IM
else
    PYTHON := .venv/bin/python
    PYTEST := .venv/bin/pytest
    UVICORN := .venv/bin/uvicorn
    KILL := pkill -f
endif

# Start the FastAPI application locally
run:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
# Usage: make test ARGS="-k test_health_check"
test:
	$(PYTEST) tests/ -v $(ARGS)

# Run tests with coverage
test-cov:
	$(PYTEST) tests/ -v --cov=app --cov-report=html --cov-report=term $(ARGS)

# Stop the running FastAPI application
stop:
	$(KILL) "uvicorn app.main:app" || true

# Install production dependencies
install:
	uv pip install --requirements requirements.txt

# Install development dependencies
install-dev:
	uv pip install --requirements requirements.txt
	uv pip install --requirements requirements-dev.txt

# Lint code
lint:
	$(PYTHON) -m flake8 app tests
	$(PYTHON) -m mypy app

# Format code
format:
	$(PYTHON) -m black app tests
	$(PYTHON) -m isort app tests

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov 2>/dev/null || true

