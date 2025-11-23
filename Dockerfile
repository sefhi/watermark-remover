# Watermark Remover - Dockerfile Optimizado
# Soporte para CPU, CUDA GPU y Apple Silicon (MPS)

FROM python:3.11-slim

# Información del mantenedor
LABEL maintainer="watermark-remover"
LABEL description="AI-powered watermark removal from videos"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para aprovechar caché de Docker)
COPY backend/requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código del backend
COPY backend/app/ /app/

# Copiar frontend estático
COPY frontend/public/ /app/static/

# Crear directorios necesarios
RUN mkdir -p /app/temp_uploads /app/temp_processed

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
