from transformers import YolosImageProcessor, YolosForObjectDetection
from PIL import Image
import torch
import requests
import time
from torchvision import transforms

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start the timer
        result = func(*args, **kwargs)  # Call the function
        end_time = time.time()  # End the timer
        print(f"Function {func.__name__} took {end_time - start_time} seconds to run.")
        return result
    return wrapper

@timer
def detect_object(image, model, image_processor,device,image_size):

    inputs = image_processor(images=image, return_tensors="pt").to(device)
    
    outputs = model(**inputs)

    # print results
    target_sizes = torch.tensor([image_size[::-1]])
    results = image_processor.post_process_object_detection(outputs, threshold=0.9, target_sizes=target_sizes)[0]
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]
        print(
            f"Detected {model.config.id2label[label.item()]} with confidence "
            f"{round(score.item(), 3)} at location {box}"
        )

def load_model():
    model = YolosForObjectDetection.from_pretrained('hustvl/yolos-tiny')
    image_processor = YolosImageProcessor.from_pretrained("hustvl/yolos-tiny")
    return model, image_processor


def main():
    model, image_processor = load_model()

    # Check if CUDA is available and move the model to GPU if it is
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    images = ["target.png", "target2.png", "target3.png"]
    transform = transforms.ToTensor()

    for image_path in images:
        image = Image.open(image_path).convert("RGB")
        image_size = image.size  # Get the size here
        image_tensor = transform(image)  # Convert to tensor

        image_tensor = image_tensor.to(device)
        detect_object(image_tensor, model, image_processor, device,image_size)

    
if __name__ == "__main__":
    main()