from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
import tempfile
import torch
from ultralytics import YOLO
import cv2
import os

app = FastAPI()

# Cargar tu modelo fine-tuned YOLO11 (ajusta la ruta)
yolo_model = YOLO("/Users/juank/Desktop/computer_vision/proyecto/api/yolo11_hpsearch_640_0.001_0.2/weights/best.pt")

# Tus clases
CLASSES = [
    'Vehiculos', 'estructuras', 'carretera', 'rio', 'area descubierta'
]

def run_yolo_inference(image_path):
    results = yolo_model(image_path)
    detections = []

    for r in results:
        for box in r.boxes:
            bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            detections.append({
                "label": cls,
                "name": CLASSES[cls],  # Corrige aquí el nombre
                "score": conf,
                "box": bbox
            })

    return detections

def draw_boxes(image_path, detections, output_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    for det in detections:
        x1, y1, x2, y2 = map(int, det["box"])
        label_name = det["name"]
        score = det["score"]

        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        text = f"{label_name}: {score:.2f}"
        cv2.putText(image, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    annotated_path = output_path
    cv2.imwrite(annotated_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return annotated_path

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        results = run_yolo_inference(tmp_path)
        return JSONResponse(content={"detections": results})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        results = run_yolo_inference(tmp_path)

        annotated_path = tmp_path.replace(".jpg", "_annotated.jpg")
        draw_boxes(tmp_path, results, annotated_path)

        return StreamingResponse(open(annotated_path, "rb"), media_type="image/jpeg")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})