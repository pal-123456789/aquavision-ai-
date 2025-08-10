
from fastapi import FastAPI
from pydantic import BaseModel
import random, time
app = FastAPI(title='Algal Bloom ML')

class PredictRequest(BaseModel):
    lat: float
    lng: float
    temperature: float | None = None

class PredictResponse(BaseModel):
    probability: float
    chlorophyll: float | None = None

@app.post('/predict', response_model=PredictResponse)
def predict(req: PredictRequest):
    # Dummy prediction logic for scaffold: replace with real model inference
    # Use simple heuristic: probability increases with temperature
    base = 0.05
    if req.temperature:
        prob = min(0.98, base + max(0, (req.temperature - 15) * 0.02))
    else:
        prob = 0.1
    # add a little randomness for demo
    prob = max(0.0, min(1.0, prob + random.uniform(-0.05, 0.05)))
    chlorophyll = round(2.0 + prob * 20.0, 3)
    return {'probability': prob, 'chlorophyll': chlorophyll}
