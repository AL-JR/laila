from transformers import MarianMTModel, MarianTokenizer

def translate_text(text, src_lang="en", tgt_lang="es"):
    """
    Translate text from source language to target language using MarianMT.
    
    Args:
        text (str): Text to translate
        src_lang (str): Source language code (default: "en")
        tgt_lang (str): Target language code (default: "es")
        
    Returns:
        str: Translated text
    """
    print(f"[*] Translating from {src_lang} to {tgt_lang}...")
    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
    
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
    except Exception as e:
        print(f"[✗] Error loading translation model: {e}")
        raise

    tokens = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    translated = model.generate(**tokens)
    output = tokenizer.decode(translated[0], skip_special_tokens=True)
    print("[✓] Translation complete.")
    return output