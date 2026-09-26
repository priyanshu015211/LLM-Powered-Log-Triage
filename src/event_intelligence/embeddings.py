"""
Semantic embeddings (Phase 2: "Embeddings").

Embeds each event's mined *template*, not the raw message — templates
collapse near-duplicates so embedding compute isn't wasted re-encoding the
same structural event hundreds of times.

sentence-transformers and torch are already hard dependencies in
requirements.txt. A TF-IDF+SVD fallback is included only so this module
still runs (e.g. in a lightweight CI job) if those aren't installed; the
(N, D) numpy contract is identical either way, so clustering.py doesn't
need to know which path produced it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from src import config
from src.preprocessing.schema import LogEvent


def _embed_with_sentence_transformers(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    embeddings = model.encode(
        texts, batch_size=config.EMBEDDING_BATCH_SIZE,
        show_progress_bar=False, normalize_embeddings=True,
    )
    return np.asarray(embeddings, dtype=np.float32)


def _embed_with_tfidf_fallback(texts: list[str], n_components: int = 64) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD

    vectorizer = TfidfVectorizer(max_features=4096, ngram_range=(1, 2))
    tfidf = vectorizer.fit_transform(texts)

    n_components = max(min(n_components, tfidf.shape[1] - 1, tfidf.shape[0] - 1), 2)
    svd = TruncatedSVD(n_components=n_components, random_state=config.RANDOM_SEED)
    reduced = svd.fit_transform(tfidf)

    norms = np.linalg.norm(reduced, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (reduced / norms).astype(np.float32)


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 2), dtype=np.float32)
    try:
        return _embed_with_sentence_transformers(texts)
    except ImportError:
        print("[embeddings] sentence-transformers/torch not available — "
              "falling back to TF-IDF+SVD. `pip install -r requirements.txt` for the real model.")
        return _embed_with_tfidf_fallback(texts)


def embed_events(events: list[LogEvent], save_path: Optional[Path] = None) -> np.ndarray:
    texts = [e.template or e.message for e in events]
    matrix = embed_texts(texts)

    for i, event in enumerate(events):
        event.embedding_index = i

    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(save_path, matrix)

    return matrix
