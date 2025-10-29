# SVM Event Classification Guide

## Overview
This project uses a Support Vector Machine (SVM) to automatically classify events as "community events" (label=1) or "non-community events" (label=0).

## Setup
1. Activate your virtual environment:
   ```powershell
   .\.venvEnvisionPerdido\Scripts\Activate.ps1
   ```

2. All required packages are already installed (pandas, scikit-learn, joblib, etc.)

## Training the Model

Train a new model using your labeled events:

```powershell
python scripts\svm_train_from_file.py --input perdido_events.csv --propagate-series-labels --collapse-series
```

**Options:**
- `--input`: Path to your CSV or JSON file with labeled events
- `--model-path`: Where to save the model (default: `models/community_svm.pkl`)
- `--propagate-series-labels`: Copy labels within event series (recommended)
- `--collapse-series`: Train on one representative event per series (recommended)

**Output:**
- Trained model saved to `models/community_svm.pkl`
- Prints accuracy, precision, recall, and confusion matrix

## Using the Model to Tag New Events

Classify new/unlabeled events using your trained model:

```powershell
python scripts\svm_tag_events.py --input new_events.csv
```

**Options:**
- `--input`: Path to events file (CSV or JSON)
- `--output`: Where to save tagged results (default: `{input}_tagged.csv`)
- `--model-path`: Path to trained model (default: `models/community_svm.pkl`)
- `--confidence`: Add prediction confidence scores
- `--show-predictions`: Print predictions to console

**Examples:**

1. **Basic usage** (tags your current events):
   ```powershell
   python scripts\svm_tag_events.py --input perdido_events.csv
   ```
   Output: `perdido_events_tagged.csv` with a `predicted_label` column

2. **With confidence scores and preview**:
   ```powershell
   python scripts\svm_tag_events.py --input perdido_events.csv --confidence --show-predictions
   ```
   Shows predictions in console and adds `prediction_confidence` column

3. **Custom output location**:
   ```powershell
   python scripts\svm_tag_events.py --input new_events.csv --output results\classified_events.csv
   ```

4. **Export as JSON**:
   ```powershell
   python scripts\svm_tag_events.py --input perdido_events.csv --output tagged_events.json
   ```

## Typical Workflow

1. **Collect events** → Use your data collection script to scrape events
2. **Manually label** → Add a `label` column with 1 (community) or 0 (non-community) for at least 50-100 events
3. **Train model** → Run `svm_train_from_file.py` to create the classifier
4. **Auto-tag new events** → Run `svm_tag_events.py` on new scraped data to predict labels
5. **Review & correct** → Check the predictions, fix errors, retrain with more data

## Understanding the Output

**Labeled columns:**
- `label`: Your manual labels (1 = community, 0 = non-community)
- `predicted_label`: Model's predictions (1 = community, 0 = non-community)
- `prediction_confidence` (optional): How confident the model is (higher = more certain)

**What makes a "community event"?**
Based on your training data, community events typically:
- Are free or low-cost public gatherings
- Focus on local residents and families
- Include: trivia nights, music bingo, Oktoberfest, fundraisers, social gatherings
- Exclude: business meetings, board meetings, workshops, ribbon cuttings

## Tips for Better Accuracy

1. **Label more events** → More training data = better predictions
2. **Balance your labels** → Try to have roughly equal community/non-community examples
3. **Review edge cases** → Pay attention to events the model gets wrong and add similar examples
4. **Retrain regularly** → As you collect more labeled data, retrain the model
5. **Use propagate-series-labels** → If an event repeats (e.g., weekly trivia), one label applies to all

## File Locations

- Training data: `perdido_events.csv`
- Trained model: `models/community_svm.pkl`
- Training script: `scripts/svm_train_from_file.py`
- Tagging script: `scripts/svm_tag_events.py`
