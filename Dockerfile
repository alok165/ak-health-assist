# ── AK Health Assist — Streamlit container ───────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install dependencies (separate layer for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files only
COPY basic-chat-gemini.py .
COPY streamlit_app.py .

# Audit logs directory
RUN mkdir -p logs

# Streamlit default port
EXPOSE 8501

# Run in headless mode (required inside a container)
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
