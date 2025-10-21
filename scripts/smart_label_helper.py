#!/usr/bin/env python3
# scripts/smart_label_helper.py
"""
Smart labeling helper: Uses your trained model to predict labels for new data,
flags low-confidence predictions for manual review, and merges datasets.
"""
import argparse
from pathlib import Path
import pandas as pd
import joblib


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


def smart_label(df: pd.DataFrame, model_path: str, confidence_threshold: float = 0.55):
    """
    Use trained model to predict labels and flag uncertain ones.
    
    Args:
        df: DataFrame with events to label
        model_path: Path to trained SVM model
        confidence_threshold: Flag predictions below this confidence for review (0-1)
    
    Returns:
        DataFrame with 'predicted_label', 'confidence', and 'needs_review' columns
    """
    # Load model
    model_data = joblib.load(model_path)
    pipe = model_data["pipe"]
    
    # Get column mappings
    cols = model_data.get("columns", {})
    title_col = cols.get("title", "title")
    desc_col = cols.get("desc", "description")
    start_col = cols.get("start", "start")
    loc_col = cols.get("loc", "location")
    
    # Ensure columns exist
    for col, default in [(title_col, ""), (desc_col, ""), (start_col, ""), (loc_col, "")]:
        if col not in df.columns:
            df[col] = default
    
    # Build features and predict
    X = build_features(df, title_col, desc_col, start_col, loc_col)
    predictions = pipe.predict(X)
    decision_scores = pipe.decision_function(X)
    
    # Calculate confidence (convert decision function to pseudo-probability)
    confidence = 1 / (1 + pd.Series(decision_scores).abs())
    
    # Add predictions and flags
    df = df.copy()
    df["predicted_label"] = predictions
    df["confidence"] = confidence.values
    df["needs_review"] = confidence.values < confidence_threshold
    
    return df


def main():
    ap = argparse.ArgumentParser(
        description="Smart labeling: predict labels using trained model, flag uncertain ones for review."
    )
    ap.add_argument("--new-data", required=True, help="Path to new unlabeled CSV")
    ap.add_argument("--existing-data", help="Path to existing labeled CSV to merge with")
    ap.add_argument("--model-path", default="models/community_svm.pkl", help="Path to trained model")
    ap.add_argument("--output", help="Output path for labeled/merged CSV")
    ap.add_argument("--confidence-threshold", type=float, default=0.55,
                    help="Flag predictions below this confidence for review (default: 0.55)")
    ap.add_argument("--auto-accept-high-confidence", action="store_true",
                    help="Automatically convert high-confidence predictions to 'label' column")
    
    args = ap.parse_args()
    
    # Check model exists
    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.exists():
        raise SystemExit(f"Model not found: {model_path}\nTrain a model first.")
    
    print(f"Loading model from {model_path}...")
    
    # Load and predict on new data
    new_path = Path(args.new_data).expanduser().resolve()
    print(f"Loading new data from {new_path}...")
    df_new = pd.read_csv(new_path)
    print(f"Loaded {len(df_new)} events")
    
    print("Predicting labels with confidence scores...")
    df_new = smart_label(df_new, str(model_path), args.confidence_threshold)
    
    # Report confidence breakdown
    high_conf = (~df_new["needs_review"]).sum()
    low_conf = df_new["needs_review"].sum()
    print(f"\nPredictions:")
    print(f"  High confidence (>= {args.confidence_threshold}): {high_conf}")
    print(f"  Needs review (< {args.confidence_threshold}): {low_conf}")
    print(f"\nLabel distribution:")
    print(df_new["predicted_label"].value_counts())
    
    # Auto-accept high confidence if requested
    if args.auto_accept_high_confidence:
        df_new["label"] = df_new.apply(
            lambda row: row["predicted_label"] if not row["needs_review"] else None,
            axis=1
        )
        print(f"\nAuto-accepted {high_conf} high-confidence predictions as 'label'")
        print(f"Review and label the {low_conf} flagged events manually")
    
    # Merge with existing data if provided
    if args.existing_data:
        existing_path = Path(args.existing_data).expanduser().resolve()
        print(f"\nLoading existing labeled data from {existing_path}...")
        df_existing = pd.read_csv(existing_path)
        print(f"Loaded {len(df_existing)} existing events")
        
        # Combine, removing duplicates by uid
        combined = pd.concat([df_existing, df_new], ignore_index=True)
        if "uid" in combined.columns:
            before = len(combined)
            combined = combined.drop_duplicates(subset=["uid"], keep="first")
            print(f"Removed {before - len(combined)} duplicate events by UID")
        
        df_output = combined
        print(f"Combined dataset: {len(df_output)} events")
    else:
        df_output = df_new
    
    # Save output
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = new_path.parent / f"{new_path.stem}_smart_labeled.csv"
    
    df_output.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    # Show sample of flagged events for review
    if "needs_review" in df_output.columns:
        flagged = df_output[df_output["needs_review"] == True]
        if len(flagged) > 0:
            print(f"\n{'='*80}")
            print("EVENTS FLAGGED FOR MANUAL REVIEW (low confidence):")
            print(f"{'='*80}")
            display_cols = ["title", "predicted_label", "confidence"]
            if "label" in flagged.columns:
                display_cols.append("label")
            print(flagged[display_cols].head(20).to_string(index=False))
            print(f"\n... and {max(0, len(flagged) - 20)} more. Review these in the CSV file.")


if __name__ == "__main__":
    main()
