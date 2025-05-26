from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import tempfile
import torch
import cv2
import os
import traceback
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from transformers import AutoProcessor, AutoModelForObjectDetection
from ultralytics import YOLO

app = FastAPI()

# Montaje de estáticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Configuración de dispositivo
device = torch.device("cuda" if torch.cuda.is_available() else 
                     "mps" if torch.backends.mps.is_available() else "cpu")

class BaseDetector(ABC):
    """Clase base para detectores de objetos"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.processor = None
        
    @abstractmethod
    def load_model(self):
        """Cargar el modelo específico"""
        pass
    
    @abstractmethod
    def predict(self, image_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Realizar predicción en imagen"""
        pass
    
    def draw_detections(self, image_path: str, detections: List[Dict], output_path: str, color: tuple = (255, 0, 0)):
        """Dibujar detecciones en imagen"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"No se pudo cargar la imagen: {image_path}")
            
            print(f"Imagen cargada: {img.shape}, Detecciones: {len(detections)}")
            
            for i, det in enumerate(detections):
                try:
                    # Validar que box existe y tiene 4 elementos
                    if "box" not in det or len(det["box"]) != 4:
                        print(f"Detección {i} inválida: {det}")
                        continue
                    
                    x1, y1, x2, y2 = map(int, det["box"])
                    
                    # Validar coordenadas
                    h, w = img.shape[:2]
                    x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
                    y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
                    
                    if x2 <= x1 or y2 <= y1:
                        print(f"Coordenadas inválidas en detección {i}: ({x1},{y1},{x2},{y2})")
                        continue
                    
                    label_text = self._get_label_text(det)
                    
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                    
                    # Asegurar que el texto esté dentro de la imagen
                    text_y = max(y1 - 5, 15)
                    cv2.putText(img, label_text, (x1, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    
                except Exception as e:
                    print(f"Error procesando detección {i}: {e}")
                    continue
            
            success = cv2.imwrite(output_path, img)
            if not success:
                raise ValueError(f"No se pudo guardar la imagen en: {output_path}")
            
            print(f"Imagen guardada exitosamente: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error en draw_detections: {e}")
            raise
    
    def _get_label_text(self, detection: Dict) -> str:
        """Obtener texto de etiqueta para detección"""
        try:
            score = detection.get("score", 0.0)
            
            if "name" in detection:
                # YOLO format
                return f"{detection['name']}:{score:.2f}"
            elif "label" in detection:
                # RT-DETR format
                return f"{detection['label']}:{score:.2f}"
            else:
                return f"unknown:{score:.2f}"
        except Exception as e:
            print(f"Error generando texto de etiqueta: {e}")
            return "error:0.00"

class RTDETRDetector(BaseDetector):
    """Detector RT-DETR"""
    
    def __init__(self, model_path: str = "model/rtdetr"):
        super().__init__(model_path)
        self.load_model()
    
    def load_model(self):
        """Cargar modelo RT-DETR"""
        self.processor = AutoProcessor.from_pretrained(
            self.model_path, trust_remote_code=True, use_fast=True
        )
        self.model = AutoModelForObjectDetection.from_pretrained(
            self.model_path, trust_remote_code=True
        )
        self.model.to(device).eval()
    
    def predict(self, image_path: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Predicción con RT-DETR"""
        img = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=img, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        target_sizes = torch.tensor([img.size[::-1]]).to(device)
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=threshold
        )[0]
        
        detections = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections.append({
                "label": int(label.cpu()),
                "score": float(score.cpu()),
                "box": [float(x) for x in box.cpu().tolist()]
            })
        
        return detections

class YOLODetector(BaseDetector):
    """Detector YOLO"""
    
    CLASSES = ['Vehiculos', 'estructuras', 'carretera', 'rio', 'area descubierta']
    
    def __init__(self, model_path: str = "model/yolo/best.pt"):
        super().__init__(model_path)
        self.load_model()
    
    def load_model(self):
        """Cargar modelo YOLO"""
        self.model = YOLO(self.model_path)
    
    def predict(self, image_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Predicción con YOLO"""
        results = self.model(image_path)
        detections = []
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0].item())
                
                detections.append({
                    "label": cls_id,
                    "name": self.CLASSES[cls_id] if cls_id < len(self.CLASSES) else str(cls_id),
                    "score": float(box.conf[0].item()),
                    "box": [x1, y1, x2, y2]
                })
        
        return detections

class ModelManager:
    """Gestor de modelos"""
    
    def __init__(self):
        self.detectors = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Inicializar todos los modelos"""
        try:
            print("Iniciando carga de RT-DETR...")
            self.detectors['rtdetr'] = RTDETRDetector()
            print("✓ RT-DETR cargado correctamente")
        except Exception as e:
            print(f"✗ Error cargando RT-DETR: {e}")
            traceback.print_exc()
        
        try:
            print("Iniciando carga de YOLO...")
            self.detectors['yolo'] = YOLODetector()
            print("✓ YOLO cargado correctamente")
        except Exception as e:
            print(f"✗ Error cargando YOLO: {e}")
            traceback.print_exc()
    
    def get_detector(self, model_name: str) -> BaseDetector:
        """Obtener detector por nombre"""
        if model_name not in self.detectors:
            raise HTTPException(404, f"Modelo '{model_name}' no encontrado")
        return self.detectors[model_name]
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles"""
        return list(self.detectors.keys())

# Inicializar gestor de modelos
model_manager = ModelManager()

class TempFileManager:
    """Gestor de archivos temporales"""
    
    @staticmethod
    def create_temp_file(file_content: bytes, suffix: str = ".jpg") -> str:
        """Crear archivo temporal"""
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(file_content)
        tmp.close()
        return tmp.name
    
    @staticmethod
    def cleanup_file(file_path: str):
        """Limpiar archivo temporal"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass

# Rutas
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/models")
async def get_models():
    """Obtener modelos disponibles"""
    return JSONResponse({
        "available_models": model_manager.get_available_models()
    })

@app.post("/predict/{model_name}")
async def predict(model_name: str, file: UploadFile = File(...), threshold: float = 0.5):
    """Predicción JSON para cualquier modelo"""
    temp_path = None
    try:
        # Validar modelo
        detector = model_manager.get_detector(model_name)
        
        # Crear archivo temporal
        file_content = await file.read()
        temp_path = TempFileManager.create_temp_file(file_content)
        
        # Realizar predicción
        kwargs = {"threshold": threshold} if model_name == "rtdetr" else {}
        detections = detector.predict(temp_path, **kwargs)
        
        return JSONResponse({
            "model": model_name,
            "detections": detections,
            "count": len(detections)
        })
        
    except Exception as e:
        raise HTTPException(500, f"Error en predicción: {str(e)}")
    finally:
        if temp_path:
            TempFileManager.cleanup_file(temp_path)

@app.post("/predict/{model_name}/image")
async def predict_image(model_name: str, file: UploadFile = File(...), threshold: float = 0.5):
    """Predicción con imagen anotada para cualquier modelo"""
    temp_path = None
    output_path = None
    try:
        # Validar modelo
        detector = model_manager.get_detector(model_name)
        print(f"Usando detector: {model_name}")
        
        # Crear archivo temporal
        file_content = await file.read()
        temp_path = TempFileManager.create_temp_file(file_content)
        print(f"Archivo temporal creado: {temp_path}")
        
        # Realizar predicción
        kwargs = {"threshold": threshold} if model_name == "rtdetr" else {}
        detections = detector.predict(temp_path, **kwargs)
        print(f"Predicción completada. Detecciones: {len(detections)}")
        
        if detections:
            print(f"Primera detección: {detections[0]}")
        
        # Dibujar detecciones
        output_path = temp_path.replace(".jpg", f"_{model_name}.jpg")
        color = (255, 0, 0) if model_name == "rtdetr" else (0, 255, 0)
        
        print(f"Iniciando dibujado de detecciones...")
        annotated_path = detector.draw_detections(temp_path, detections, output_path, color)
        print(f"Dibujado completado: {annotated_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(annotated_path):
            raise FileNotFoundError(f"Archivo anotado no encontrado: {annotated_path}")
        
        return StreamingResponse(
            open(annotated_path, "rb"), 
            media_type="image/jpeg",
            headers={"X-Detection-Count": str(len(detections))}
        )
        
    except Exception as e:
        print(f"ERROR en predict_image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error en predicción: {str(e)}")
    finally:
        if temp_path:
            TempFileManager.cleanup_file(temp_path)
        if output_path and output_path != temp_path:
            TempFileManager.cleanup_file(output_path)

# Endpoints de compatibilidad (mantienen la API anterior)
@app.post("/predict")
async def predict_legacy(file: UploadFile = File(...), threshold: float = 0.5):
    """Endpoint legacy para RT-DETR"""
    return await predict("rtdetr", file, threshold)

@app.post("/predict/image") 
async def predict_image_legacy(file: UploadFile = File(...), threshold: float = 0.5):
    """Endpoint legacy para RT-DETR con imagen"""
    return await predict_image("rtdetr", file, threshold)

@app.on_event("startup")
async def startup_event():
    print(f"🚀 Servidor iniciado en dispositivo: {device}")
    print(f"📊 Modelos disponibles: {model_manager.get_available_models()}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)