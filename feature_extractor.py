import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter

# CONFIGURATION
TRANSACTIONS_FILE = "transactions.json"
FEATURES_FILE     = "features.csv"


# EXTRACT FEATURES
def extract_features(transactions: list) -> pd.DataFrame:

    # Global stats for z-scores
    all_locs   = [tx.get("loc", 0) for tx in transactions]
    all_sizes  = [tx.get("sizeBytes", 0) for tx in transactions]
    mean_loc   = np.mean(all_locs)
    std_loc    = np.std(all_locs) + 1
    mean_size  = np.mean(all_sizes)
    std_size   = np.std(all_sizes) + 1

    # Parse timestamps
    timestamps = []
    for tx in transactions:
        try:
            timestamps.append(datetime.fromisoformat(tx["timestamp"]))
        except Exception:
            timestamps.append(None)

    records = []

    for i, tx in enumerate(transactions):

        # ── Time features ──────────────────────────────
        ts           = timestamps[i]
        hour_of_day  = ts.hour if ts else 0
        day_of_week  = ts.weekday() if ts else 0

        if i > 0 and timestamps[i] and timestamps[i-1]:
            time_gap_seconds = abs((ts - timestamps[i-1]).total_seconds())
        else:
            time_gap_seconds = 3600

        # ── Route features ─────────────────────────────
        route           = tx.get("route", [])
        route_length    = len(route)
        route_is_normal = 1 if route_length == 3 else 0
        has_verifier    = 1 if "Verifier_Org" in route else 0
        has_deployer    = 1 if "Deployer_Org" in route else 0

        # ── Contract size features ─────────────────────
        loc        = tx.get("loc", 0)
        size_bytes = tx.get("sizeBytes", 0)
        loc_zscore  = (loc - mean_loc) / std_loc
        size_zscore = (size_bytes - mean_size) / std_size

        # ── Duplicate features ─────────────────────────
        # Read directly from payload — simulator sets hashFreq=5 for duplicates
        hash_freq    = tx.get("hashFreq", 1)
        is_duplicate = 1 if hash_freq > 1 else 0

        # ── Hash entropy ───────────────────────────────
        contract_hash = tx.get("contractHash", "")
        hash_entropy  = len(set(contract_hash)) / max(len(contract_hash), 1)

        # ── Org encoding ───────────────────────────────
        org_map = {
            "Auditor_Org" : 0, "Deployer_Org": 1,
            "Verifier_Org": 2, "Monitor_Org" : 3
        }
        from_org_enc = org_map.get(tx.get("fromOrg", ""), -1)
        to_org_enc   = org_map.get(tx.get("toOrg", ""), -1)

        # ── Signature length ───────────────────────────
        tx_sig     = tx.get("txSignature", "")
        sig_length = len(bytes.fromhex(tx_sig)) if tx_sig else 0

        on_chain   = 1 if tx.get("onChain", False) else 0

        # ── Ground truth ───────────────────────────────
        is_anomaly   = 1 if tx.get("isAnomaly", False) else 0
        anomaly_type = tx.get("anomalyType", "none") or "none"

        records.append({
            "shipmentId"     : tx.get("shipmentId"),
            "contractHash"   : contract_hash,
            "loc"            : loc,
            "sizeBytes"      : size_bytes,
            "locZscore"      : round(loc_zscore, 4),
            "sizeZscore"     : round(size_zscore, 4),
            "hashEntropy"    : round(hash_entropy, 4),
            "hashFreq"       : hash_freq,
            "isDuplicate"    : is_duplicate,
            "routeLength"    : route_length,
            "routeIsNormal"  : route_is_normal,
            "hasVerifier"    : has_verifier,
            "hasDeployer"    : has_deployer,
            "fromOrg"        : from_org_enc,
            "toOrg"          : to_org_enc,
            "hourOfDay"      : hour_of_day,
            "dayOfWeek"      : day_of_week,
            "timeGapSeconds" : round(time_gap_seconds, 2),
            "sigLength"      : sig_length,
            "onChain"        : on_chain,
            "isAnomaly"      : is_anomaly,
            "anomalyType"    : anomaly_type
        })

    return pd.DataFrame(records)


# STATS
def print_feature_stats(df: pd.DataFrame):
    print(f"\n{'='*55}")
    print("  Feature Statistics")
    print(f"{'='*55}")
    print(f"  {'Feature':<20} {'Min':>8} {'Max':>10} {'Mean':>10}")
    print(f"  {'─'*50}")
    for col in ["loc", "sizeBytes", "locZscore", "sizeZscore",
                "hashFreq", "routeLength", "timeGapSeconds"]:
        print(f"  {col:<20} {df[col].min():>8.1f} "
              f"{df[col].max():>10.1f} {df[col].mean():>10.1f}")
    print(f"\n  Total    : {len(df)}")
    print(f"  Normal   : {(df['isAnomaly']==0).sum()}")
    print(f"  Anomalies: {(df['isAnomaly']==1).sum()} "
          f"({df['isAnomaly'].mean()*100:.1f}%)")
    print(f"\n  Anomaly Types:")
    for atype, count in df[df['isAnomaly']==1]['anomalyType'].value_counts().items():
        print(f"    {atype:<30}: {count}")
    print(f"{'='*55}")


# MAIN
def main():
    print("\n" + "=" * 55)
    print("  Feature Extractor — Supply Chain Transactions")
    print("=" * 55)

    print(f"\n📂 Loading {TRANSACTIONS_FILE}...")
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
        print(f"✅ Loaded {len(transactions)} transactions")
    except FileNotFoundError:
        print(f"❌ {TRANSACTIONS_FILE} not found.")
        return None

    print("\n⚙️  Extracting features...")
    df = extract_features(transactions)
    print(f"✅ Extracted {len(df.columns)-2} features per transaction")

    print_feature_stats(df)

    df.to_csv(FEATURES_FILE, index=False)
    print(f"\n✅ Saved to : {FEATURES_FILE}")
    print(f"   Shape    : {df.shape[0]} rows × {df.shape[1]} columns\n")

    return df


if __name__ == "__main__":
    main()