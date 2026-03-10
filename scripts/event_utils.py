#!/usr/bin/env python3
import datetime
import hashlib
import re


TZ = datetime.timezone(datetime.timedelta(hours=8))


def now_iso():
    return datetime.datetime.now(TZ).isoformat(timespec="seconds")


def day_str():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%d")


def normalize_summary(summary):
    return " ".join((summary or "").strip().lower().split())


def tokenize_for_similarity(text):
    """Tokenize text for similarity comparison.
    English: word-level tokens.  Chinese: character-level bigrams.
    This gives meaningful overlap detection for both languages."""
    text = (text or "").strip().lower()
    tokens = set()
    # Extract English/digit words
    for m in re.finditer(r"[a-z0-9]+", text):
        tokens.add(m.group())
    # Extract CJK characters and build bigrams
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    for i in range(len(cjk)):
        tokens.add(cjk[i])  # unigrams
        if i + 1 < len(cjk):
            tokens.add(cjk[i] + cjk[i + 1])  # bigrams
    return tokens


def jaccard_similarity(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def make_fingerprint(kind, scope, summary, project=None):
    raw = "|".join(
        [
            (kind or "").strip().lower(),
            (scope or "").strip().lower(),
            (project or "").strip().lower(),
            normalize_summary(summary),
        ]
    )
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
