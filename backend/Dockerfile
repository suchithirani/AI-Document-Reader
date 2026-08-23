FROM python:3.11-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency metadata and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application source
COPY . .
COPY DigiCertRootCA.crt /usr/local/share/ca-certificates/DigiCertRootCA.crt

# Reinstall CA certificates after copying source (prevents overwriting)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && update-ca-certificates && rm -rf /var/lib/apt/lists/*

# Relax OpenSSL security level so Docker container can reach MongoDB Atlas
# (Debian Bookworm's default SECLEVEL=2 breaks TLS handshake from within Docker NAT)
RUN sed -i 's/^\(MinProtocol\s*=\s*\).*/\1TLSv1/' /etc/ssl/openssl.cnf 2>/dev/null || true \
 && sed -i 's/^\(CipherString\s*=\s*\).*/\1DEFAULT@SECLEVEL=1/' /etc/ssl/openssl.cnf 2>/dev/null || true

# Expose port
EXPOSE 8000

# Default command (overridden in compose for worker/beat)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
