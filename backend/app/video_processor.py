"""
Video Processor - Procesamiento de video y remoción de marcas de agua
Usa el modelo prithiVLMods/Kontext-Watermark-Remover de HuggingFace
"""

import cv2
import numpy as np
import torch
from pathlib import Path
from PIL import Image
from typing import Dict, Optional
import tempfile
import subprocess
import os

try:
    from transformers import AutoModelForImageSegmentation
    from torchvision import transforms
except ImportError:
    print("Warning: transformers not installed. Install with: pip install transformers")


class VideoProcessor:
    """Clase para procesar videos y remover marcas de agua usando IA"""

    def __init__(self, video_path: str):
        """
        Inicializar el procesador de video.

        Args:
            video_path: Ruta al archivo de video
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")

        # Obtener propiedades del video
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0

        # Inicializar modelo (lazy loading)
        self.model = None
        self.device = self._get_device()
        self.transform = None

    def _get_device(self) -> str:
        """
        Detectar el mejor dispositivo disponible (CUDA, MPS, o CPU).

        Returns:
            Nombre del dispositivo
        """
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            # Apple Silicon (M1/M2)
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """Cargar el modelo de remoción de marcas de agua (lazy loading)"""
        if self.model is not None:
            return

        print(f"Cargando modelo en {self.device}...")

        try:
            # Cargar el modelo de HuggingFace
            model_name = "prithiVLMods/Kontext-Watermark-Remover"
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            self.model.to(self.device)
            self.model.eval()

            # Transformaciones para el modelo
            self.transform = transforms.Compose([
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

            print("Modelo cargado exitosamente")

        except Exception as e:
            print(f"Error cargando modelo: {e}")
            print("Usando fallback con procesamiento de inpainting básico")
            self.model = "fallback"  # Usar método alternativo

    def get_video_info(self) -> Dict:
        """
        Obtener información del video.

        Returns:
            Diccionario con información del video
        """
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration": self.duration
        }

    def extract_first_frame(self, output_path: str) -> np.ndarray:
        """
        Extraer el primer frame del video y guardarlo.

        Args:
            output_path: Ruta donde guardar la imagen

        Returns:
            Frame como array de numpy
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()

        if not ret:
            raise ValueError("No se pudo leer el primer frame del video")

        # Guardar como JPEG
        cv2.imwrite(output_path, frame)

        return frame

    def _create_mask_from_area(self, watermark_area: Dict) -> np.ndarray:
        """
        Crear una máscara binaria a partir del área seleccionada.

        Args:
            watermark_area: Diccionario con {x, y, width, height}

        Returns:
            Máscara binaria (0 y 255)
        """
        mask = np.zeros((self.height, self.width), dtype=np.uint8)

        x = watermark_area["x"]
        y = watermark_area["y"]
        w = watermark_area["width"]
        h = watermark_area["height"]

        # Crear máscara rectangular
        mask[y:y+h, x:x+w] = 255

        return mask

    def _remove_watermark_with_model(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Remover marca de agua usando el modelo de IA.

        Args:
            frame: Frame del video (BGR)
            mask: Máscara del área de marca de agua

        Returns:
            Frame procesado sin marca de agua
        """
        if self.model == "fallback":
            return self._remove_watermark_inpainting(frame, mask)

        try:
            # Convertir BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # Preparar imagen para el modelo
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

            # Inferencia
            with torch.no_grad():
                output = self.model(input_tensor)

            # Post-procesamiento
            output_img = output.squeeze().cpu().numpy()

            # Normalizar y convertir a uint8
            output_img = (output_img * 255).astype(np.uint8)

            # Si la salida es 1 canal, convertir a 3 canales
            if len(output_img.shape) == 2:
                output_img = cv2.cvtColor(output_img, cv2.COLOR_GRAY2BGR)

            # Aplicar solo en el área de la máscara
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            result = (frame * (1 - mask_3ch) + output_img * mask_3ch).astype(np.uint8)

            return result

        except Exception as e:
            print(f"Error en procesamiento con modelo: {e}")
            return self._remove_watermark_inpainting(frame, mask)

    def _remove_watermark_inpainting(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Método alternativo usando inpainting de OpenCV (fallback).

        Args:
            frame: Frame del video
            mask: Máscara del área de marca de agua

        Returns:
            Frame procesado
        """
        # Usar inpainting de OpenCV como alternativa
        result = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        return result

    def process_video(self, watermark_area: Dict, output_path: str, progress_callback=None):
        """
        Procesar el video completo removiendo la marca de agua.

        Args:
            watermark_area: Diccionario con {x, y, width, height}
            output_path: Ruta donde guardar el video procesado
            progress_callback: Función opcional para reportar progreso
        """
        # Cargar modelo si no está cargado
        self._load_model()

        # Crear máscara
        mask = self._create_mask_from_area(watermark_area)

        # Crear directorio temporal para frames procesados
        temp_dir = tempfile.mkdtemp()
        temp_frames_dir = Path(temp_dir) / "frames"
        temp_frames_dir.mkdir(exist_ok=True)

        try:
            print(f"Procesando {self.total_frames} frames...")

            # Resetear posición del video
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            frame_count = 0
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break

                # Procesar frame
                processed_frame = self._remove_watermark_with_model(frame, mask)

                # Guardar frame procesado
                frame_filename = temp_frames_dir / f"frame_{frame_count:06d}.png"
                cv2.imwrite(str(frame_filename), processed_frame)

                frame_count += 1

                # Reportar progreso
                if progress_callback:
                    progress = (frame_count / self.total_frames) * 100
                    progress_callback(progress)

                if frame_count % 30 == 0:
                    print(f"Procesados {frame_count}/{self.total_frames} frames ({frame_count/self.total_frames*100:.1f}%)")

            print(f"Frames procesados: {frame_count}")

            # Recomponer video usando ffmpeg
            print("Recomponiendo video con ffmpeg...")
            self._reassemble_video(temp_frames_dir, output_path)

            print(f"Video procesado guardado en: {output_path}")

        finally:
            # Limpiar archivos temporales
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error limpiando archivos temporales: {e}")

    def _reassemble_video(self, frames_dir: Path, output_path: str):
        """
        Recomponer el video a partir de frames procesados usando ffmpeg.

        Args:
            frames_dir: Directorio con los frames
            output_path: Ruta de salida del video
        """
        # Detectar si el archivo original es un GIF
        is_gif = self.video_path.lower().endswith('.gif')

        if is_gif:
            # Para GIF, usar configuración especial
            frames_pattern = str(frames_dir / "frame_%06d.png")
            ffmpeg_cmd = [
                "ffmpeg",
                "-framerate", str(self.fps),
                "-i", frames_pattern,
                "-vf", "split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5",
                "-loop", "0",  # Loop infinito
                output_path,
                "-y"
            ]

            try:
                result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                print("GIF recompuesto exitosamente")
            except subprocess.CalledProcessError as e:
                print(f"Error en ffmpeg: {e.stderr}")
                raise RuntimeError(f"Error al recomponer GIF: {e.stderr}")
        else:
            # Procesamiento normal de video
            # Extraer audio del video original
            audio_path = frames_dir.parent / "audio.aac"

            # Extraer audio
            extract_audio_cmd = [
                "ffmpeg", "-i", self.video_path,
                "-vn", "-acodec", "copy",
                str(audio_path),
                "-y"
            ]

            try:
                subprocess.run(extract_audio_cmd, check=True, capture_output=True)
                has_audio = True
            except subprocess.CalledProcessError:
                print("Video no tiene audio o no se pudo extraer")
                has_audio = False

            # Crear video a partir de frames
            frames_pattern = str(frames_dir / "frame_%06d.png")

            if has_audio:
                # Video con audio
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-framerate", str(self.fps),
                    "-i", frames_pattern,
                    "-i", str(audio_path),
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    output_path,
                    "-y"
                ]
            else:
                # Video sin audio
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-framerate", str(self.fps),
                    "-i", frames_pattern,
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    output_path,
                    "-y"
                ]

            try:
                result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                print("Video recompuesto exitosamente")
            except subprocess.CalledProcessError as e:
                print(f"Error en ffmpeg: {e.stderr}")
                raise RuntimeError(f"Error al recomponer video: {e.stderr}")

    def cleanup(self):
        """Liberar recursos"""
        if self.cap:
            self.cap.release()

        if self.model and self.model != "fallback":
            del self.model
            self.model = None

        # Limpiar caché de CUDA si está disponible
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def __del__(self):
        """Destructor para asegurar limpieza de recursos"""
        self.cleanup()
