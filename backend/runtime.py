from functools import lru_cache
from threading import RLock
import numpy as np
from backend.config import settings

_model_lock = RLock()


@lru_cache
def embedder():
    from sentence_transformers import SentenceTransformer
    import torch

    torch.set_num_threads(2)
    model = SentenceTransformer(
        settings().embedding_model, device=settings().model_device, revision=settings().embedding_revision
    )
    if model.get_embedding_dimension() != 384:
        raise ValueError(
            "Configured embedding model must output 384 dimensions; migrate/reindex before changing."
        )
    return model


def embed(texts: list[str]) -> list[list[float]]:
    with _model_lock:
        return embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


@lru_cache
def nli():
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch

    torch.set_num_threads(2)
    cfg = settings()
    tokenizer = AutoTokenizer.from_pretrained(cfg.nli_model, revision=cfg.nli_revision)
    model = (
        AutoModelForSequenceClassification.from_pretrained(cfg.nli_model, revision=cfg.nli_revision)
        .to(cfg.model_device)
        .eval()
    )
    labels = {str(v).lower(): int(k) for k, v in model.config.id2label.items()}
    if not all(label in labels for label in ["contradiction", "entailment", "neutral"]):
        raise ValueError("NLI model must expose contradiction, entailment and neutral labels.")
    return tokenizer, model, labels


def score_pairs(pairs: list[tuple[str, str]]) -> list[dict]:
    if not pairs:
        return []
    import torch

    with _model_lock:
        tokenizer, model, labels = nli()
        outputs = []
        for start in range(0, len(pairs), 12):
            batch = pairs[start : start + 12]
            tokens = tokenizer(
                [p[0] for p in batch],
                [p[1] for p in batch],
                return_tensors="pt",
                padding=True,
                truncation="only_first",
                max_length=512,
            )
            tokens = {k: v.to(model.device) for k, v in tokens.items()}
            with torch.inference_mode():
                probabilities = model(**tokens).logits.softmax(dim=-1).cpu().numpy()
            outputs.extend(
                {label: float(row[index]) for label, index in labels.items()} for row in probabilities
            )
        return outputs


def token_vectors(text: str) -> tuple[list[str], np.ndarray]:
    import torch

    with _model_lock:
        model = embedder()
        features = model.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=model.max_seq_length
        )
        features = {k: v.to(model.device) for k, v in features.items()}
        with torch.inference_mode():
            output = model[0].auto_model(**features)
        mask = features["attention_mask"][0].bool()
        tokens = model.tokenizer.convert_ids_to_tokens(features["input_ids"][0][mask].tolist())
        vectors = output.last_hidden_state[0][mask].cpu().numpy()
        special = set(model.tokenizer.all_special_tokens)
        keep = [i for i, token in enumerate(tokens) if token not in special]
        return [tokens[i] for i in keep], vectors[keep]


@lru_cache
def generator():
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    name = "google/flan-t5-small"
    return AutoTokenizer.from_pretrained(
        name, revision=settings().generator_revision
    ), AutoModelForSeq2SeqLM.from_pretrained(name, revision=settings().generator_revision).eval()


def generate_local(prompt: str, max_tokens: int = 80) -> str:
    import torch

    with _model_lock:
        tokenizer, model = generator()
        inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        with torch.inference_mode():
            ids = model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False, no_repeat_ngram_size=3)
        return tokenizer.decode(ids[0], skip_special_tokens=True).strip()
