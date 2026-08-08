FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOOGLE_GENAI_USE_VERTEXAI=TRUE

WORKDIR /app

COPY proofline/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

COPY proofline /app/agents/proofline
COPY server.py /app/server.py

EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port \"$PORT\""]
