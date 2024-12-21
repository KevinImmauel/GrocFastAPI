# Grocery Detection API using YOLOv8

## Overview
This project is a FastAPI-based application for real-time grocery item detection using a custom-trained YOLOv8 model. It identifies grocery items such as apples, tomatoes, bananas, and grapes from uploaded images.

## Features
- Custom YOLOv8 model for grocery detection.
- Supports real-time prediction with confidence thresholding.
- Outputs predictions with labels and confidence scores.
- API support for client applications.

---

## Requirements
- Python 3.8+
- ultralytics==8.0.0 (or later)
- OpenCV
- FastAPI
- Uvicorn

### Install Dependencies
```bash
pip install ultralytics opencv-python fastapi uvicorn
```

---

## Running the Server
1. Start the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
2. Use ngrok to expose the server to the internet:
```bash
ngrok http 8000
```
3. Copy the public URL provided by ngrok and use it to access the API endpoint:
```
POST {ngrok-url}/predict/
```

---

## Results
- Outputs detected objects with confidence levels.
- Displays label with the highest confidence.

---

## Notes
- Ensure the dataset is properly labeled and organized.
- Adjust confidence threshold (`conf=0.6`) as needed for performance.
- Update `best.pt` with the latest trained model weights.

---

## License
This project is licensed under the MIT License.

