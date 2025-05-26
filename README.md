# Detección de Objetos en Vídeo Termal (FLIR)

**Repositorio:** https://github.com/MichaelMoreno0428/detection-flir-videos

Este proyecto ofrece una **API en FastAPI** y una **interfaz web** para inferir dos modelos de detección de objetos sobre imágenes termales:

- **RT-DETR**: Transformer RT-DETR R50  
- **YOLOv8** (Ultralytics): YOLO optimizado para detección en tiempo real

---

## 📦 Clonar e instalar

```bash
git clone https://github.com/MichaelMoreno0428/detection-flir-videos.git
cd detection-flir-videos

# Inicializa y descarga modelos con Git LFS
git lfs install
git lfs pull

# Crea y activa un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instala dependencias
pip install --upgrade pip
pip install -r requirements.txt

🚀 Ejecutar localmente
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
Abre en tu navegador:


```bash
http://localhost:8000/


🔌 Endpoints disponibles
1. /predict
Método: POST

Descripción: Recibe una imagen y devuelve JSON con las detecciones.

Parámetros:

file (form-data): archivo de imagen.

threshold (form-data, opcional): umbral de confianza (0.0–1.0), defecto 0.5.

Ejemplo:

```bash
curl -X POST "http://35.247.251.247:8000/predict" \
  -F file=@imagen.jpg \
  -F threshold=0.6
Respuesta:

```json
{
  "detections": [
    {"label": 0, "score": 0.82, "box": [x1, y1, x2, y2]},
    {"label": 1, "score": 0.75, "box": [x1, y1, x2, y2]}
  ]
}
2. /predict/image
Método: POST

Descripción: Recibe una imagen y devuelve la misma con cajas dibujadas.

Parámetros:

file (form-data): archivo de imagen.

threshold (form-data, opcional): umbral de confianza.

Ejemplo:

``` bash
curl -X POST "http://35.247.251.247:8000/predict/image" \
  -F file=@imagen.jpg \
  -F threshold=0.6 \
  --output salida.jpg
Resultado: se descarga salida.jpg con las detecciones anotadas.

🎯 Modelos disponibles
Modelo	Descripción	Carpeta en model/
RT-DETR	Transformer RT-DETR R50	model/pytorch_model.bin
YOLOv8	Ultralytics YOLOv8 (best.pt)	model/yolo/best.pt

📝 Uso rápido
Levanta el servidor con Uvicorn.

Accede a la interfaz web en http://<TU_IP_O_LOCAL>:8000/.

Prueba los endpoints desde la UI o con curl.

