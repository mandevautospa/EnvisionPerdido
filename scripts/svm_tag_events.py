#!/usr/bin/env python3
# scripts/svm_tag_events.py
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd


def load_any(p: Path) -> pd.DataFrame:
    """Load events from CSV or JSON file."""
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    if p.suffix.lower() == ".json":
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "events" in data:
            data = data["events"]
        return pd.json_normalize(data)
    raise SystemExit("Input must be .csv or .json")


def build_features(df: pd.DataFrame, title_col: str, desc_col: str, start_col: str, loc_col: str):
    """Build feature matrix matching training format."""
    text = df[title_col].fillna("") + " " + df[desc_col].fillna("")
    dt = pd.to_datetime(df[start_col], errors="coerce", utc=True)
    hour = dt.dt.hour.fillna(-1).astype(int)
    dow = dt.dt.dayofweek.fillna(-1).astype(int)
    is_weekend = dow.between(5, 6).astype(int)

    loc = df[loc_col].fillna("").str.lower()
    venue_library = loc.str.contains(r"\blibrary\b").astype(int)
    venue_park = loc.str.contains(r"\bpark\b").astype(int)
    venue_church = loc.str.contains(r"\bchurch\b").astype(int)
    venue_museum = loc.str.contains(r"\bmuseum\b|gallery").astype(int)

    X = pd.DataFrame({
        "text": text,
        "hour": hour,
        "is_weekend": is_weekend,
        "venue_library": venue_library,
        "venue_park": venue_park,
        "venue_church": venue_church,
        "venue_museum": venue_museum,
    })
    return X


def main():
    ap = argparse.ArgumentParser(
        description="Use trained SVM model to predict community event labels."
    )
    ap.add_argument("--input", required=True, help="Path to events CSV or JSON file")
    ap.add_argument("--output", help="Path to save tagged output (CSV or JSON, defaults to input_tagged.csv)")
    ap.add_argument("--model-path", default="models/community_svm.pkl", help="Path to trained model")
    ap.add_argument("--confidence", action="store_true", help="Add prediction confidence scores")
    ap.add_argument("--show-predictions", action="store_true", help="Print predictions to console")

    args = ap.parse_args()

    # Load model
    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}\nTrain a model first using svm_train_from_file.py")

    print(f"Loading model from {model_path}...")
    model_data = joblib.load(model_path)
    pipe = model_data["pipe"]

    # Get column mappings from model metadata
    cols = model_data.get("columns", {})
    title_col = cols.get("title", "title")
    desc_col = cols.get("desc", "description")
    start_col = cols.get("start", "start")
    loc_col = cols.get("loc", "location")

    # Load input data
    input_path = Path(args.input).expanduser().resolve()
    print(f"Loading events from {input_path}...")
    df = load_any(input_path)
    print(f"Loaded {len(df)} events")

    # Ensure required columns exist
    for col, default in [(title_col, ""), (desc_col, ""), (start_col, ""), (loc_col, "")]:
        if col not in df.columns:
            df[col] = default

    # Build features
    X = build_features(df, title_col, desc_col, start_col, loc_col)

    # Predict
    print("Classifying events...")
    predictions = pipe.predict(X)
    df["predicted_label"] = predictions

    # Add confidence scores if requested
    if args.confidence:
        # Get decision function scores (distance from hyperplane)
        decision_scores = pipe.decision_function(X)
        # Convert to pseudo-probabilities (0-1 range)
        # Positive = community event, negative = non-community
        confidence = 1 / (1 + pd.Series(decision_scores).abs())
        df["prediction_confidence"] = confidence.values

    # Count predictions
    community_count = int(predictions.sum())
    non_community_count = len(predictions) - community_count
    print(f"\nPredictions: {community_count} community events, {non_community_count} non-community events")

    # Show sample predictions if requested
    if args.show_predictions:
        print("\nSample predictions:")
        display_cols = [title_col, "predicted_label"]
        if args.confidence:
            display_cols.append("prediction_confidence")
        print(df[display_cols].head(20).to_string(index=False))

    # Save output
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        # Default: input_tagged.csv
        output_path = input_path.parent / f"{input_path.stem}_tagged.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".json":
        df.to_json(output_path, orient="records", indent=2)
    else:
        df.to_csv(output_path, index=False)

    print(f"\nTagged events saved to: {output_path}")


if __name__ == "__main__":
    main()
