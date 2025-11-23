/**
 * Watermark Remover - Frontend React Application
 * Aplicación completa para remover marcas de agua de videos
 */

const { useState, useRef, useEffect } = React;

// Configuración de la API
const API_URL = `${window.location.protocol}//${window.location.hostname}:8000`;

/**
 * Componente principal de la aplicación
 */
function WatermarkRemoverApp() {
    // Estados
    const [step, setStep] = useState('upload'); // upload, select, processing, completed
    const [videoFile, setVideoFile] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const [videoInfo, setVideoInfo] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [selection, setSelection] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const [downloadUrl, setDownloadUrl] = useState(null);

    // Referencias
    const canvasRef = useRef(null);
    const imageRef = useRef(null);

    /**
     * Manejar selección de archivo
     */
    const handleFileSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            setVideoFile(file);
            setError(null);
        }
    };

    /**
     * Manejar drag & drop
     */
    const handleDrop = (e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && file.type.startsWith('video/')) {
            setVideoFile(file);
            setError(null);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    /**
     * Subir video al servidor
     */
    const uploadVideo = async () => {
        if (!videoFile) return;

        setError(null);
        setProcessing(true);

        const formData = new FormData();
        formData.append('file', videoFile);

        try {
            const response = await fetch(`${API_URL}/api/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al subir el video');
            }

            const data = await response.json();

            setSessionId(data.session_id);
            setVideoInfo(data);
            setPreviewUrl(`${API_URL}${data.preview_url}`);
            setStep('select');

        } catch (err) {
            setError(err.message);
        } finally {
            setProcessing(false);
        }
    };

    /**
     * Procesar video con el área seleccionada
     */
    const processVideo = async () => {
        if (!selection || !sessionId) return;

        setError(null);
        setProcessing(true);
        setProgress(0);
        setStep('processing');

        const formData = new FormData();
        formData.append('x', Math.round(selection.x));
        formData.append('y', Math.round(selection.y));
        formData.append('width', Math.round(selection.width));
        formData.append('height', Math.round(selection.height));

        try {
            const response = await fetch(`${API_URL}/api/process/${sessionId}`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al procesar el video');
            }

            const data = await response.json();

            setDownloadUrl(`${API_URL}${data.download_url}`);
            setProgress(100);
            setStep('completed');

        } catch (err) {
            setError(err.message);
            setStep('select');
        } finally {
            setProcessing(false);
        }
    };

    /**
     * Reiniciar aplicación
     */
    const reset = () => {
        setStep('upload');
        setVideoFile(null);
        setSessionId(null);
        setVideoInfo(null);
        setPreviewUrl(null);
        setSelection(null);
        setProgress(0);
        setError(null);
        setDownloadUrl(null);
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>🎬 Watermark Remover</h1>
                <p>Remueve marcas de agua de videos usando Inteligencia Artificial</p>
            </header>

            <main className="app-main">
                {error && (
                    <div className="error-message">
                        <strong>Error:</strong> {error}
                    </div>
                )}

                {step === 'upload' && (
                    <UploadStep
                        videoFile={videoFile}
                        onFileSelect={handleFileSelect}
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        onUpload={uploadVideo}
                        processing={processing}
                    />
                )}

                {step === 'select' && (
                    <SelectionStep
                        previewUrl={previewUrl}
                        videoInfo={videoInfo}
                        selection={selection}
                        onSelectionChange={setSelection}
                        onProcess={processVideo}
                        onBack={reset}
                    />
                )}

                {step === 'processing' && (
                    <ProcessingStep
                        progress={progress}
                        videoInfo={videoInfo}
                    />
                )}

                {step === 'completed' && (
                    <CompletedStep
                        downloadUrl={downloadUrl}
                        videoInfo={videoInfo}
                        onReset={reset}
                    />
                )}
            </main>

            <footer className="app-footer">
                <p>Powered by <strong>Kontext-Watermark-Remover</strong> AI Model</p>
            </footer>
        </div>
    );
}

/**
 * Paso 1: Subir video
 */
function UploadStep({ videoFile, onFileSelect, onDrop, onDragOver, onUpload, processing }) {
    return (
        <div className="upload-step">
            <div
                className={`drop-zone ${videoFile ? 'has-file' : ''}`}
                onDrop={onDrop}
                onDragOver={onDragOver}
            >
                {!videoFile ? (
                    <>
                        <div className="drop-zone-icon">📹</div>
                        <p className="drop-zone-text">
                            Arrastra tu video aquí<br />
                            <span>o haz clic para seleccionar</span>
                        </p>
                        <input
                            type="file"
                            accept="video/mp4,video/mov,video/avi,video/mkv,video/webm"
                            onChange={onFileSelect}
                            className="file-input"
                        />
                        <p className="supported-formats">
                            Formatos soportados: MP4, MOV, AVI, MKV, WebM
                        </p>
                    </>
                ) : (
                    <>
                        <div className="file-selected">
                            <div className="file-icon">✓</div>
                            <p className="file-name">{videoFile.name}</p>
                            <p className="file-size">
                                {(videoFile.size / (1024 * 1024)).toFixed(2)} MB
                            </p>
                        </div>
                        <button
                            onClick={onUpload}
                            disabled={processing}
                            className="btn btn-primary"
                        >
                            {processing ? 'Subiendo...' : 'Subir Video'}
                        </button>
                        <button
                            onClick={() => window.location.reload()}
                            className="btn btn-secondary"
                            disabled={processing}
                        >
                            Cambiar Video
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}

/**
 * Paso 2: Seleccionar área de marca de agua
 */
function SelectionStep({ previewUrl, videoInfo, selection, onSelectionChange, onProcess, onBack }) {
    const canvasRef = useRef(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [startPos, setStartPos] = useState(null);
    const [imageLoaded, setImageLoaded] = useState(false);

    useEffect(() => {
        if (previewUrl && canvasRef.current) {
            loadImage();
        }
    }, [previewUrl]);

    const loadImage = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            setImageLoaded(true);
        };

        img.crossOrigin = 'anonymous';
        img.src = previewUrl;
    };

    const handleMouseDown = (e) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        setIsDrawing(true);
        setStartPos({ x, y });
    };

    const handleMouseMove = (e) => {
        if (!isDrawing) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        const width = x - startPos.x;
        const height = y - startPos.y;

        // Actualizar selección temporal
        drawSelection({
            x: startPos.x,
            y: startPos.y,
            width,
            height
        });
    };

    const handleMouseUp = (e) => {
        if (!isDrawing) return;

        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        const x = (e.clientX - rect.left) * scaleX;
        const y = (e.clientY - rect.top) * scaleY;

        const width = x - startPos.x;
        const height = y - startPos.y;

        // Normalizar rectángulo (ancho y alto positivos)
        const normalizedSelection = {
            x: width < 0 ? startPos.x + width : startPos.x,
            y: height < 0 ? startPos.y + height : startPos.y,
            width: Math.abs(width),
            height: Math.abs(height)
        };

        onSelectionChange(normalizedSelection);
        setIsDrawing(false);
    };

    const drawSelection = (sel) => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        // Redibujar imagen
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = previewUrl;
        img.onload = () => {
            ctx.drawImage(img, 0, 0);

            // Dibujar rectángulo de selección
            ctx.strokeStyle = '#ff0000';
            ctx.lineWidth = 3;
            ctx.strokeRect(sel.x, sel.y, sel.width, sel.height);

            // Overlay semi-transparente
            ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
            ctx.fillRect(sel.x, sel.y, sel.width, sel.height);
        };
    };

    useEffect(() => {
        if (selection && imageLoaded) {
            drawSelection(selection);
        }
    }, [selection, imageLoaded]);

    return (
        <div className="selection-step">
            <h2>Selecciona el área de la marca de agua</h2>

            {videoInfo && (
                <div className="video-info">
                    <p><strong>Archivo:</strong> {videoInfo.filename}</p>
                    <p><strong>Resolución:</strong> {videoInfo.resolution}</p>
                    <p><strong>Duración:</strong> {videoInfo.duration.toFixed(2)}s</p>
                    <p><strong>FPS:</strong> {videoInfo.fps.toFixed(2)}</p>
                    <p><strong>Frames totales:</strong> {videoInfo.total_frames}</p>
                </div>
            )}

            <div className="canvas-container">
                <canvas
                    ref={canvasRef}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    className="preview-canvas"
                />
                <p className="instruction">
                    Haz clic y arrastra para seleccionar el área de la marca de agua
                </p>
            </div>

            {selection && (
                <div className="selection-info">
                    <p>
                        <strong>Área seleccionada:</strong> {Math.round(selection.width)} x {Math.round(selection.height)} px
                    </p>
                </div>
            )}

            <div className="button-group">
                <button onClick={onBack} className="btn btn-secondary">
                    Volver
                </button>
                <button
                    onClick={onProcess}
                    disabled={!selection}
                    className="btn btn-primary"
                >
                    Procesar Video
                </button>
            </div>
        </div>
    );
}

/**
 * Paso 3: Procesando video
 */
function ProcessingStep({ progress, videoInfo }) {
    return (
        <div className="processing-step">
            <h2>Procesando video...</h2>
            <div className="processing-animation">
                <div className="spinner"></div>
            </div>
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${progress}%` }}
                ></div>
            </div>
            <p className="progress-text">{progress}%</p>
            <p className="processing-info">
                Esto puede tomar varios minutos dependiendo de la duración del video
                ({videoInfo?.total_frames} frames)
            </p>
            <p className="warning-text">
                ⚠️ No cierres esta ventana durante el procesamiento
            </p>
        </div>
    );
}

/**
 * Paso 4: Procesamiento completado
 */
function CompletedStep({ downloadUrl, videoInfo, onReset }) {
    return (
        <div className="completed-step">
            <div className="success-icon">✓</div>
            <h2>¡Video procesado exitosamente!</h2>
            <p className="success-message">
                Tu video ha sido procesado y está listo para descargar
            </p>

            <div className="download-section">
                <a
                    href={downloadUrl}
                    download
                    className="btn btn-download"
                >
                    📥 Descargar Video
                </a>
            </div>

            <button onClick={onReset} className="btn btn-secondary">
                Procesar otro video
            </button>
        </div>
    );
}

// Renderizar aplicación
ReactDOM.render(
    <WatermarkRemoverApp />,
    document.getElementById('root')
);
