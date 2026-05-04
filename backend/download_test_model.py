"""
Quick script to download a base MuRIL model for testing
WARNING: This is NOT trained for sarcasm detection - just for system testing
"""
import os
import sys

# Add trust for certificates
os.environ['HF_HUB_DISABLE_SSL_WARNINGS'] = '1'

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    print("? Transformers loaded successfully")
except ImportError:
    print("? Error: transformers not installed")
    print("Run: pip install transformers")
    sys.exit(1)

try:
    print("\n" + "="*60)
    print("Downloading base MuRIL model...")
    print("="*60)
    print("\n??  WARNING: This is NOT trained for sarcasm detection!")
    print("   It's only for testing the system architecture.\n")
    
    # Download base model
    print("Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        "google/muril-base-cased",
        trust_remote_code=True
    )
    
    print("Downloading model...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "google/muril-base-cased",
        num_labels=2,  # Binary classification (non-sarcastic, sarcastic)
        trust_remote_code=True
    )
    
    # Save to saved_model directory
    save_path = "./saved_model"
    print(f"\nSaving to {save_path}...")
    
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    print("\n" + "="*60)
    print("? Model downloaded successfully!")
    print("="*60)
    
    # Verify files
    print("\nVerifying files...")
    import os
    files = os.listdir(save_path)
    required_files = ['config.json', 'pytorch_model.bin']
    
    for f in required_files:
        if any(f in file for file in files):
            print(f"  ? {f}")
        else:
            print(f"  ??  {f} - checking alternatives...")
    
    print("\nAll files:")
    for f in sorted(files):
        print(f"  - {f}")
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. The model is ready for testing")
    print("2. Start the backend: python main.py")
    print("3. NOTE: This model is NOT trained for sarcasm!")
    print("4. Replace with your trained model for real use")
    print("="*60)
    
except Exception as e:
    print(f"\n? Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check internet connection")
    print("2. Try with VPN if behind firewall")
    print("3. Or manually download from: https://huggingface.co/google/muril-base-cased")
    sys.exit(1)
