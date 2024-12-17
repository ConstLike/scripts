import torch
import torchvision.transforms as transforms
from torchvision import models
import cv2
import numpy as np
import os
import requests


def download_imagenet_labels():
    url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
    local_file = "imagenet_classes.txt"
    if not os.path.exists(local_file):
        print("Downloading ImageNet class labels...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_file, "w") as f:
                f.write(response.text)
            print("Downloaded successfully!")
        else:
            raise Exception(f"Failed to download labels: {response.status_code}")
    return local_file


def main():
    # Load a pre-trained ResNet-18 model with the updated weights argument
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.eval()  # Set the model to evaluation mode

    # Download ImageNet class labels
    class_file = download_imagenet_labels()
    with open(class_file) as f:
        class_names = [line.strip() for line in f.readlines()]

    # Define preprocessing for the frames (ResNet input size: 224x224)
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Open a connection to the webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the webcam")
        return

    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess the frame
        input_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        input_tensor = preprocess(input_frame).unsqueeze(0)  # Add batch dimension

        # Perform inference
        with torch.no_grad():
            outputs = model(input_tensor)
            _, predicted = outputs.max(1)
            label = class_names[predicted.item()]

        # Display the label on the frame
        cv2.putText(frame, f"Prediction: {label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show the video feed
        cv2.imshow("PyTorch Classification", frame)

        # Exit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
