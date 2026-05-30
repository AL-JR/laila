import re
from transformers import MarianMTModel, MarianTokenizer

# MarianMT hard limit — stay safely under it
_MAX_TOKENS = 450

def _split_into_chunks(text, tokenizer, max_tokens):
    """
    Split text into sentence-level chunks that each fit within max_tokens.
    Falls back to word-level splitting if a single sentence is too long.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = ""

    for sentence in sentences:
        candidate = (current + " " + sentence).strip() if current else sentence
        token_count = len(tokenizer.encode(candidate))

        if token_count <= max_tokens:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single sentence exceeds the limit, split by words
            if len(tokenizer.encode(sentence)) > max_tokens:
                words = sentence.split()
                current = ""
                for word in words:
                    candidate = (current + " " + word).strip() if current else word
                    if len(tokenizer.encode(candidate)) <= max_tokens:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        current = word
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def translate_segments(segments, src_lang="en", tgt_lang="es"):
    """
    Translate a list of timed segments in-place.

    Args:
        segments (list[dict]): Each dict has keys: start, end, text
        src_lang (str): Source language code
        tgt_lang (str): Target language code

    Returns:
        list[dict]: Same list with a new 'translated' key added to each segment
    """
    print(f"[*] Translating {len(segments)} segment(s) from {src_lang} to {tgt_lang}...")
    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"

    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        try:
            model = MarianMTModel.from_pretrained(model_name)
        except OSError:
            print("[!] PyTorch weights not found — loading from TensorFlow weights...")
            model = MarianMTModel.from_pretrained(model_name, from_tf=True)
    except Exception as e:
        print(f"[✗] Error loading translation model: {e}")
        raise

    for i, seg in enumerate(segments):
        text = seg["text"].strip()
        if not text:
            seg["translated"] = ""
            continue
        # Each segment is already short — no chunking needed
        tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=_MAX_TOKENS)
        translated = model.generate(**tokens)
        seg["translated"] = tokenizer.decode(translated[0], skip_special_tokens=True)
        print(f"[•] Segment {i+1}/{len(segments)}: {seg['translated'][:60]}")

    print("[✓] Segment translation complete.")
    return segments


def translate_text(text, src_lang="en", tgt_lang="es"):
    """
    Translate text from source language to target language using MarianMT.
    Handles arbitrarily long input by splitting into token-safe chunks.

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
        try:
            model = MarianMTModel.from_pretrained(model_name)
        except OSError:
            print("[!] PyTorch weights not found — loading from TensorFlow weights...")
            model = MarianMTModel.from_pretrained(model_name, from_tf=True)
    except Exception as e:
        print(f"[✗] Error loading translation model: {e}")
        raise

    chunks = _split_into_chunks(text, tokenizer, _MAX_TOKENS)
    print(f"[→] Translating {len(chunks)} chunk(s)...")

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        tokens = tokenizer(chunk, return_tensors="pt", padding=True)
        translated = model.generate(**tokens)
        translated_chunks.append(tokenizer.decode(translated[0], skip_special_tokens=True))
        print(f"[•] Chunk {i+1}/{len(chunks)} translated.")

    output = " ".join(translated_chunks)
    print("[✓] Translation complete.")
    return output