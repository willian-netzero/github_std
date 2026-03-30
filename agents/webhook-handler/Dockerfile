FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared/ ./shared/
COPY ../architecture-guard/ ./architecture_guard/
COPY ../code-reviewer/ ./code_reviewer/
COPY ../test-runner/ ./test_runner/
COPY ../security-scanner/ ./security_scanner/
COPY ../pr-summarizer/ ./pr_summarizer/
COPY ../tlpp-checker/ ./tlpp_checker/
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
