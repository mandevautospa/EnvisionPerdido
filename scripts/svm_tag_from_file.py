#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

import joblib
import pandas as pd


def load_any(p: Path) -> pd.DataFrame:
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
    text = df[title_col].fillna("") + " " + df[desc_col].fillna("")
    dt = pd.to_datetime(df[start_col], errors="coerce", utc=True)
    hour = dt.dt.hour.fillna(-1).astype(int)
    dow = dt.dt.dayofweek.fillna(-1).astype(int)
    is_weekend = dow.between(5, 6).astype(int)

    loc = df[loc_col].fillna("").str.lower()
    venue_library = loc.str.contains(r"\blibrary\b").astype(int)
    venue_park    = loc.str.contains(r"\bpark\b").astype(int)
    venue_church  = loc.str.contains(r"\bchurch\b").astype(int)
    venue_museum  = loc.str.contains(r"\bmuseum\b|gallery").astype(int)

    X = pd.DataFrame({
        "text": text,
        "hour": hour,
        "is_weekend": is_weekend,
        "venue_library": venue_library,
        "venue_park": venue_park,
        "venue_church": venue_church,
        "venue_museum": venue_museum,
    })
    num_cols = ["hour","is_weekend","venue_library","venue_park","venue_church","venue_museum"]
    return X, num_cols


def save_any(df: pd.DataFrame, p: Path):
    if p.suffix.lower() == ".csv":
        df.to_csv(p, index=False)
    elif p.suffix.lower() == ".json":
        with open(p, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    else:
        raise SystemExit("Output must be .csv or .json")


def main():
    ap = argparse.ArgumentParser(description="Tag events as community-oriented using a trained SVM model.")
    ap.add_argument("--input", required=True, help="Path to your events CSV or JSON")
    ap.add_argument("--model-path", default="models/community_svm.pkl")
    ap.add_argument("--output", default=None, help="Optional output path; default = <input>.pred.<ext>")
    ap.add_argument("--inplace", action="store_true", help="Write predictions back into the same CSV (adds is_community_pred, svm_margin, svm_confidence)")
    args = ap.parse_args()

    in_path = Path(args.input).expanduser().resolve()
    df = load_any(in_path)

    # Load pipeline + metadata saved by the trainer
    md = joblib.load(args.model_path)
    pipe = md["pipe"]
    cols = md.get("columns", None)
    if cols is None:
        # Back-compat: older model dict had these top-level
        cols = {"title": md["title"], "desc": md["desc"], "start": md["start"], "loc": md["loc"]}

    # Ensure expected columns exist even if blank
    for c in [cols["title"], cols["desc"], cols["start"], cols["loc"]]:
        if c not in df.columns:
            df[c] = ""

    # Build features exactly like training
    X, _ = build_features(df, cols["title"], cols["desc"], cols["start"], cols["loc"])

    # Predict labels and margins
    df["is_community_pred"] = pipe.predict(X)
    # decision_function gives signed distance to hyperplane; abs distance ~= confidence
    try:
        margin = pipe.decision_function(X)
    except Exception:
        # Some sklearn wrappers may not expose decision_function; keep columns anyway
        import numpy as np
        margin = [0.0] * len(df)
    import numpy as np
    df["svm_margin"] = margin
    df["svm_confidence"] = np.abs(df["svm_margin"])

    # Decide output path
    if args.inplace:
        if in_path.suffix.lower() != ".csv":
            raise SystemExit("--inplace only supports CSV inputs.")
        out_path = in_path
    else:
        if args.output:
            out_path = Path(args.output).expanduser().resolve()
        else:
            out_path = in_path.with_suffix(in_path.suffix + ".pred" + in_path.suffix)

    save_any(df, out_path)
    print(f"Wrote predictions → {out_path}")
    print("Preview:")
    cols_show = [c for c in ["title", "is_community_pred", "svm_confidence"] if c in df.columns]
    print(df[cols_show].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
