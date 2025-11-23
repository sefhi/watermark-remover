# 🎬 Watermark Remover - AI Video Processing

Aplicación web dockerizada para remover marcas de agua de videos usando Inteligencia Artificial. Utiliza el modelo [prithiVLMods/Kontext-Watermark-Remover](https://huggingface.co/prithiVLMods/Kontext-Watermark-Remover) de HuggingFace para eliminar automáticamente marcas de agua de videos.

## ✨ Características

- 🎥 **Soporte múltiples formatos**: MP4, MOV, AVI, MKV, WebM
- 🖱️ **Interfaz intuitiva**: Selección visual del área de marca de agua mediante canvas interactivo
- 🤖 **IA de última generación**: Utiliza modelo pre-entrenado de HuggingFace
- 🚀 **Alto rendimiento**: Soporte para GPU (CUDA), Apple Silicon (MPS) y CPU
- 🐳 **Completamente dockerizado**: Fácil despliegue y portabilidad
- 📊 **Progreso en tiempo real**: Indicadores de progreso durante el procesamiento
- 💾 **Descarga automática**: Video procesado listo para descargar

## 🏗️ Arquitectura

```
watermark-remover/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI backend
│   │   └── video_processor.py   # Procesamiento de video con IA
│   ├── temp_uploads/            # Videos subidos
│   ├── temp_processed/          # Videos procesados
│   └── requirements.txt         # Dependencias Python
├── frontend/
│   └── public/
│       ├── index.html           # HTML principal
│       ├── app.js               # React application
│       └── styles.css           # Estilos CSS
├── Dockerfile                   # Configuración Docker
├── docker-compose.yml           # Orquestación Docker
└── README.md                    # Este archivo
```

## 📋 Requisitos

### Mínimos
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: 4 GB mínimo, 8 GB recomendado
- **Espacio**: 10 GB para modelo + dependencias

### Recomendados (para mejor rendimiento)
- **GPU NVIDIA** con CUDA 11.8+ (opcional pero muy recomendado)
- **Apple Silicon** (M1/M2/M3) con soporte MPS
- **RAM**: 16 GB+
- **CPU**: 4+ cores

## 🚀 Inicio Rápido

### Opción 1: Usando Docker Compose (Recomendado)

```bash
# 1. Clonar o descargar el repositorio
cd watermark-remover

# 2. Construir y ejecutar con Docker Compose
docker compose up --build

# 3. Abrir navegador en http://localhost:8000
```

### Opción 2: Usando Docker directamente

```bash
# 1. Construir la imagen
docker build -t watermark-remover .

# 2. Ejecutar el contenedor
docker run -p 8000:8000 watermark-remover

# 3. Abrir navegador en http://localhost:8000
```

### Opción 3: Desarrollo local (sin Docker)

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
cd backend
pip install -r requirements.txt

# 3. Instalar ffmpeg (si no está instalado)
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt-get install ffmpeg

# 4. Ejecutar servidor
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Abrir navegador en http://localhost:8000
```

## 📖 Guía de Uso

### Paso 1: Subir Video
1. Arrastra tu video a la zona de drop o haz clic para seleccionarlo
2. Formatos soportados: MP4, MOV, AVI, MKV, WebM
3. Haz clic en "Subir Video"

### Paso 2: Seleccionar Área
1. Se mostrará el primer frame del video en un canvas interactivo
2. Haz clic y arrastra para dibujar un rectángulo sobre la marca de agua
3. Puedes redefinir el área haciendo otra selección
4. Haz clic en "Procesar Video"

### Paso 3: Procesamiento
1. El sistema procesará todos los frames del video
2. Se mostrará una barra de progreso
3. El tiempo depende de:
   - Duración del video
   - Resolución
   - Hardware disponible (GPU vs CPU)

### Paso 4: Descargar
1. Una vez completado, aparecerá el botón de descarga
2. El video procesado estará en formato MP4
3. Se mantendrá el audio original

## ⚙️ Configuración Avanzada

### Usar GPU NVIDIA (CUDA)

Modificar `docker-compose.yml`:

```yaml
services:
  watermark-remover:
    # ... otras configuraciones
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
```

Luego ejecutar:
```bash
docker compose up --build
```

### Ajustar Límites de Memoria

En `docker-compose.yml`:

```yaml
services:
  watermark-remover:
    # ... otras configuraciones
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### Variables de Entorno

Crear archivo `.env`:

```bash
# Puerto de la aplicación
PORT=8000

# Límite de tamaño de archivo (en MB)
MAX_FILE_SIZE=500

# Dispositivo (cpu, cuda, mps)
DEVICE=cpu
```

## 🔧 Desarrollo

### Estructura del Backend (FastAPI)

```python
# Endpoints principales
POST /api/upload          # Subir video
GET  /api/preview/{id}    # Obtener primer frame
POST /api/process/{id}    # Procesar video
GET  /api/download/{id}   # Descargar video procesado
DELETE /api/session/{id}  # Limpiar sesión
```

### Frontend (React + Vanilla)

El frontend está construido con React sin build tools, usando CDN para máxima simplicidad:
- **React 18**: UI components
- **Canvas API**: Selección de área interactiva
- **Fetch API**: Comunicación con backend

### Modificar el Modelo

Editar `backend/app/video_processor.py`:

```python
# Cambiar modelo de HuggingFace
model_name = "tu-modelo/aqui"
self.model = AutoModelForImageSegmentation.from_pretrained(
    model_name,
    trust_remote_code=True
)
```

## 📊 Rendimiento

### Tiempos de Procesamiento (Estimados)

| Hardware | Video 1080p (10s) | Video 1080p (60s) |
|----------|-------------------|-------------------|
| CPU (4 cores) | ~5-10 min | ~30-60 min |
| GPU (RTX 3060) | ~1-2 min | ~6-12 min |
| Apple M1 (MPS) | ~2-4 min | ~12-24 min |

*Los tiempos varían según la complejidad de la marca de agua y la calidad del video.*

### Optimizaciones

1. **Usar GPU**: Acelera el procesamiento 5-10x
2. **Reducir resolución**: Si es aceptable, procesar en 720p y luego upscale
3. **Batch processing**: Procesar múltiples videos en paralelo (modificación requerida)

## 🐛 Solución de Problemas

### Error: "No se pudo cargar el modelo"

```bash
# Verificar conexión a internet (descarga modelo de HuggingFace)
# O pre-descargar el modelo:
from transformers import AutoModelForImageSegmentation
model = AutoModelForImageSegmentation.from_pretrained(
    "prithiVLMods/Kontext-Watermark-Remover",
    trust_remote_code=True
)
```

### Error: "CUDA out of memory"

```bash
# Reducir batch size o usar CPU
# En video_processor.py cambiar device:
self.device = "cpu"
```

### Video procesado sin audio

```bash
# Verificar que ffmpeg esté instalado correctamente
ffmpeg -version

# Reinstalar ffmpeg en el contenedor si es necesario
```

### Contenedor se queda sin memoria

```bash
# Aumentar límite de memoria en docker-compose.yml
# O procesar videos más cortos
```

## 🔐 Consideraciones de Seguridad

- ⚠️ **No exponer a internet sin autenticación**: Esta aplicación no tiene autenticación por defecto
- 🔒 **Usar HTTPS**: En producción, configurar reverse proxy con SSL
- 🗑️ **Limpiar archivos temporales**: Los archivos se guardan en `temp_uploads` y `temp_processed`
- 📝 **Validar inputs**: Se validan extensiones de archivo y tamaños

## 📄 Licencia

Este proyecto está bajo licencia MIT. El modelo de IA utilizado puede tener su propia licencia - consultar [HuggingFace](https://huggingface.co/prithiVLMods/Kontext-Watermark-Remover).

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📮 Soporte

Para problemas o preguntas:
- Abrir un issue en GitHub
- Revisar la documentación del modelo en HuggingFace

## 🙏 Agradecimientos

- [prithiVLMods](https://huggingface.co/prithiVLMods) por el modelo Kontext-Watermark-Remover
- [HuggingFace](https://huggingface.co) por la plataforma de modelos
- [FastAPI](https://fastapi.tiangolo.com) por el excelente framework
- [OpenCV](https://opencv.org) por las herramientas de procesamiento de video

---

**⚠️ Aviso Legal**: Esta herramienta está destinada únicamente para uso en contenido del cual posees los derechos. No la uses para infringir derechos de autor o marcas registradas.