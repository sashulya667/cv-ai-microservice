## CV AI Microservice

FastAPI service that accepts a CV PDF, extracts text, and returns a structured evaluation.
LLM clients are pluggable via a registry (Gemini by default).

uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000