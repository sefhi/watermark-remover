"""
Watermark Remover API - Backend Principal
FastAPI application para remover marcas de agua de videos usando IA
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from video_processor import VideoProcessor

# Configuración de directorios
# Detectar si estamos en Docker o local
if Path("/app/static").exists():
    # Estamos en Docker
    BASE_DIR = Path("/app")
else:
    # Desarrollo local
    BASE_DIR = Path(__file__).parent.parent

UPLOAD_DIR = BASE_DIR / "temp_uploads"
PROCESSED_DIR = BASE_DIR / "temp_processed"
STATIC_DIR = BASE_DIR / "static"

# Asegurar que los directorios existen
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Inicializar FastAPI
app = FastAPI(
    title="Watermark Remover API",
    description="API para remover marcas de agua de videos usando IA",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos si existen
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Almacenar sesiones de procesamiento
sessions = {}


@app.get("/")
async def root():
    """Servir la aplicación web"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(), status_code=200)
    return {
        "status": "online",
        "service": "Watermark Remover API",
        "version": "1.0.0"
    }


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Endpoint para subir un video o GIF.

    Args:
        file: Archivo de video (.mp4, .mov, .avi, .gif)

    Returns:
        session_id: ID único de la sesión
        preview_url: URL para obtener el preview del primer frame
        filename: Nombre del archivo original
        duration: Duración del video en segundos
        fps: Frames por segundo
        resolution: Resolución del video (ancho x alto)
    """
    # Validar extensión del archivo
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Formatos permitidos: {', '.join(allowed_extensions)}"
        )

    # Generar ID único para esta sesión
    session_id = str(uuid.uuid4())

    # Guardar el archivo subido
    video_path = UPLOAD_DIR / f"{session_id}{file_extension}"

    try:
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {str(e)}")

    # Inicializar el procesador de video
    try:
        processor = VideoProcessor(str(video_path))

        # Extraer primer frame
        preview_path = UPLOAD_DIR / f"{session_id}_preview.jpg"
        first_frame = processor.extract_first_frame(str(preview_path))

        # Obtener información del video
        video_info = processor.get_video_info()

        # Guardar la sesión
        sessions[session_id] = {
            "video_path": str(video_path),
            "preview_path": str(preview_path),
            "processor": processor,
            "filename": file.filename,
            "video_info": video_info
        }

        return {
            "session_id": session_id,
            "preview_url": f"/api/preview/{session_id}",
            "filename": file.filename,
            "duration": video_info["duration"],
            "fps": video_info["fps"],
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "total_frames": video_info["total_frames"]
        }

    except Exception as e:
        # Limpiar archivos si hay error
        if video_path.exists():
            video_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error al procesar el video: {str(e)}")


@app.get("/api/preview/{session_id}")
async def get_preview(session_id: str):
    """
    Obtener el preview (primer frame) del video subido

    Args:
        session_id: ID de la sesión

    Returns:
        Imagen JPG del primer frame
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    preview_path = sessions[session_id]["preview_path"]

    if not Path(preview_path).exists():
        raise HTTPException(status_code=404, detail="Preview no encontrado")

    return FileResponse(preview_path, media_type="image/jpeg")


@app.post("/api/process/{session_id}")
async def process_video(
    session_id: str,
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...)
):
    """
    Procesar el video removiendo la marca de agua del área seleccionada.

    Args:
        session_id: ID de la sesión
        x: Coordenada X del área seleccionada
        y: Coordenada Y del área seleccionada
        width: Ancho del área seleccionada
        height: Alto del área seleccionada

    Returns:
        status: Estado del procesamiento
        progress_url: URL para consultar el progreso
        download_url: URL para descargar el video procesado
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    session = sessions[session_id]
    processor = session["processor"]

    # Validar coordenadas
    video_info = session["video_info"]
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Coordenadas inválidas")

    if x + width > video_info["width"] or y + height > video_info["height"]:
        raise HTTPException(status_code=400, detail="Área seleccionada fuera de los límites del video")

    # Configurar área de marca de agua
    watermark_area = {
        "x": x,
        "y": y,
        "width": width,
        "height": height
    }

    # Generar ruta de salida con extensión correcta
    original_path = session["video_path"]
    output_ext = ".gif" if original_path.lower().endswith(".gif") else ".mp4"
    output_filename = f"{session_id}_processed{output_ext}"
    output_path = PROCESSED_DIR / output_filename

    try:
        # Procesar el video (esto puede tomar tiempo)
        processor.process_video(
            watermark_area=watermark_area,
            output_path=str(output_path)
        )

        # Actualizar sesión
        sessions[session_id]["processed_path"] = str(output_path)
        sessions[session_id]["watermark_area"] = watermark_area

        return {
            "status": "completed",
            "message": "Video procesado exitosamente",
            "download_url": f"/api/download/{session_id}",
            "session_id": session_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el video: {str(e)}")


@app.get("/api/download/{session_id}")
async def download_video(session_id: str):
    """
    Descargar el video procesado.

    Args:
        session_id: ID de la sesión

    Returns:
        Archivo de video procesado
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if "processed_path" not in sessions[session_id]:
        raise HTTPException(status_code=404, detail="Video aún no procesado")

    processed_path = sessions[session_id]["processed_path"]

    if not Path(processed_path).exists():
        raise HTTPException(status_code=404, detail="Video procesado no encontrado")

    original_filename = sessions[session_id]["filename"]
    download_filename = f"processed_{original_filename}"

    # Determinar media type según extensión
    media_type = "image/gif" if processed_path.lower().endswith(".gif") else "video/mp4"

    return FileResponse(
        processed_path,
        media_type=media_type,
        filename=download_filename
    )


@app.delete("/api/session/{session_id}")
async def cleanup_session(session_id: str):
    """
    Limpiar archivos de una sesión.

    Args:
        session_id: ID de la sesión

    Returns:
        Confirmación de limpieza
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    session = sessions[session_id]

    # Eliminar archivos
    files_to_delete = [
        session.get("video_path"),
        session.get("preview_path"),
        session.get("processed_path")
    ]

    for file_path in files_to_delete:
        if file_path and Path(file_path).exists():
            try:
                Path(file_path).unlink()
            except Exception as e:
                print(f"Error eliminando {file_path}: {e}")

    # Limpiar procesador
    if "processor" in session:
        session["processor"].cleanup()

    # Eliminar sesión
    del sessions[session_id]

    return {"status": "success", "message": "Sesión limpiada exitosamente"}


@app.get("/api/sessions")
async def list_sessions():
    """Listar todas las sesiones activas (útil para debugging)"""
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "session_id": sid,
                "filename": session["filename"],
                "has_processed": "processed_path" in session
            }
            for sid, session in sessions.items()
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
