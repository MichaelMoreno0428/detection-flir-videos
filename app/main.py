from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import tempfile
import torch
from transformers import AutoModelForObjectDetection, AutoProcessor
import cv2

# Inicializa FastAPI
app = FastAPI()

# Monta archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Ruta principal: sirve el frontend
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Cargar modelo RT-DETR fine-tuned
model_path = "model"
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True, use_fast=True)
model = AutoModelForObjectDetection.from_pretrained(model_path, trust_remote_code=True)

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model.to(device)
model.eval()

def run_rtdetr_inference(image_path: str, threshold: float = 0.5):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]]).to(device)
    results = processor.post_process_object_detection(
        outputs, target_sizes=target_sizes, threshold=threshold
    )[0]
    detections = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        detections.append({
            "label": int(label.cpu().item()),
            "score": float(score.cpu().item()),
            "box": [float(coord) for coord in box.cpu().numpy()]
        })
    return detections

def draw_boxes(image_path: str, detections: list, output_path: str, class_names: list = None):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    for det in detections:
        x1, y1, x2, y2 = map(int, det["box"])
        label = det["label"]
        score = det["score"]
        label_name = class_names[label] if class_names and label < len(class_names) else str(label)
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(image, f"{label_name}: {score:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    cv2.imwrite(output_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return output_path

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        results = run_rtdetr_inference(tmp_path)
        return JSONResponse(content={"detections": results})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        results = run_rtdetr_inference(tmp_path)
        annotated_path = tmp_path.replace(".jpg", "_annotated.jpg")
        draw_boxes(tmp_path, results, annotated_path)
        return StreamingResponse(open(annotated_path, "rb"), media_type="image/jpeg")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
