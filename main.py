from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import cv2
import numpy as np

# Initialize FastAPI app
app = FastAPI()

# Load YOLO model
model_path = "best.pt"
model = YOLO(model_path)

@app.post("/predict/")
async def predict_image(file: UploadFile = File(...)):
    # Check if the uploaded file is an image
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Please upload a JPEG or PNG image.")

    # Read image from upload
    image_bytes = await file.read()
    image_np = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # Run YOLO prediction
    results = model.predict(source=image, conf=0.01)

    # Prepare response data
    response_data = []
    highest = 0
    labelHigh = ''

    for result in results:
        for box in result.boxes:
            confidence = box.conf[0]
            class_id = int(box.cls[0])
            label = model.names[class_id]
            if float(f'{confidence:.2}') > highest:
                highest = float(f'{confidence:.2}')
                labelHigh = label

    response_data.append({
        labelHigh:highest
    })

    return JSONResponse(content={"results": response_data})

# Run the app with `uvicorn filename:app --reload`

# uvicorn main:app --host 0.0.0.0 --port 8000
# ngrok http 8000                                                                                                                                                                                                                          