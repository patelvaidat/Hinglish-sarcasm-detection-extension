"""
FastAPI Backend for Sarcasm Detection with Fuzzy Logic
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import logging
from datetime import datetime
import json
import os
import re
from pathlib import Path
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import skfuzzy as fuzz
from skfuzzy import control as ctrl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FuzzySystem:
    """Fuzzy inference system for sarcasm degree detection"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.universe = np.arange(0, 1.01, 0.01)
        self._build_fuzzy_rules()
    
    def _build_fuzzy_rules(self):
        """Build the fuzzy control system"""
        # Antecedents
        self.p_sarcastic_var = ctrl.Antecedent(self.universe, "p_sarcastic")
        self.attn_entropy_var = ctrl.Antecedent(self.universe, "attn_entropy")
        self.sentiment_gap_var = ctrl.Antecedent(self.universe, "sentiment_gap")
        self.intensifier_var = ctrl.Antecedent(self.universe, "intensifier")
        self.marker_var = ctrl.Antecedent(self.universe, "marker_score")
        
        # Consequent
        self.sarcasm_level_var = ctrl.Consequent(self.universe, "sarcasm_level")
        
        # Membership functions
        self.p_sarcastic_var["low"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.35])
        self.p_sarcastic_var["medium"] = fuzz.trimf(self.universe, [0.25, 0.50, 0.75])
        self.p_sarcastic_var["high"] = fuzz.trimf(self.universe, [0.65, 1.0, 1.0])
        
        self.attn_entropy_var["low"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.40])
        self.attn_entropy_var["medium"] = fuzz.trimf(self.universe, [0.30, 0.50, 0.70])
        self.attn_entropy_var["high"] = fuzz.trimf(self.universe, [0.60, 1.0, 1.0])
        
        self.sentiment_gap_var["low"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.30])
        self.sentiment_gap_var["medium"] = fuzz.trimf(self.universe, [0.20, 0.45, 0.70])
        self.sentiment_gap_var["high"] = fuzz.trimf(self.universe, [0.55, 1.0, 1.0])
        
        self.intensifier_var["low"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.40])
        self.intensifier_var["medium"] = fuzz.trimf(self.universe, [0.20, 0.50, 0.80])
        self.intensifier_var["high"] = fuzz.trimf(self.universe, [0.60, 1.0, 1.0])
        
        self.marker_var["absent"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.30])
        self.marker_var["partial"] = fuzz.trimf(self.universe, [0.20, 0.50, 0.80])
        self.marker_var["strong"] = fuzz.trimf(self.universe, [0.70, 1.0, 1.0])
        
        self.sarcasm_level_var["none"] = fuzz.trimf(self.universe, [0.0, 0.0, 0.25])
        self.sarcasm_level_var["mild"] = fuzz.trimf(self.universe, [0.15, 0.35, 0.55])
        self.sarcasm_level_var["moderate"] = fuzz.trimf(self.universe, [0.45, 0.60, 0.75])
        self.sarcasm_level_var["heavy"] = fuzz.trimf(self.universe, [0.70, 1.0, 1.0])
        
        # Fuzzy rules
        rules = [
            ctrl.Rule(self.p_sarcastic_var["high"] & self.marker_var["strong"], self.sarcasm_level_var["heavy"]),
            ctrl.Rule(self.p_sarcastic_var["high"] & self.intensifier_var["high"], self.sarcasm_level_var["heavy"]),
            ctrl.Rule(self.p_sarcastic_var["high"] & self.sentiment_gap_var["high"], self.sarcasm_level_var["heavy"]),
            ctrl.Rule(self.p_sarcastic_var["high"] & self.attn_entropy_var["high"], self.sarcasm_level_var["moderate"]),
            ctrl.Rule(self.p_sarcastic_var["high"], self.sarcasm_level_var["moderate"]),
            ctrl.Rule(self.p_sarcastic_var["medium"] & self.marker_var["strong"], self.sarcasm_level_var["moderate"]),
            ctrl.Rule(self.p_sarcastic_var["medium"] & self.sentiment_gap_var["high"], self.sarcasm_level_var["moderate"]),
            ctrl.Rule(self.p_sarcastic_var["medium"] & self.intensifier_var["high"], self.sarcasm_level_var["mild"]),
            ctrl.Rule(self.p_sarcastic_var["medium"], self.sarcasm_level_var["mild"]),
            ctrl.Rule(self.p_sarcastic_var["low"] & self.marker_var["absent"], self.sarcasm_level_var["none"]),
            ctrl.Rule(self.p_sarcastic_var["low"] & self.sentiment_gap_var["low"], self.sarcasm_level_var["none"]),
            ctrl.Rule(self.p_sarcastic_var["low"] & self.marker_var["strong"], self.sarcasm_level_var["mild"]),
            ctrl.Rule(self.marker_var["strong"], self.sarcasm_level_var["heavy"]),
            ctrl.Rule(self.p_sarcastic_var["medium"] & self.attn_entropy_var["high"] & self.sentiment_gap_var["medium"], self.sarcasm_level_var["moderate"]),
            ctrl.Rule(self.p_sarcastic_var["high"] & self.marker_var["partial"] & self.intensifier_var["medium"], self.sarcasm_level_var["heavy"]),
        ]
        
        self.control_system = ctrl.ControlSystem(rules)
        self.simulator = ctrl.ControlSystemSimulation(self.control_system)
        logger.info("Fuzzy system initialized")
    
    def get_sentiment_gap(self, text: str) -> float:
        """Get sentiment gap from VADER"""
        try:
            scores = self.vader.polarity_scores(str(text))
            return float(abs(scores["compound"]))
        except Exception:
            return 0.5
    
    def get_intensifier_score(self, text: str) -> float:
        """Get intensifier score (exclamations, questions, caps)"""
        text = str(text)
        exclamations = text.count("!")
        questions = text.count("?")
        caps_words = len(re.findall(r"\b[A-Z]{2,}\b", text))
        return float(min((exclamations + questions + caps_words) / 5.0, 1.0))
    
    def get_marker_score(self, text: str) -> float:
        """Get sarcasm marker score (emoticons, hashtags)"""
        # FIX 5: Added more Hinglish/emoji sarcasm markers (😅, 🤡, 💩, 🤮, 👎, 🤬)
        emoticons = [":p", ":/", "xd", "xp", ";)", "-_-", "😂", "🤣", "😒", "😭", "😅", "🤡", "💩", "🤮", "👎", "🤬"]
        hashtags = ["#sarcasm", "#sarcastic", "#irony", "#wah", "#wahwah"]
        
        text_lower = str(text).lower()
        total = sum(1 for e in emoticons if e in text_lower) + \
                sum(1 for h in hashtags if h in text_lower)
        
        if total == 0:
            return 0.0
        elif total == 1:
            return 0.5
        return 1.0
    
    def predict_fuzzy_degree(self, text: str, p_sarcastic: float) -> tuple:
        """
        Predict fuzzy degree and score
        Returns: (fuzzy_degree, fuzzy_score)
        """
        # FIX 3: Raised early-exit threshold from 0.15 → 0.20
        if p_sarcastic < 0.20:
            return ("none", 0.0)
        
        try:
            self.simulator.input["p_sarcastic"] = min(p_sarcastic, 1.0)
            self.simulator.input["attn_entropy"] = 0.5
            self.simulator.input["sentiment_gap"] = self.get_sentiment_gap(text)
            self.simulator.input["intensifier"] = self.get_intensifier_score(text)
            self.simulator.input["marker_score"] = self.get_marker_score(text)
            
            self.simulator.compute()
            fuzzy_score = float(self.simulator.output["sarcasm_level"])
        except Exception:
            fuzzy_score = p_sarcastic
        
        # FIX 4: Tighter fuzzy degree bands — humorous < 0.38, mocking < 0.65, else insulting
        if fuzzy_score < 0.38:
            fuzzy_degree = "humorous"
        elif fuzzy_score < 0.65:
            fuzzy_degree = "mocking"
        else:
            fuzzy_degree = "insulting"
        
        return (fuzzy_degree, round(fuzzy_score, 4))

app = FastAPI(title="Sarcasm Detection API", version="1.0.0")

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
    dominant_label: str
    dominant_label_score: float
    tone_label: str
    tone_label_score: float
    label_probabilities: Dict[str, float]
    fuzzy_degree: str
    fuzzy_score: float
    prediction_id: str
    timestamp: str

class ModelHandler:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.id2label = {}
        self.sarcasm_patterns = [
            r'\b(oh (great|wonderful|fantastic|amazing))\b',
            r'\b(yeah|yea) (right|sure)\b',
            r'\b(exactly|precisely) what i (wanted|needed)\b',
            r'\b(love|loving|loved) (working|dealing|having)\b',
            r'\btotally\b.*\bnot\b',
            r'\bsure,?\s+(because|that)\b',
            r'\b(perfect|brilliant|genius)\b.*\!+',
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sarcasm_patterns]
        self.load_model()
    
    def load_model(self):
        """Load the fine-tuned MuRIL model"""
        try:
            logger.info(f"Loading model from {self.model_path}")

            model_dir = Path(self.model_path)
            required_files = [
                "config.json",
                "model.safetensors",
                "tokenizer.json",
                "tokenizer_config.json",
            ]

            if not model_dir.exists() or not model_dir.is_dir():
                raise FileNotFoundError(
                    f"Model directory not found: {model_dir}. "
                    "Set MODEL_PATH to a valid local model folder."
                )

            missing_files = [f for f in required_files if not (model_dir / f).exists()]
            if missing_files:
                raise FileNotFoundError(
                    f"Model directory is missing required files: {missing_files}. "
                    f"Directory checked: {model_dir}"
                )
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_path,
                local_files_only=True,
            )
            self.model.to(self.device)
            self.model.eval()
            self.id2label = {
                int(key): value for key, value in getattr(self.model.config, "id2label", {}).items()
            }
            
            logger.info("Model loaded successfully")
            if self.id2label:
                logger.info(f"Model labels: {self.id2label}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def _heuristic_score(self, text: str) -> float:
        """Fallback sarcasm score based on common sarcastic phrasing."""
        try:
            pattern_matches = sum(1 for pattern in self.compiled_patterns if pattern.search(text))
            # FIX 2: Lowered baseline from 0.3 → 0.1 to avoid inflating non-sarcastic texts
            score = 0.1 + (pattern_matches * 0.25)

            if text.count('!') > 2:
                score += 0.15

            if '"' in text or "'" in text:
                score += 0.1

            return min(score, 0.95)
        except Exception:
            return 0.5
    
    def predict(self, text: str) -> Dict:
        """
        Predict sarcasm probability for input text
        Returns: dict with is_sarcastic, confidence, and sarcasm_score
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)

                label_probs = {
                    self.id2label.get(index, str(index)): probabilities[0][index].item()
                    for index in range(probabilities.shape[-1])
                }

                target_label = None
                for candidate in ("sarcasm", "light-hearted", "heavy-hearted", "negative", "toxic"):
                    if candidate in label_probs:
                        target_label = candidate
                        break

                if target_label is None:
                    target_label = max(label_probs, key=label_probs.get)

                # FIX 6: Only boost with heuristic if it actually matched patterns (> 0.35)
                # Previously always applied, inflating scores for plain non-sarcastic text
                heuristic = self._heuristic_score(text)
                sarcasm_prob = max(label_probs[target_label], heuristic) if heuristic > 0.35 else label_probs[target_label]

                prediction = int(sarcasm_prob > 0.5)
                confidence = max(max(label_probs.values()), sarcasm_prob)
                dominant_label = max(label_probs, key=label_probs.get)
                dominant_label_score = label_probs[dominant_label]
                tone_candidates = {label: score for label, score in label_probs.items() if label != 'neutral'}
                best_tone_label = max(tone_candidates, key=tone_candidates.get) if tone_candidates else 'neutral'
                best_tone_score = tone_candidates.get(best_tone_label, 0.0)

                if dominant_label == 'neutral' and best_tone_score < 0.15 and not prediction:
                    tone_label = 'neutral'
                    tone_label_score = label_probs.get('neutral', dominant_label_score)
                else:
                    tone_label = best_tone_label if best_tone_label != 'neutral' else dominant_label
                    tone_label_score = best_tone_score if best_tone_label != 'neutral' else dominant_label_score
            
            return {
                "is_sarcastic": bool(prediction),
                "confidence": float(confidence),
                "sarcasm_score": float(sarcasm_prob),
                "dominant_label": dominant_label,
                "dominant_label_score": float(dominant_label_score),
                "tone_label": tone_label,
                "tone_label_score": float(tone_label_score),
                "label_probabilities": {label: float(score) for label, score in label_probs.items()}
            }
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise

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

# Initialize model handler, fuzzy system, and logger
DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parent / "saved_model")
MODEL_PATH = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
model_handler = ModelHandler(MODEL_PATH)
fuzzy_system = FuzzySystem()
prediction_logger = PredictionLogger()

@app.get("/")
async def root():
    return {
        "message": "Sarcasm Detection API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_handler.model is not None,
        "device": str(model_handler.device)
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_sarcasm(input_data: TextInput):
    """
    Predict sarcasm in text with fuzzy degree
    """
    try:
        if not input_data.text or len(input_data.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Get prediction
        prediction = model_handler.predict(input_data.text)
        
        # FIX 1: Correctly extract p_sarcastic using hyphenated label keys from label_probabilities
        # Old code used "p_light_hearted" (underscored) which never matched "light-hearted" (hyphenated)
        label_probs = prediction.get("label_probabilities", {})
        p_sarcastic = label_probs.get("light-hearted", 0.0) + label_probs.get("heavy-hearted", 0.0)
        if p_sarcastic == 0.0:
            p_sarcastic = prediction.get("sarcasm_score", 0.0)
        
        fuzzy_degree, fuzzy_score = fuzzy_system.predict_fuzzy_degree(input_data.text, p_sarcastic)
        
        # Generate prediction ID
        prediction_id = f"{datetime.utcnow().timestamp()}_{hash(input_data.text) % 10000}"
        
        # Create response
        response = PredictionResponse(
            is_sarcastic=prediction["is_sarcastic"],
            confidence=prediction["confidence"],
            sarcasm_score=prediction["sarcasm_score"],
            dominant_label=prediction["dominant_label"],
            dominant_label_score=prediction["dominant_label_score"],
            tone_label=prediction["tone_label"],
            tone_label_score=prediction["tone_label_score"],
            label_probabilities=prediction["label_probabilities"],
            fuzzy_degree=fuzzy_degree,
            fuzzy_score=fuzzy_score,
            prediction_id=prediction_id,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Log prediction for MLOps
        prediction_logger.log_prediction(
            text=input_data.text,
            prediction={**prediction, "fuzzy_degree": fuzzy_degree, "fuzzy_score": fuzzy_score},
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
    """
    Batch prediction endpoint for multiple texts with fuzzy degrees
    """
    try:
        results = []
        for input_data in inputs:
            if input_data.text and len(input_data.text.strip()) > 0:
                prediction = model_handler.predict(input_data.text)
                
                # FIX 1 (batch): Same hyphen fix applied here too
                label_probs = prediction.get("label_probabilities", {})
                p_sarcastic = label_probs.get("light-hearted", 0.0) + label_probs.get("heavy-hearted", 0.0)
                if p_sarcastic == 0.0:
                    p_sarcastic = prediction.get("sarcasm_score", 0.0)
                
                fuzzy_degree, fuzzy_score = fuzzy_system.predict_fuzzy_degree(input_data.text, p_sarcastic)
                
                prediction_id = f"{datetime.utcnow().timestamp()}_{hash(input_data.text) % 10000}"
                
                results.append(PredictionResponse(
                    is_sarcastic=prediction["is_sarcastic"],
                    confidence=prediction["confidence"],
                    sarcasm_score=prediction["sarcasm_score"],
                    dominant_label=prediction["dominant_label"],
                    dominant_label_score=prediction["dominant_label_score"],
                    tone_label=prediction["tone_label"],
                    tone_label_score=prediction["tone_label_score"],
                    label_probabilities=prediction["label_probabilities"],
                    fuzzy_degree=fuzzy_degree,
                    fuzzy_score=fuzzy_score,
                    prediction_id=prediction_id,
                    timestamp=datetime.utcnow().isoformat()
                ))
                
                # Log prediction
                prediction_logger.log_prediction(
                    text=input_data.text,
                    prediction={**prediction, "fuzzy_degree": fuzzy_degree, "fuzzy_score": fuzzy_score},
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
    uvicorn.run(app, host="0.0.0.0", port=8000)