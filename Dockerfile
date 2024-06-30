FROM rvolosatovs/protoc:4.0.0 AS proto
WORKDIR /build
COPY src/app/proto src/app/proto
RUN protoc --proto_path=app/proto=src/app/proto \
        --python_out=src \
        --grpc-python_out=src \
        src/app/proto/*.proto

FROM --platform=$BUILDPLATFORM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY . ./
COPY --from=proto /build/src/app/proto src/app/proto
RUN adduser -u 5678 --disabled-password --gecos "" appuser \
                && chown -R appuser /app
USER appuser
# Plugin arch gRPC server port
EXPOSE 6565
# Prometheus /metrics web server port
EXPOSE 8080
ENTRYPOINT PYTHONPATH=/app/src python -m app \
                --enable_health_checking --enable_reflection
