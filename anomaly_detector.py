import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score,
    f1_score, confusion_matrix
)
import warnings
warnings.filterwarnings("ignore")

# CONFIGURATION
FEATURES_FILE  = "features.csv"
RESULTS_FILE   = "anomaly_results.json"
FLAGGED_FILE   = "flagged_transactions.json"

FEATURE_COLS = [
    "locZscore",
    "sizeZscore",
    "loc",
    "sizeBytes",
    "hashFreq",
    "isDuplicate",
    "routeLength",
    "routeIsNormal",
    "hasVerifier",
    "hasDeployer",
    "fromOrg",
    "toOrg",
    "hourOfDay",
    "dayOfWeek",
    "timeGapSeconds",
    "hashEntropy",
    "sigLength",
    "onChain"
]


# LOAD FEATURES
def load_features():
    print(f"\n📂 Loading {FEATURES_FILE}...")
    try:
        df = pd.read_csv(FEATURES_FILE)
        print(f"✅ Loaded {len(df)} records\n")
        return df
    except FileNotFoundError:
        print(f"❌ {FEATURES_FILE} not found. Run feature_extractor.py first.")
        return None


# EVALUATE MODEL
def evaluate(name, model, X_test, y_test, scaler=None):
    if scaler:
        X_test = scaler.transform(X_test)

    preds     = model.predict(X_test)
    precision = precision_score(y_test, preds, zero_division=0)
    recall    = recall_score(y_test, preds, zero_division=0)
    f1        = f1_score(y_test, preds, zero_division=0)

    print(f"\n── {name}")
    print(f"   Precision : {precision*100:.1f}%")
    print(f"   Recall    : {recall*100:.1f}%")
    print(f"   F1 Score  : {f1*100:.1f}%")

    return preds, {"precision": precision, "recall": recall, "f1": f1}


# DETAILED RESULTS
def detailed_results(name, preds, y_test, df_test):
    print(f"\n{'='*55}")
    print(f"  {name} — Detailed Results")
    print(f"{'='*55}")

    cm           = confusion_matrix(y_test, preds)
    tn, fp, fn, tp = cm.ravel()
    precision    = precision_score(y_test, preds, zero_division=0)
    recall       = recall_score(y_test, preds, zero_division=0)
    f1           = f1_score(y_test, preds, zero_division=0)

    print(f"  True Positives  (TP) : {tp:<6} ← anomalies caught ✅")
    print(f"  False Positives (FP) : {fp:<6} ← false alarms")
    print(f"  True Negatives  (TN) : {tn:<6} ← correct normals ✅")
    print(f"  False Negatives (FN) : {fn:<6} ← missed anomalies")
    print(f"  {'─'*45}")
    print(f"  Precision            : {precision:.4f} ({precision*100:.1f}%)")
    print(f"  Recall               : {recall:.4f} ({recall*100:.1f}%)")
    print(f"  F1 Score             : {f1:.4f} ({f1*100:.1f}%)")
    print(f"{'='*55}")

    print(f"\n📋 Detection Rate by Anomaly Type:")
    print(f"  {'Type':<25} {'Total':>6} {'Caught':>7} {'Rate':>8}")
    print(f"  {'─'*50}")

    anomaly_df           = df_test[df_test["isAnomaly"] == 1].copy()
    anomaly_df["predicted"] = preds[df_test["isAnomaly"].values == 1]

    for atype in sorted(anomaly_df["anomalyType"].unique()):
        subset   = anomaly_df[anomaly_df["anomalyType"] == atype]
        total    = len(subset)
        detected = int(subset["predicted"].sum())
        rate     = detected / total * 100 if total > 0 else 0
        print(f"  {atype:<25} {total:>6} {detected:>7} {rate:>7.1f}%")

    return {
        "tp": int(tp), "fp": int(fp),
        "tn": int(tn), "fn": int(fn),
        "precision": round(float(precision), 4),
        "recall"   : round(float(recall), 4),
        "f1_score" : round(float(f1), 4)
    }


# FLAG ANOMALIES
def flag_anomalies(df, preds):
    print(f"\n🚩 Flagging anomalies...")

    flagged = []
    for i, (_, row) in enumerate(df.iterrows()):
        if preds[i] == 1:
            flagged.append({
                "shipmentId"     : row["shipmentId"],
                "contractHash"   : row["contractHash"],
                "flagReason"     : determine_flag_reason(row),
                "anomalyType"    : row["anomalyType"],
                "isActualAnomaly": bool(row["isAnomaly"]),
                "loc"            : int(row["loc"]),
                "sizeBytes"      : int(row["sizeBytes"]),
                "routeLength"    : int(row["routeLength"]),
                "hashFreq"       : int(row["hashFreq"]),
                "timeGapSeconds" : float(row["timeGapSeconds"])
            })

    with open(FLAGGED_FILE, "w") as f:
        json.dump(flagged, f, indent=2)

    true_flags  = sum(1 for f in flagged if f["isActualAnomaly"])
    false_flags = sum(1 for f in flagged if not f["isActualAnomaly"])

    print(f"✅ Total flagged   : {len(flagged)}")
    print(f"   True anomalies : {true_flags}")
    print(f"   False alarms   : {false_flags}")
    print(f"   Saved to       : {FLAGGED_FILE}")

    return flagged


def determine_flag_reason(row) -> str:
    if row.get("isDuplicate", 0) == 1:
        return "Duplicate contract hash detected"
    if row.get("routeIsNormal", 1) == 0:
        return "Unusual routing path"
    if abs(row.get("locZscore", 0)) > 2:
        return "Abnormal contract size"
    if row.get("timeGapSeconds", 3600) < 60:
        return "Rapid resubmission detected"
    return "Statistical anomaly"


# SAVE RESULTS
def save_results(best_name, best_metrics, all_metrics, flagged):
    results = {
        "best_model"    : best_name,
        "total_records" : 4131,
        "features_used" : FEATURE_COLS,
        "model_comparison": {
            name: {
                "precision": round(m["precision"], 4),
                "recall"   : round(m["recall"], 4),
                "f1_score" : round(m["f1"], 4)
            }
            for name, m in all_metrics.items()
        },
        "best_metrics"   : best_metrics,
        "total_flagged"  : len(flagged),
        "true_positives" : sum(1 for f in flagged if f["isActualAnomaly"]),
        "false_positives": sum(1 for f in flagged if not f["isActualAnomaly"])
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {RESULTS_FILE}")


# MAIN
def main():
    print("\n" + "=" * 55)
    print("  Anomaly Detector — Supervised Model Comparison")
    print("=" * 55)

    df = load_features()
    if df is None:
        return

    X = df[FEATURE_COLS].fillna(0).values
    y = df["isAnomaly"].values

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(df)),
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    df_test = df.iloc[idx_test].reset_index(drop=True)

    # Scale for SVM
    scaler = StandardScaler()
    scaler.fit(X_train)
    X_train_scaled = scaler.transform(X_train)

    print(f"  Train set : {len(X_train)} records ({y_train.sum()} anomalies)")
    print(f"  Test set  : {len(X_test)} records ({y_test.sum()} anomalies)")
    print(f"\n🔬 Training supervised models...\n")

    all_metrics = {}

    # ── Decision Tree ──────────────────────────────────
    dt = DecisionTreeClassifier(
        max_depth=10,
        class_weight="balanced",
        random_state=42
    )
    dt.fit(X_train, y_train)
    _, dt_metrics = evaluate("Decision Tree", dt, X_test, y_test)
    all_metrics["DecisionTree"] = dt_metrics

    # ── SVM ────────────────────────────────────────────
    svm = SVC(
        kernel="rbf",
        class_weight="balanced",
        C=10,
        gamma="scale",
        random_state=42
    )
    svm.fit(X_train_scaled, y_train)
    X_test_scaled = scaler.transform(X_test)
    svm_preds     = svm.predict(X_test_scaled)
    svm_precision = precision_score(y_test, svm_preds, zero_division=0)
    svm_recall    = recall_score(y_test, svm_preds, zero_division=0)
    svm_f1        = f1_score(y_test, svm_preds, zero_division=0)
    print(f"\n── SVM (RBF Kernel)")
    print(f"   Precision : {svm_precision*100:.1f}%")
    print(f"   Recall    : {svm_recall*100:.1f}%")
    print(f"   F1 Score  : {svm_f1*100:.1f}%")
    all_metrics["SVM"] = {
        "precision": svm_precision,
        "recall"   : svm_recall,
        "f1"       : svm_f1
    }

    # ── Gradient Boosting ──────────────────────────────
    gb = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    gb.fit(X_train, y_train)
    _, gb_metrics = evaluate("Gradient Boosting", gb, X_test, y_test)
    all_metrics["GradientBoosting"] = gb_metrics

    # ── Random Forest ──────────────────────────────────
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_preds, rf_metrics = evaluate("Random Forest", rf, X_test, y_test)
    all_metrics["RandomForest"] = rf_metrics

    # Feature importance
    importances = pd.Series(
        rf.feature_importances_,
        index=FEATURE_COLS
    ).sort_values(ascending=False)
    print(f"\n   Top 5 Important Features:")
    for feat, imp in importances.head(5).items():
        print(f"     {feat:<25}: {imp:.4f}")

    # ── Pick best ──────────────────────────────────────
    best_name    = max(all_metrics, key=lambda k: all_metrics[k]["f1"])
    best_model   = {"DecisionTree": dt, "SVM": svm,
                    "GradientBoosting": gb, "RandomForest": rf}[best_name]
    best_preds   = rf_preds if best_name == "RandomForest" else best_model.predict(
        X_test_scaled if best_name == "SVM" else X_test
    )

    print(f"\n🏆 Best Model: {best_name} "
          f"(F1: {all_metrics[best_name]['f1']*100:.1f}%)")

    # Detailed results
    best_metrics = detailed_results(best_name, best_preds, y_test, df_test)

    # Full dataset flagging
    print(f"\n🔄 Re-running {best_name} on full dataset for flagging...")
    full_rf = RandomForestClassifier(
        n_estimators=300, max_depth=10,
        min_samples_split=5, class_weight="balanced",
        random_state=42, n_jobs=-1
    )
    full_rf.fit(X, y)
    full_preds = full_rf.predict(X)

    flagged = flag_anomalies(df, full_preds)
    save_results(best_name, best_metrics, all_metrics, flagged)

    # ── Final Summary ──────────────────────────────────
    print(f"\n{'='*55}")
    print("  Layer 3 Complete ✅")
    print(f"{'='*55}")
    print(f"  Best Model  : {best_name}")
    print(f"  Precision   : {best_metrics['precision']*100:.1f}%")
    print(f"  Recall      : {best_metrics['recall']*100:.1f}%")
    print(f"  F1 Score    : {best_metrics['f1_score']*100:.1f}%")
    print(f"{'='*55}")

    print(f"\n  📄 Supervised Model Comparison (for paper):")
    print(f"  {'Model':<20} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print(f"  {'─'*48}")
    for name, m in all_metrics.items():
        marker = " ⭐" if name == best_name else ""
        print(f"  {name:<20} {m['precision']*100:>9.1f}%"
              f" {m['recall']*100:>7.1f}%"
              f" {m['f1']*100:>7.1f}%{marker}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()