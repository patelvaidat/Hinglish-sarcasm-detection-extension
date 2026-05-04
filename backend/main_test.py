"""
TEST VERSION - Sarcasm Detection API (No Model Required)
This version uses a simple heuristic for testing the system without a trained model.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import logging
from datetime import datetime
import json
import os
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sarcasm Detection API (TEST MODE)", version="1.0.0-test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str
    platform: str = "twitter"
    post_id: str = None
    metadata: Dict = {}

class PredictionResponse(BaseModel):
    is_sarcastic: bool
    confidence: float
    sarcasm_score: float
    prediction_id: str
    timestamp: str

class SimplePredictor:
    """
    Simple rule-based sarcasm detector for testing
    NOT FOR PRODUCTION - Replace with your trained MuRIL model
    """
    
    def __init__(self):
        # Sarcasm indicators
        self.sarcasm_patterns = [
            r'\b(oh (great|wonderful|fantastic|amazing))\b',
            r'\b(yeah|yea) (right|sure)\b',
            r'\b(exactly|precisely) what i (wanted|needed)\b',
            r'\b(love|loving|loved) (working|dealing|having)\b',
            r'\btotally\b.*\bnot\b',
            r'\bsure,?\s+(because|that)\b',
            r'\b(perfect|brilliant|genius)\b.*\!+',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.sarcasm_patterns]
        
        logger.info("? Simple predictor initialized (TEST MODE)")
    
    def predict(self, text: str) -> Dict:
        """
        Simple heuristic-based sarcasm detection
        Returns dict with is_sarcastic, confidence, and sarcasm_score
        """
        try:
            text_lower = text.lower()
            
            # Check for sarcasm patterns
            pattern_matches = sum(1 for pattern in self.compiled_patterns if pattern.search(text))
            
            # Check for punctuation indicators
            exclamation_count = text.count('!')
            question_count = text.count('?')
            
            # Check for quotes
            has_quotes = '"' in text or "'" in text
            
            # Calculate sarcasm score (0-1)
            score = 0.3  # Base score
            
            # Add points for pattern matches
            score += pattern_matches * 0.25
            
            # Add points for excessive punctuation
            if exclamation_count > 2:
                score += 0.15
            
            # Add points for quotes (often used in sarcasm)
            if has_quotes:
                score += 0.1
            
            # Cap at 0.95
            score = min(score, 0.95)
            
            # Determine if sarcastic
            is_sarcastic = score > 0.5
            
            # Confidence is how far from 0.5
            confidence = abs(score - 0.5) * 2
            confidence = max(0.5, min(confidence, 0.95))
            
            logger.info(f"Prediction: {is_sarcastic}, Score: {score:.2f}, Text: {text[:50]}...")
            
            return {
                "is_sarcastic": is_sarcastic,
                "confidence": float(confidence),
                "sarcasm_score": float(score)
            }
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            # Return neutral prediction on error
            return {
                "is_sarcastic": False,
                "confidence": 0.5,
                "sarcasm_score": 0.5
            }

class PredictionLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.predictions_file = self.log_dir / "predictions.jsonl"
    
    def log_prediction(self, text: str, prediction: Dict, metadata: Dict):
        """Log prediction for future retraining"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "prediction": prediction,
            "metadata": metadata
        }
        
        with open(self.predictions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# Initialize predictor and logger
predictor = SimplePredictor()
prediction_logger = PredictionLogger()

@app.get("/")
async def root():
    return {
        "message": "Sarcasm Detection API (TEST MODE)",
        "version": "1.0.0-test",
        "status": "running",
        "warning": "Using simple heuristics - replace with trained MuRIL model"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": True,
        "mode": "TEST - Simple Heuristics",
        "device": "cpu"
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_sarcasm(input_data: TextInput):
    """Predict sarcasm in text"""
    try:
        if not input_data.text or len(input_data.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get prediction
        prediction = predictor.predict(input_data.text)
        
        # Generate prediction ID
        prediction_id = f"{datetime.utcnow().timestamp()}_{hash(input_data.text) % 10000}"
        
        # Create response
        response = PredictionResponse(
            is_sarcastic=prediction["is_sarcastic"],
            confidence=prediction["confidence"],
            sarcasm_score=prediction["sarcasm_score"],
            prediction_id=prediction_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Log prediction
        prediction_logger.log_prediction(
            text=input_data.text,
            prediction=prediction,
            metadata={
                "platform": input_data.platform,
                "post_id": input_data.post_id,
                **input_data.metadata
            }
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in prediction endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
async def predict_batch(inputs: List[TextInput]):
    """Batch prediction endpoint"""
    try:
        results = []
        for input_data in inputs:
            if input_data.text and len(input_data.text.strip()) > 0:
                prediction = predictor.predict(input_data.text)
                prediction_id = f"{datetime.utcnow().timestamp()}_{hash(input_data.text) % 10000}"
                
                results.append(PredictionResponse(
                    is_sarcastic=prediction["is_sarcastic"],
                    confidence=prediction["confidence"],
                    sarcasm_score=prediction["sarcasm_score"],
                    prediction_id=prediction_id,
                    timestamp=datetime.utcnow().isoformat()
                ))
                
                prediction_logger.log_prediction(
                    text=input_data.text,
                    prediction=prediction,
                    metadata={
                        "platform": input_data.platform,
                        "post_id": input_data.post_id,
                        **input_data.metadata
                    }
                )
        
        return results
    
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get prediction statistics"""
    try:
        predictions_file = Path("logs/predictions.jsonl")
        if not predictions_file.exists():
            return {"total_predictions": 0}
        
        total = 0
        sarcastic_count = 0
        
        with open(predictions_file, "r", encoding="utf-8") as f:
            for line in f:
                total += 1
                entry = json.loads(line)
                if entry["prediction"]["is_sarcastic"]:
                    sarcastic_count += 1
        
        return {
            "total_predictions": total,
            "sarcastic_count": sarcastic_count,
            "non_sarcastic_count": total - sarcastic_count,
            "sarcasm_rate": sarcastic_count / total if total > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("??  RUNNING IN TEST MODE")
    print("="*60)
    print("Using simple heuristic-based sarcasm detection")
    print("This is NOT production-ready!")
    print("Replace with your trained MuRIL model for real use")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
