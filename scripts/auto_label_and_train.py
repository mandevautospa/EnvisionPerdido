"""
Auto-label new events using existing labeled data, then retrain the model.

This script:
1. Trains an SVM on existing labeled data
2. Predicts labels for new scraped events
3. Propagates labels within event series (recurring events)
4. Merges all data together
5. Retrains the final model on the expanded dataset
"""

import pandas as pd
import numpy as np
import re
import joblib
from pathlib import Path
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Paths
BASE_DIR = Path(__file__).parent.parent
EXISTING_LABELED = BASE_DIR / "combined_events_auto.csv"
NEW_EVENTS = BASE_DIR / "perdido_events_2025.csv"
OUTPUT_COMBINED = BASE_DIR / "perdido_events_2025_labeled.csv"
MODEL_PATH = BASE_DIR / "event_classifier_model.pkl"
VECTORIZER_PATH = BASE_DIR / "event_vectorizer.pkl"

def extract_series_id(uid):
    """Extract series_id from UID if it exists."""
    if pd.isna(uid):
        return None
    match = re.search(r'series_id=(\d+)', str(uid))
    return int(match.group(1)) if match else None

def build_features(df):
    """Build text features from event data."""
    features = []
    for _, row in df.iterrows():
        parts = []
        if pd.notna(row.get('title')):
            parts.append(str(row['title']))
        if pd.notna(row.get('description')):
            parts.append(str(row['description']))
        if pd.notna(row.get('location')):
            parts.append(str(row['location']))
        if pd.notna(row.get('category')):
            parts.append(str(row['category']))
        features.append(' '.join(parts))
    return features

def train_initial_model(labeled_df):
    """Train SVM on existing labeled data."""
    print(f"\n[Training] Using {len(labeled_df)} labeled events...")
    
    # Build features
    X_text = build_features(labeled_df)
    y = labeled_df['label'].values
    
    # Vectorize
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vectorizer.fit_transform(X_text)
    
    # Train model
    model = SVC(kernel='linear', probability=True, random_state=42)
    model.fit(X, y)
    
    # Report accuracy
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"[Training] Initial model accuracy: {accuracy:.2%}")
    
    return model, vectorizer

def predict_labels(model, vectorizer, df):
    """Predict labels for unlabeled events."""
    print(f"\n[Prediction] Predicting labels for {len(df)} events...")
    
    X_text = build_features(df)
    X = vectorizer.transform(X_text)
    
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    confidence = np.max(probabilities, axis=1)
    
    df['label'] = predictions
    df['prediction_confidence'] = confidence
    
    return df

def propagate_series_labels(df):
    """Propagate labels within event series (recurring events)."""
    print(f"\n[Propagation] Propagating labels within event series...")
    
    # Extract series_id if not already present
    if 'series_id' not in df.columns or df['series_id'].isna().all():
        df['series_id'] = df['uid'].apply(extract_series_id)
    
    initial_labeled = df['label'].notna().sum()
    
    # Group by series_id and propagate
    for series_id, group in df.groupby('series_id'):
        if pd.isna(series_id):
            continue
        
        # Get all labels in this series
        labels = group['label'].dropna()
        
        if len(labels) > 0:
            # Use the most common label (or first if tied)
            majority_label = labels.mode()[0] if len(labels.mode()) > 0 else labels.iloc[0]
            
            # Apply to all events in this series
            df.loc[group.index, 'label'] = majority_label
            df.loc[group.index, 'label_source'] = 'series_propagation'
    
    final_labeled = df['label'].notna().sum()
    print(f"[Propagation] Labeled events: {initial_labeled} -> {final_labeled}")
    
    return df

def merge_datasets(existing_df, new_df):
    """Merge existing labeled data with new predictions."""
    print(f"\n[Merging] Combining datasets...")
    
    # Mark sources
    existing_df['label_source'] = 'manual_or_previous'
    new_df['label_source'] = new_df.get('label_source', 'model_prediction')
    
    # Combine
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Remove duplicates based on UID, keeping manual labels
    combined = combined.sort_values('label_source').drop_duplicates(subset=['uid'], keep='first')
    
    print(f"[Merging] Combined dataset: {len(combined)} unique events")
    
    return combined

def train_final_model(df):
    """Train final model on the expanded labeled dataset."""
    print(f"\n[Final Training] Training on expanded dataset...")
    
    # Only use labeled events
    labeled_df = df[df['label'].notna()].copy()
    print(f"[Final Training] Using {len(labeled_df)} labeled events")
    
    if len(labeled_df) < 10:
        print("[Final Training] Not enough labeled data to train!")
        return None, None
    
    # Build features
    X_text = build_features(labeled_df)
    y = labeled_df['label'].values
    
    # Vectorize
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vectorizer.fit_transform(X_text)
    
    # Split for validation
    if len(labeled_df) >= 20:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y
    
    # Train model
    model = SVC(kernel='linear', probability=True, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"[Final Training] Model accuracy: {accuracy:.2%}")
    print("\n[Final Training] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Community', 'Community']))
    
    # Save model
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"\n[Final Training] Model saved to {MODEL_PATH}")
    print(f"[Final Training] Vectorizer saved to {VECTORIZER_PATH}")
    
    return model, vectorizer

def main():
    print("=" * 80)
    print("AUTO-LABEL AND TRAIN PIPELINE")
    print("=" * 80)
    
    # Step 1: Load existing labeled data
    print(f"\n[Loading] Reading existing labeled data from {EXISTING_LABELED}")
    existing_df = pd.read_csv(EXISTING_LABELED)
    labeled_count = existing_df['label'].notna().sum()
    print(f"[Loading] Found {labeled_count} labeled events in existing data")
    
    # Step 2: Train initial model
    labeled_df = existing_df[existing_df['label'].notna()].copy()
    if len(labeled_df) < 5:
        print("\n[Error] Not enough labeled data to train initial model!")
        return
    
    model, vectorizer = train_initial_model(labeled_df)
    
    # Step 3: Load new events
    print(f"\n[Loading] Reading new events from {NEW_EVENTS}")
    new_df = pd.read_csv(NEW_EVENTS)
    print(f"[Loading] Found {len(new_df)} new events")
    
    # Add label column if it doesn't exist
    if 'label' not in new_df.columns:
        new_df['label'] = np.nan
    
    # Step 4: Predict labels for new events
    new_df = predict_labels(model, vectorizer, new_df)
    
    # Step 5: Propagate labels within series
    new_df = propagate_series_labels(new_df)
    
    # Step 6: Merge datasets
    combined_df = merge_datasets(existing_df, new_df)
    
    # Step 7: Propagate again on the merged dataset
    combined_df = propagate_series_labels(combined_df)
    
    # Step 8: Save combined labeled dataset
    combined_df.to_csv(OUTPUT_COMBINED, index=False)
    print(f"\n[Saving] Combined labeled dataset saved to {OUTPUT_COMBINED}")
    
    labeled_final = combined_df['label'].notna().sum()
    unlabeled_final = combined_df['label'].isna().sum()
    print(f"[Saving] Labeled: {labeled_final}, Unlabeled: {unlabeled_final}")
    
    # Step 9: Train final model on expanded dataset
    final_model, final_vectorizer = train_final_model(combined_df)
    
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE!")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  - Combined dataset: {OUTPUT_COMBINED}")
    print(f"  - Trained model: {MODEL_PATH}")
    print(f"  - Vectorizer: {VECTORIZER_PATH}")
    print(f"  - Total events: {len(combined_df)}")
    print(f"  - Labeled events: {labeled_final}")
    print(f"  - Unlabeled events: {unlabeled_final}")
    
    if unlabeled_final > 0:
        print(f"\nNote: {unlabeled_final} events remain unlabeled. Consider manual review.")

if __name__ == "__main__":
    main()
