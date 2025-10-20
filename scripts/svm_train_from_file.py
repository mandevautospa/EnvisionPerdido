#!/usr/bin/env python3
# scripts/svm_train_from_file.py
import argparse, json, re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


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


def _norm_url(u: str) -> str:
    u = str(u or "").strip()
    if not u:
        return ""
    u = re.sub(r"[\?#].*$", "", u)  # strip query/fragment
    return u.rstrip("/")


def _norm_str(s: str) -> str:
    s = str(s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"[^a-z0-9 ]+", "", s)


def make_series_id(df: pd.DataFrame, id_col: str, url_col: str, title_col: str, loc_col: str) -> pd.Series:
    uid = df.get(id_col, pd.Series("", index=df.index)).astype(str).str.strip()
    url = df.get(url_col, pd.Series("", index=df.index)).map(_norm_url)
    title = df.get(title_col, pd.Series("", index=df.index)).map(_norm_str)
    loc = df.get(loc_col, pd.Series("", index=df.index)).map(_norm_str)

    series_id = uid
    empty_uid = series_id.eq("") | series_id.isna()
    series_id = series_id.where(~empty_uid, url)
    still_empty = series_id.eq("") | series_id.isna()
    series_id = series_id.where(~still_empty, title + "|" + loc)
    return series_id.fillna("")


def build_features(df: pd.DataFrame, title_col: str, desc_col: str, start_col: str, loc_col: str):
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
    num_cols = ["hour", "is_weekend", "venue_library", "venue_park", "venue_church", "venue_museum"]
    return X, num_cols


def main():
    ap = argparse.ArgumentParser(description="Train SVM to classify community-oriented events (CSV or JSON input).")
    ap.add_argument("--input", required=True, help="Path to perdido_events.csv or .json")
    ap.add_argument("--model-path", default="models/community_svm.pkl")

    # column names in your file
    ap.add_argument("--id", default="uid")
    ap.add_argument("--url", default="url")
    ap.add_argument("--title", default="title")
    ap.add_argument("--desc", default="description")
    ap.add_argument("--start", default="start")
    ap.add_argument("--loc", default="location")
    ap.add_argument("--label", default="label", help="1 = community, 0 = not")

    # training options
    ap.add_argument("--propagate-series-labels", action="store_true",
                    help="Copy a series' label to unlabeled recurrences if exactly one label (0/1) exists in that series.")
    ap.add_argument("--collapse-series", action="store_true",
                    help="Train on a single representative row per series (longest description).")

    args = ap.parse_args()

    p = Path(args.input).expanduser().resolve()
    df = load_any(p)

    # ensure columns exist
    for c in [args.title, args.desc, args.start, args.loc]:
        if c not in df.columns:
            df[c] = ""

    # ensure / create series_id
    if "series_id" not in df.columns:
        df["series_id"] = make_series_id(df, args.id, args.url, args.title, args.loc)

    # (optional) propagate labels within series
    if args.propagate_series_labels and args.label in df.columns:
        def propagate(group: pd.Series) -> pd.Series:
            vals = {v for v in group.astype(str) if v in ("0", "1")}
            if len(vals) == 1:
                v = vals.pop()
                return group.where(group.astype(str).isin(["0", "1"]), other=v)
            return group
        df[args.label] = df.groupby("series_id")[args.label].transform(propagate)

    # keep labeled rows only
    if args.label not in df.columns:
        raise SystemExit(f"'{args.label}' column not found in {p}. Add 1/0 labels and retry.")
    # Handle both string and numeric labels (0, 1, 0.0, 1.0, "0", "1")
    labeled_mask = df[args.label].astype(str).str.replace('.0', '', regex=False).isin(["0", "1"])
    df_l = df.loc[labeled_mask].copy()
    if df_l.empty:
        raise SystemExit("No labeled rows found. Fill some labels (1/0) and try again.")

    # (optional) collapse to one row per series for training
    if args.collapse_series:
        desc_len = df_l.get(args.desc, pd.Series("", index=df_l.index)).astype(str).str.len()
        df_l = df_l.assign(_desc_len=desc_len).sort_values(["series_id", "_desc_len"], ascending=[True, False])
        df_l = df_l.drop_duplicates(subset=["series_id"]).drop(columns=["_desc_len"])

    y = df_l[args.label].astype(int).values
    X, num_cols = build_features(df_l, args.title, args.desc, args.start, args.loc)

    pre = ColumnTransformer([
        ("txt", TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, max_df=0.9,
            strip_accents="unicode", sublinear_tf=True
        ), "text"),
        ("num", StandardScaler(with_mean=False), num_cols),
    ], verbose_feature_names_out=False)

    pipe = Pipeline([
        ("pre", pre),
        ("clf", LinearSVC(class_weight="balanced"))
    ])

    # ---- Group-aware split by series_id to avoid leakage ----
    try:
        if df_l["series_id"].nunique() >= 3 and len(np.unique(y)) >= 2:
            groups = df_l["series_id"].astype(str).values
            gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
            train_idx, test_idx = next(gss.split(X, y, groups))
            Xtr, Xte = X.iloc[train_idx], X.iloc[test_idx]
            ytr, yte = y[train_idx], y[test_idx]
            pipe.fit(Xtr, ytr)
            yp = pipe.predict(Xte)
            print("Confusion matrix:\n", confusion_matrix(yte, yp))
            print(classification_report(yte, yp, digits=3))
        else:
            pipe.fit(X, y)
            print("Trained on all labeled data (not enough series/classes for a split).")
    except Exception as e:
        pipe.fit(X, y)
        print("Split failed; trained on all labeled data. Reason:", e)

    Path(args.model_path).parent.mkdir(parents=True, exist_ok=True)
    # Save both old and new metadata keys for compatibility with your tagger
    joblib.dump({
        "pipe": pipe,
        # for compatibility with prior tag script
        "title": args.title, "desc": args.desc, "start": args.start, "loc": args.loc,
        # structured
        "columns": {
            "id": args.id, "url": args.url, "title": args.title,
            "desc": args.desc, "start": args.start, "loc": args.loc,
            "label": args.label
        }
    }, args.model_path)
    pos = int(df_l[args.label].astype(int).sum())
    neg = int(len(df_l) - pos)
    print(f"Saved model → {args.model_path}")
    print(f"Labeled rows: {len(df_l)} | Positives: {pos} | Negatives: {neg}")


if __name__ == "__main__":
    main()
