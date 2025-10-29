#!/usr/bin/env python3
# scripts/merge_and_propagate_labels.py
"""
Merge manual labels with predicted labels and propagate within series.
Priority: manual label > predicted label > propagate from series
"""
import pandas as pd
from pathlib import Path

def main():
    # Organized paths
    base = Path(__file__).parent.parent
    input_csv = base / "data" / "processed" / "combined_events.csv"
    output_csv = base / "data" / "processed" / "combined_events_auto.csv"
    
    # Load combined data
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} events from {input_csv}")
    
    # Step 1: Merge label and predicted_label (manual takes priority)
    df['final_label'] = df['label'].fillna(df['predicted_label'])
    
    before = df['final_label'].notna().sum()
    print(f"Labels before propagation: {before}/{len(df)}")
    
    # Step 2: Propagate within series (only if series_id is valid)
    def propagate_series(group):
        """For each series, propagate the most common label to unlabeled events."""
        labeled = group[group.notna()]
        if len(labeled) == 0:
            return group
        # Use the most common label in this series
        most_common = labeled.mode()
        if len(most_common) > 0:
            fill_value = most_common.iloc[0]
            return group.fillna(fill_value)
        return group
    
    # Only propagate for valid series_ids (not NaN/empty)
    valid_series = df['series_id'].notna() & (df['series_id'] != '')
    df.loc[valid_series, 'final_label'] = df[valid_series].groupby('series_id')['final_label'].transform(propagate_series)
    
    after = df['final_label'].notna().sum()
    print(f"Labels after propagation: {after}/{len(df)}")
    print(f"Auto-filled: {after - before} events")
    
    # Step 3: Update main label column
    df['label'] = df['final_label']
    df = df.drop(columns=['final_label'])
    
    # Save
    df.to_csv(output_csv, index=False)
    print(f"\nSaved to: {output_csv}")
    
    # Show summary
    print(f"\nLabel distribution:")
    print(df['label'].value_counts(dropna=False))
    
    # Show unlabeled series
    unlabeled = df[df['label'].isna()]
    if len(unlabeled) > 0:
        print(f"\n{len(unlabeled)} events still unlabeled")
        print("\nUnlabeled series:")
        print(unlabeled.groupby('series_id')['title'].first().head(10))

if __name__ == "__main__":
    main()
