"""
Example: How to prepare and use your MuRIL model for sarcasm detection

This script demonstrates:
1. How to load/save a model compatible with the backend
2. How to test the model before integration
3. Expected model structure

Note: Replace this with your actual trained model
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# ============================================================================
# OPTION 1: If you have a trained model already saved
# ============================================================================

def load_existing_model(model_path="./saved_model"):
    """Load your existing fine-tuned model"""
    print(f"Loading model from {model_path}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    
    print("? Model loaded successfully!")
    return tokenizer, model


# ============================================================================
# OPTION 2: Download base MuRIL model (for testing only)
# ============================================================================

def download_base_model():
    """
    Download base MuRIL model (NOT trained for sarcasm)
    Use this only for testing the system architecture
    """
    print("Downloading base MuRIL model...")
    print("??  WARNING: This is NOT trained for sarcasm detection!")
    print("   Use this only to test the system. You should use your trained model.")
    
    tokenizer = AutoTokenizer.from_pretrained("google/muril-base-cased")
    
    # Create a model with 2 classes (non-sarcastic, sarcastic)
    model = AutoModelForSequenceClassification.from_pretrained(
        "google/muril-base-cased",
        num_labels=2
    )
    
    print("? Base model downloaded")
    return tokenizer, model


# ============================================================================
# OPTION 3: Load your custom trained model from checkpoint
# ============================================================================

def load_from_training_checkpoint(checkpoint_path):
    """
    If you have a checkpoint from your training run
    """
    print(f"Loading from checkpoint: {checkpoint_path}")
    
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint_path)
    
    return tokenizer, model


# ============================================================================
# Save model in correct format for the backend
# ============================================================================

def save_model_for_backend(tokenizer, model, save_path="./saved_model"):
    """
    Save model in the format expected by the backend
    
    This will create:
    - config.json
    - pytorch_model.bin
    - tokenizer_config.json
    - vocab.txt
    - special_tokens_map.json
    """
    print(f"\nSaving model to {save_path}...")
    
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    print(f"? Model saved to {save_path}")
    print("\nFiles created:")
    import os
    for file in os.listdir(save_path):
        print(f"  - {file}")


# ============================================================================
# Test the model
# ============================================================================

def test_model(tokenizer, model):
    """Test the model with sample inputs"""
    print("\n" + "="*60)
    print("Testing Model")
    print("="*60)
    
    # Set model to evaluation mode
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    
    # Test samples
    test_texts = [
        "Oh great, another meeting that could have been an email",
        "Sure, because that's exactly what I wanted to do today",
        "I love working on weekends!",
        "This is a wonderful day and I am very happy",
        "The weather is nice today"
    ]
    
    print(f"\nUsing device: {device}")
    print("\nTest Predictions:\n")
    
    for text in test_texts:
        # Tokenize
        inputs = tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            
            sarcasm_prob = probabilities[0][1].item()
            is_sarcastic = sarcasm_prob > 0.5
            confidence = max(probabilities[0][0].item(), sarcasm_prob)
        
        # Print result
        print(f"Text: {text[:50]}...")
        print(f"  Sarcastic: {is_sarcastic}")
        print(f"  Confidence: {confidence:.4f}")
        print(f"  Sarcasm Score: {sarcasm_prob:.4f}")
        print()


# ============================================================================
# Main function
# ============================================================================

def main():
    print("="*60)
    print("MuRIL Model Preparation for Sarcasm Detection")
    print("="*60)
    print()
    print("Choose an option:")
    print("1. Load existing trained model")
    print("2. Download base MuRIL model (testing only)")
    print("3. Load from training checkpoint")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        model_path = input("Enter model path (default: ./saved_model): ").strip()
        if not model_path:
            model_path = "./saved_model"
        
        try:
            tokenizer, model = load_existing_model(model_path)
        except Exception as e:
            print(f"? Error: {e}")
            print("\nModel not found. Make sure you have trained your model first.")
            return
    
    elif choice == "2":
        print("\n??  This will download the base model (not trained for sarcasm)")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        
        tokenizer, model = download_base_model()
    
    elif choice == "3":
        checkpoint_path = input("Enter checkpoint path: ").strip()
        try:
            tokenizer, model = load_from_training_checkpoint(checkpoint_path)
        except Exception as e:
            print(f"? Error: {e}")
            return
    
    else:
        print("Invalid choice")
        return
    
    # Test the model
    test_model(tokenizer, model)
    
    # Save in correct format
    print("\n" + "="*60)
    save_choice = input("\nSave model for backend? (y/n): ").strip().lower()
    if save_choice == 'y':
        save_path = input("Save path (default: ./saved_model): ").strip()
        if not save_path:
            save_path = "./saved_model"
        
        save_model_for_backend(tokenizer, model, save_path)
        
        print("\n? Model is ready to use with the backend!")
        print(f"\nNext steps:")
        print(f"1. Move the model to backend/saved_model/")
        print(f"2. Start the backend: cd backend && python main.py")
        print(f"3. Test the API: python test_api.py")


# ============================================================================
# If you already have your trained model
# ============================================================================

def quick_save_existing_model():
    """
    Quick function if you already have your model loaded
    
    Usage:
    ```python
    # After training your model:
    model = your_trained_model
    tokenizer = your_tokenizer
    
    model.save_pretrained("./saved_model")
    tokenizer.save_pretrained("./saved_model")
    ```
    """
    pass


if __name__ == "__main__":
    print()
    print("?? Model Preparation Tool")
    print()
    
    # Check if dependencies are installed
    try:
        import transformers
        import torch
        print(f"? PyTorch version: {torch.__version__}")
        print(f"? Transformers version: {transformers.__version__}")
        print(f"? CUDA available: {torch.cuda.is_available()}")
        print()
    except ImportError as e:
        print(f"? Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("pip install torch transformers")
        exit(1)
    
    main()
