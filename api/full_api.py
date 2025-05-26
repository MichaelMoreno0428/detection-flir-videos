from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
import tempfile
import torch
import cv2
import os

# YOLO
from ultralytics import YOLO

# RT-DETR
from transformers import AutoModelForObjectDetection, AutoProcessor

app = FastAPI()

CLASSES = ['Vehiculos', 'estructuras', 'carretera', 'rio', 'area descubierta']

# ==== Cargar YOLO11 ====
yolo_model = YOLO("/Users/juank/Desktop/computer_vision/proyecto/api/yolo11_hpsearch_640_0.001_0.2/weights/best.pt")

def run_yolo_inference(image_path):
    results = yolo_model(image_path)
    detections = []
    for r in results:
        for box in r.boxes:
            bbox = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            cls = int(box.cls[0].item())
            detections.append({
                "label": cls,
                "name": CLASSES[cls],
                "score": conf,
                "box": bbox
            })
    return detections

# ==== Cargar RT-DETR ====
rtdetr_path = "./model"
processor = AutoProcessor.from_pretrained(rtdetr_path, trust_remote_code=True, use_fast=True)
rtdetr_model = AutoModelForObjectDetection.from_pretrained(rtdetr_path, trust_remote_code=True)

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
rtdetr_model.to(device)
rtdetr_model.eval()

def run_rtdetr_inference(image_path, threshold=0.5):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = rtdetr_model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]]).to(device)
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=threshold)[0]
    detections = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        detections.append({
            "label": int(label.cpu().item()),
            "name": CLASSES[int(label.cpu().item())] if int(label.cpu().item()) < len(CLASSES) else str(label),
            "score": float(score.cpu().item()),
            "box": [float(coord) for coord in box.cpu().numpy()]
        })
    return detections

def draw_boxes(image_path, detections, output_path, class_names=CLASSES):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    for det in detections:
        x1, y1, x2, y2 = map(int, det["box"])
        label = det.get("label", 0)
        label_name = det.get("name", str(label))
        score = det["score"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        text = f"{label_name}: {score:.2f}"
        cv2.putText(image, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    cv2.imwrite(output_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return output_path

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_type: str = Query("yolo", enum=["yolo", "rtdetr"])
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        if model_type == "yolo":
            results = run_yolo_inference(tmp_path)
        elif model_type == "rtdetr":
            results = run_rtdetr_inference(tmp_path)
        else:
            return JSONResponse(status_code=400, content={"error": "Modelo no soportado."})

        return JSONResponse(content={"detections": results})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/predict/image")
async def predict_image(
    file: UploadFile = File(...),
    model_type: str = Query("yolo", enum=["yolo", "rtdetr"])
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        if model_type == "yolo":
            results = run_yolo_inference(tmp_path)
        elif model_type == "rtdetr":
            results = run_rtdetr_inference(tmp_path)
        else:
            return JSONResponse(status_code=400, content={"error": "Modelo no soportado."})

        annotated_path = tmp_path.replace(".jpg", "_annotated.jpg")
        draw_boxes(tmp_path, results, annotated_path)

        return StreamingResponse(open(annotated_path, "rb"), media_type="image/jpeg")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})