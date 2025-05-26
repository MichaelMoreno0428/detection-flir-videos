import io
import base64
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import torch
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from transformers import RTDetrImageProcessor, RTDetrForObjectDetection
from app.utils import run_inference, visualize_and_encode

# Inicialización de FastAPI
app = FastAPI(title="FLIR Object Detection")

# Montar carpetas estáticas y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Cargar modelo y procesador una sola vez al arrancar
processor = RTDetrImageProcessor.from_pretrained("model")
model = RTDetrForObjectDetection.from_pretrained("model")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result_img": None})

@app.post("/predict/", response_class=HTMLResponse)
async def predict(request: Request, file: UploadFile = File(...), threshold: float = 0.5):
    # Leer imagen subida
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    # Obtener resultados
    results = run_inference(model, processor, image, device, threshold)
    # Generar imagen con bounding boxes y codificarla en base64
    img_encoded = visualize_and_encode(image, results, threshold)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "result_img": img_encoded,
        "filename": file.filename
    })
