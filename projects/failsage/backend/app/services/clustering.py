import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import get_settings

settings = get_settings()


@dataclass
class FailureRecord:
    index: int
    test_id: str
    classname: str
    failure_type: Optional[str]
    failure_message: Optional[str]
    stack_trace: Optional[str]


@dataclass
class FailureCluster:
    cluster_id: str
    representative_message: str
    test_ids: list[str] = field(default_factory=list)
    count: int = 0


def _fingerprint(rec: FailureRecord) -> str:
    """Stable hash for identical failures (exact dedup before TF-IDF clustering)."""
    key = f"{rec.failure_type}::{_first_exception_line(rec.stack_trace)}::{rec.classname.rsplit('.', 1)[0]}"
    return hashlib.md5(key.encode()).hexdigest()[:12]  # noqa: S324


def _first_exception_line(stack_trace: Optional[str]) -> str:
    if not stack_trace:
        return ""
    for line in stack_trace.splitlines():
        line = line.strip()
        if line and not line.startswith("at ") and not line.startswith("File "):
            return line[:200]
    return ""


def _build_text(rec: FailureRecord) -> str:
    parts = []
    if rec.failure_type:
        parts.append(rec.failure_type)
    if rec.failure_message:
        # Normalise variable parts: numbers, UUIDs, file paths
        msg = re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27}", "UUID", rec.failure_message)
        msg = re.sub(r"\b\d+\b", "NUM", msg)
        parts.append(msg[:300])
    if rec.stack_trace:
        # Keep only exception class lines for clustering signal
        exc_lines = [
            ln.strip()
            for ln in rec.stack_trace.splitlines()
            if ln.strip() and not ln.strip().startswith(("at ", "File ", "...", "Caused"))
        ]
        parts.append(" ".join(exc_lines[:5]))
    return " ".join(parts)


def cluster_failures(records: list[FailureRecord]) -> list[FailureCluster]:
    if not records:
        return []

    # Phase 1: exact fingerprint dedup
    fp_to_cluster: dict[str, FailureCluster] = {}
    unmatched: list[FailureRecord] = []

    for rec in records:
        fp = _fingerprint(rec)
        if fp in fp_to_cluster:
            fp_to_cluster[fp].test_ids.append(rec.test_id)
            fp_to_cluster[fp].count += 1
        else:
            unmatched.append(rec)
            fp_to_cluster[fp] = FailureCluster(
                cluster_id=fp,
                representative_message=(rec.failure_message or "")[:200],
                test_ids=[rec.test_id],
                count=1,
            )

    if len(unmatched) < 2:
        return list(fp_to_cluster.values())

    # Phase 2: TF-IDF + cosine similarity for fuzzy grouping
    texts = [_build_text(r) for r in unmatched]
    valid = [(i, t) for i, t in enumerate(texts) if t.strip()]

    if len(valid) < 2:
        return list(fp_to_cluster.values())

    indices, valid_texts = zip(*valid)
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500)
        tfidf = vectorizer.fit_transform(valid_texts)
        sim_matrix = cosine_similarity(tfidf)
    except ValueError:
        return list(fp_to_cluster.values())

    visited = set()
    threshold = settings.cluster_similarity_threshold

    for i, rec_i in enumerate(unmatched):
        if i not in {idx for idx, _ in valid} or i in visited:
            continue
        visited.add(i)
        fp_i = _fingerprint(rec_i)
        cluster = fp_to_cluster[fp_i]

        for j, rec_j in enumerate(unmatched):
            if j <= i or j not in {idx for idx, _ in valid} or j in visited:
                continue
            row = list(indices).index(i) if i in indices else -1
            col = list(indices).index(j) if j in indices else -1
            if row < 0 or col < 0:
                continue
            if sim_matrix[row, col] >= threshold:
                fp_j = _fingerprint(rec_j)
                if fp_j != fp_i:
                    old_cluster = fp_to_cluster.pop(fp_j, None)
                    if old_cluster:
                        cluster.test_ids.extend(old_cluster.test_ids)
                        cluster.count += old_cluster.count
                    visited.add(j)

    return list(fp_to_cluster.values())
