import io
import base64
import torch
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def run_inference(model, processor, image: Image.Image, device, threshold: float):
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]]).to(device)
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=threshold)[0]
    return results

def visualize_and_encode(image: Image.Image, results, threshold: float):
    fig, ax = plt.subplots(1, figsize=(8, 6))
    ax.imshow(image)
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        if score < threshold: 
            continue
        x0, y0, x1, y1 = box.cpu().numpy()
        rect = patches.Rectangle((x0, y0), x1 - x0, y1 - y0,
                                 linewidth=2, edgecolor='red', facecolor='none')
        ax.add_patch(rect)
        ax.text(x0, y0 - 5, f"{label.item()}: {score:.2f}",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="red", alpha=0.5),
                color="white", fontsize=9)
    plt.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
