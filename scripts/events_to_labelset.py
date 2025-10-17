cat > scripts/events_to_labelset.py << 'PY'
# scripts/events_to_labelset.py (hardened)
import pandas as pd, json, sys, pathlib, re

if len(sys.argv) < 2:
    raise SystemExit("Usage: python scripts/events_to_labelset.py <input.json|csv>")

IN = pathlib.Path(sys.argv[1]).expanduser().resolve()
OUT_RAW = pathlib.Path("data") / "events_latest.csv"
OUT_LBL = pathlib.Path("data") / "labelset.csv"

OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

def load_any(path):
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "events" in data:
            data = data["events"]
        if not isinstance(data, list):
            raise SystemExit("JSON must be list or dict with 'events'.")
        return pd.json_normalize(data)
    elif path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    else:
        raise SystemExit("Input must be .json or .csv")

df = load_any(IN)

# Map your known keys -> canonical
def col(name):
    return name if name in df.columns else None

mapping = {
    "event_id": col("uid") or col("event_id") or col("id") or col("url"),
    "title": col("title") or col("name"),
    "description": col("description") or col("summary") or col("details"),
    "url": col("url") or col("source_page"),
    "location": col("location") or col("venue") or col("place") or col("address"),
    "start_time": col("start") or col("start_time") or col("startDate"),
    "end_time": col("end") or col("end_time") or col("endDate"),
    "cost_text": col("cost_text") or col("price") or col("fee"),
    "tags": col("category") or col("tags") or col("categories"),
    "source": col("source") or col("source_page")
}

# Build normalized frame robustly
out_cols = {}
for k, v in mapping.items():
    out_cols[k] = (df[v] if v is not None else "")

out = pd.DataFrame(out_cols)

# Ensure event_id
if (out["event_id"] == "").all():
    if "url" in out and (out["url"] != "").any():
        out["event_id"] = out["url"]
    else:
        out["event_id"] = (out.get("title","").astype(str) + "|" + out.get("start_time","").astype(str)).factorize()[0]

out.to_csv(OUT_RAW, index=False)

# Build labelset you can hand-tag
labelset = out[["event_id","title","description","start_time","location","url"]].copy()
text = (labelset["title"].fillna("") + " " + labelset["description"].fillna("")).str.lower()

community_kw = r"(festival|parade|market|farmers|community|workshop|class|volunteer|fundraiser|family|youth|meetup|open house|concert|library|park|veterans|food truck|gallery|art\\b|craft\\b)"
noncomm_kw = r"(ribbon cutting|board meeting|committee|webinar|sponsor|chamber members|leads? group|business after hours|b2b|networking)"

labelset["weak_label"] = None
labelset.loc[text.str.contains(community_kw, regex=True, na=False), "weak_label"] = 1
labelset.loc[text.str.contains(noncomm_kw, regex=True, na=False), "weak_label"] = 0
labelset["label"] = ""

labelset.to_csv(OUT_LBL, index=False)

print(f"Wrote {OUT_RAW}")
print(f"Wrote {OUT_LBL}")
PY
