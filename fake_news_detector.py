#!/usr/bin/env python3
"""
fake_news_detector.py
- Train a fake-news detection model (TF-IDF + classifier)
- Evaluate and save a pipeline (vectorizer + model) using joblib
Usage:
    python fake_news_detector.py --data data/fake_or_real_news.csv --out model_pipeline.joblib
"""

import argparse
import os
import re
import sys
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.utils import shuffle

# Suppress harmless warnings for clarity
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# -------------------------
# Text cleaning utilities
# -------------------------
def simple_clean_text(text):
    """Simple text cleaning: remove non-letters, lowercase, collapse spaces."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+", " ", text)               # remove URLs
    text = re.sub(r"[^a-zA-Z']", " ", text)            # keep letters and apostrophes
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------
# Dataset loading helpers
# -------------------------
def detect_text_column(df):
    candidates = ['text', 'content', 'article', 'news', 'body']
    for c in candidates:
        if c in df.columns:
            return c
    # try combining title + text if title exists
    if 'title' in df.columns and any(c in df.columns for c in ['text', 'content', 'article', 'body']):
        for c in ['text', 'content', 'article', 'body']:
            if c in df.columns:
                combined = df['title'].fillna('') + ' ' + df[c].fillna('')
                df['__combined_text__'] = combined
                return '__combined_text__'
    # otherwise, take first string column
    for c in df.columns:
        if df[c].dtype == object:
            return c
    return df.columns[0]


def detect_label_column(df):
    candidates = ['label', 'target', 'class', 'is_fake', 'label_type']
    for c in candidates:
        if c in df.columns:
            return c
    # otherwise try to find a small-cardinality column with values like 'FAKE'/'REAL'
    for c in df.columns:
        if df[c].dtype == object:
            if df[c].nunique() <= 5:
                return c
    return None


def normalize_labels(series):
    """Map common label variants to binary 0 (fake) / 1 (real)."""
    s = series.astype(str).str.lower().str.strip()
    mapping = {}
    mapped = []
    for v in s:
        if v in ('fake', '0', 'f', 'false', 'fabricated', 'satire'):
            mapped.append(0)
        elif v in ('real', '1', 't', 'true', 'legit', 'genuine'):
            mapped.append(1)
        else:
            # fallback: if word contains 'fake' or 'hoax'
            if 'fake' in v or 'hoax' in v or 'fabric' in v or 'satire' in v:
                mapped.append(0)
            elif 'real' in v or 'true' in v or 'legit' in v or 'genuine' in v:
                mapped.append(1)
            else:
                # unknown -> treat as NaN for now
                mapped.append(np.nan)
    return pd.Series(mapped, index=series.index)


# -------------------------
# Training pipeline
# -------------------------
def build_pipeline(max_features=10000, ngram_range=(1, 2)):
    """
    Build sklearn Pipeline:
      TfidfVectorizer -> PassiveAggressiveClassifier
    PassiveAggressive works well for text and is fast.
    """
    tfidf = TfidfVectorizer(max_features=max_features,
                            stop_words='english',
                            ngram_range=ngram_range)
    clf = PassiveAggressiveClassifier(max_iter=1000, random_state=42, C=1.0)
    pipeline = Pipeline([
        ('tfidf', tfidf),
        ('clf', clf)
    ])
    return pipeline


# -------------------------
# Main training/eval flow
# -------------------------
def main(args):
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)

    print("Loading dataset:", data_path)
    df = pd.read_csv(data_path)
    print("Dataset shape:", df.shape)

    # attempt to detect text column
    text_col = detect_text_column(df)
    print("Using text column:", text_col)
    df[text_col] = df[text_col].fillna("").astype(str)
    df['text_clean'] = df[text_col].map(simple_clean_text)

    # detect label column
    label_col = detect_label_column(df)
    if label_col is None:
        print("ERROR: Could not detect a label column. Please ensure a column with labels exists.")
        print("Columns:", df.columns.tolist())
        sys.exit(1)
    print("Using label column:", label_col)
    labels = normalize_labels(df[label_col])
    # drop rows with unknown labels
    mask_valid = labels.notna()
    df = df.loc[mask_valid].copy()
    labels = labels.loc[mask_valid].astype(int)

    print("After dropping unknown labels:", df.shape)
    # Shuffle dataset
    df, labels = shuffle(df, labels, random_state=args.random_state)

    # Prepare features/target
    X = df['text_clean'].values
    y = labels.values

    # split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y
    )
    print(f"Train size: {len(X_train)}  Test size: {len(X_test)}")

    # build pipeline
    pipeline = build_pipeline(max_features=args.max_features, ngram_range=(1, args.ngrams))
    print("Training pipeline...")
    pipeline.fit(X_train, y_train)

    # evaluate
    print("Evaluating on test set...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}   F1: {f1:.4f}")
    print("\nClassification report:\n", classification_report(y_test, y_pred, target_names=['FAKE', 'REAL']))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("Confusion matrix:\n", cm)
    # save confusion matrix figure
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['FAKE', 'REAL'], yticklabels=['FAKE', 'REAL'],
           title='Confusion matrix', ylabel='True label', xlabel='Predicted label')
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    cm_path = Path(args.out).with_suffix('.confusion.png')
    fig.savefig(cm_path)
    print("Saved confusion matrix to", cm_path)

    # save pipeline
    out_path = Path(args.out)
    joblib.dump(pipeline, out_path)
    print("Saved pipeline to", out_path)

    # Save a small evaluation CSV (actual, predicted, text preview)
    eval_df = pd.DataFrame({
        'text': X_test,
        'true_label': y_test,
        'pred_label': y_pred
    })
    eval_path = Path(args.out).with_suffix('.eval.csv')
    eval_df.to_csv(eval_path, index=False)
    print("Saved evaluation CSV to", eval_path)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a fake news detection pipeline.")
    parser.add_argument('--data', type=str, required=True,
                        help='Path to CSV dataset (must contain text + label columns)')
    parser.add_argument('--out', type=str, default='model_pipeline.joblib',
                        help='Output path for the saved pipeline (joblib)')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Test set fraction (default 0.2)')
    parser.add_argument('--random-state', type=int, default=42,
                        help='Random seed')
    parser.add_argument('--max-features', type=int, default=10000,
                        help='Max features for TF-IDF (default 10000)')
    parser.add_argument('--ngrams', type=int, default=2,
                        help='Max ngram (1..N) for TF-IDF (default 2)')
    args = parser.parse_args()
    main(args)
