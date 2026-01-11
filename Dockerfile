# Stage 1: Build dependencies
FROM python:3.9-alpine AS builder

RUN apk add --no-cache build-base git

WORKDIR /app
COPY app.py run.sh requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt
RUN chmod +x run.sh

# Stage 2: Runtime
FROM python:3.9-alpine

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Fix CRLF if present
RUN sed -i 's/\r$//' /app/run.sh
RUN chmod +x /app/run.sh

EXPOSE 8501
ENTRYPOINT ["/app/run.sh"]
