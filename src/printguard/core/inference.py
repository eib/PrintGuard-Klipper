"""Inference functions."""

import logging
from io import BytesIO
from typing import Union

import numpy as np
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)


def get_transform():
    """Image preprocessing transform."""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.Grayscale(num_output_channels=3),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])


def preprocess_image(image: Union[bytes, Image.Image]) -> np.ndarray:
    """Preprocess image for inference."""
    transform = get_transform()
    if isinstance(image, bytes):
        image = Image.open(BytesIO(image)).convert('RGB')
    else:
        image = image.convert('RGB')
    tensor = transform(image)
    return tensor.unsqueeze(0).numpy()


def predict(image: Union[bytes, Image.Image], model_info: dict, sensitivity: float = 1.0) -> dict:
    """Run prediction on an image."""
    image_array = preprocess_image(image)
    # Get embedding
    outputs = model_info["session"].run(
        [model_info["output_name"]], 
        {model_info["input_name"]: image_array}
    )
    embedding = outputs[0].flatten()
    
    # Compute distances to prototypes
    prototypes = model_info["prototypes"]
    class_names = model_info["class_names"]
    defect_idx = model_info["defect_idx"]
    distances = np.linalg.norm(prototypes - embedding, axis=1)
    
    # Apply sensitivity adjustment
    adjusted_distances = distances.copy()
    safe_sensitivity = max(0.001, sensitivity)
    
    if defect_idx >= 0 and safe_sensitivity != 1.0:
        adjustment = 1.0 / safe_sensitivity
        adjusted_distances[defect_idx] *= adjustment
    
    # Calculate Softmax Probabilities from adjusted distances
    temperature = 0.1 
    scores = -adjusted_distances / temperature
    exp_scores = np.exp(scores - np.max(scores)) 
    probabilities = exp_scores / exp_scores.sum()
    
    # Get the winning class
    predicted_idx = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_idx])
    
    # Standardize the class name if it's the defect index
    class_name = class_names[predicted_idx]
    if defect_idx >= 0 and predicted_idx == defect_idx:
        class_name = "defect"
    
    if safe_sensitivity != 1.0:
        orig_defect_dist = distances[defect_idx] if defect_idx >= 0 else 0
        adj_defect_dist = adjusted_distances[defect_idx] if defect_idx >= 0 else 0
        logger.debug(
            f"Sensitivity {safe_sensitivity} | "
            f"Winner: {class_name} ({confidence*100:.1f}%) | "
            f"Defect Dist: {orig_defect_dist:.4f} -> {adj_defect_dist:.4f}"
        )
    
    return {
        "class_name": class_name,
        "class_idx": predicted_idx,
        "confidence": confidence,
        "distances": {name: float(d) for name, d in zip(class_names, distances)},
        "probabilities": {name: float(p) for name, p in zip(class_names, probabilities)},
    }
