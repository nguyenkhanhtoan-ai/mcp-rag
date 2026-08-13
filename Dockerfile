FROM python:3.12-slim

WORKDIR /app

# Cài dependencies trước để tận dụng Docker layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# chroma_db sẽ được mount như volume khi deploy (xem DEPLOY.md)
RUN mkdir -p /app/chroma_db /app/documents

# Ingest PDF ngay lúc build image
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
RUN python ingest.py

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]