#!/usr/bin/env python3
# scripts/fill_recurring_labels.py
"""
Auto-fill labels for recurring events based on series_id.
If any event in a series has a label, apply it to all events in that series.
"""
import argparse
from pathlib import Path
import pandas as pd
import re


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
    """Generate series_id for grouping recurring events."""
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


def fill_recurring_labels(df: pd.DataFrame, label_col: str = "label") -> pd.DataFrame:
    """
    Fill missing labels for recurring events based on series_id.
    If any event in a series has a label, propagate it to all unlabeled events in that series.
    
    Args:
        df: DataFrame with events
        label_col: Name of the label column
    
    Returns:
        DataFrame with filled labels
    """
    if "series_id" not in df.columns:
        raise ValueError("DataFrame must have 'series_id' column")
    
    if label_col not in df.columns:
        df[label_col] = None
    
    def propagate(group: pd.Series) -> pd.Series:
        """Propagate label within a series if exactly one label (0 or 1) exists."""
        # Get all valid labels in this series (0, 1, 0.0, 1.0)
        vals = set()
        for v in group.astype(str):
            clean = v.replace('.0', '', 1).strip()
            if clean in ("0", "1"):
                vals.add(clean)
        
        # If exactly one label type exists in this series, apply to all
        if len(vals) == 1:
            label_val = vals.pop()
            # Fill missing values with the common label
            return group.where(
                group.astype(str).str.replace('.0', '', 1).isin(["0", "1"]),
                other=label_val
            )
        return group
    
    df[label_col] = df.groupby("series_id")[label_col].transform(propagate)
    return df


def main():
    ap = argparse.ArgumentParser(
        description="Auto-fill labels for recurring events based on series_id."
    )
    ap.add_argument("--input", required=True, help="Path to CSV file with events")
    ap.add_argument("--output", help="Output path (defaults to input_filled.csv)")
    ap.add_argument("--label-col", default="label", help="Name of label column (default: label)")
    
    # Column mappings for series_id generation
    ap.add_argument("--id-col", default="uid", help="UID column name")
    ap.add_argument("--url-col", default="url", help="URL column name")
    ap.add_argument("--title-col", default="title", help="Title column name")
    ap.add_argument("--loc-col", default="location", help="Location column name")
    
    args = ap.parse_args()
    
    # Load data
    input_path = Path(args.input).expanduser().resolve()
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} events")
    
    # Generate or verify series_id
    if "series_id" not in df.columns:
        print("Generating series_id for recurring events...")
        df["series_id"] = make_series_id(df, args.id_col, args.url_col, args.title_col, args.loc_col)
    
    # Count before
    if args.label_col in df.columns:
        labeled_before = df[args.label_col].astype(str).str.replace('.0', '', 1).isin(["0", "1"]).sum()
    else:
        labeled_before = 0
    
    print(f"Labels before: {labeled_before}/{len(df)}")
    
    # Fill recurring labels
    print("Propagating labels within event series...")
    df = fill_recurring_labels(df, args.label_col)
    
    # Count after
    labeled_after = df[args.label_col].astype(str).str.replace('.0', '', 1).isin(["0", "1"]).sum()
    print(f"Labels after: {labeled_after}/{len(df)}")
    print(f"Auto-filled: {labeled_after - labeled_before} events")
    
    # Show series summary
    series_summary = df.groupby("series_id").agg({
        args.label_col: lambda x: x.astype(str).str.replace('.0', '', 1).isin(["0", "1"]).sum(),
        "title": "first"
    }).rename(columns={args.label_col: "labeled_count"})
    
    filled_series = series_summary[series_summary["labeled_count"] > 0].sort_values("labeled_count", ascending=False)
    print(f"\nFilled {len(filled_series)} event series:")
    print(filled_series.head(15).to_string())
    
    # Save output
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = input_path.parent / f"{input_path.stem}_filled.csv"
    
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    # Show remaining unlabeled
    unlabeled = len(df) - labeled_after
    if unlabeled > 0:
        print(f"\n{unlabeled} events still need manual labels")
        unlabeled_df = df[~df[args.label_col].astype(str).str.replace('.0', '', 1).isin(["0", "1"])]
        print("\nUnlabeled events (sample):")
        print(unlabeled_df[["title", "series_id"]].drop_duplicates("series_id").head(10).to_string(index=False))


if __name__ == "__main__":
    main()
