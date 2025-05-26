# detection-flir-videos

Pipeline de detección de objetos en vídeo termal FLIR, desplegado como aplicación web con FastAPI.

## Estructura

- **app/**: código de la aplicación
  - `main.py`: endpoints y arranque de servidor
  - `utils.py`: funciones de inferencia y visualización
  - `templates/`: HTML Jinja2
  - `static/`: CSS y JS
- **model/**: archivos preentrenados del modelo
- `requirements.txt`, `.gitignore`

## Despliegue local

1. Clonar repo y entrar en carpeta  
   ```bash
   git clone https://github.com/tu_usuario/detection-flir-videos.git
   cd detection-flir-videos
