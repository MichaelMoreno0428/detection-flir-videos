# Detección de Objetos en Vídeo Termal (FLIR)

**Repositorio:** [https://github.com/MichaelMoreno0428/detection-flir-videos](https://github.com/MichaelMoreno0428/detection-flir-videos)

---

## 🎯 Modelos disponibles

| Modelo  | Descripción                      | Carpeta en `model/`         |
|:-------:|:---------------------------------|:----------------------------|
| RT-DETR | Transformer RT-DETR R50          | `model/pytorch_model.bin`   |
| YOLOv8  | Ultralytics YOLOv8 (`best.pt`)   | `model/yolo/best.pt`        |

---

## 📦 Clonar e instalar

```bash
git clone https://github.com/MichaelMoreno0428/detection-flir-videos.git
cd detection-flir-videos

# Inicializa Git LFS y descarga pesos grandes
git lfs install
git lfs pull

# Crea y activa un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instala dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

🚀 Ejecutar localmente
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4

Abre en tu navegador:

Local: http://localhost:8000/

Remoto (VM): http://35.247.251.247:8000/


🔌 Endpoints disponibles
1. POST /predict
Envía una imagen y recibe un JSON con las detecciones de ambos modelos.

Form-data

file (archivo de imagen)

threshold (opcional, 0.0–1.0, defecto 0.5)

curl -X POST "http://35.247.251.247:8000/predict" \
  -F file=@imagen.jpg \
  -F threshold=0.6
Respuesta de ejemplo:
 {
  "detections": [
    { "label": 0, "score": 0.82, "box": [x1, y1, x2, y2] },
    { "label": 1, "score": 0.75, "box": [x1, y1, x2, y2] }
  ]
}

2. POST /predict/image
Envía una imagen y recibe la misma con las cajas dibujadas.

Form-data

file (archivo de imagen)

threshold (opcional)
curl -X POST "http://35.247.251.247:8000/predict/image" \
  -F file=@imagen.jpg \
  -F threshold=0.6 \
  --output salida.jpg

Se descargará salida.jpg con las detecciones anotadas.

📝 Resumen rápido
Clona el repo y descarga los pesos con Git LFS.

Crea/activa tu entorno virtual e instala dependencias.

Ejecuta el servidor con Uvicorn en 0.0.0.0:8000.

Accede a la UI en / o prueba los endpoints con curl.




