# 🔐 Secure Supply Chain Management Using Smart Contract Auditing and Post-Quantum Blockchain

> A 3-layer Zero Trust Architecture (ZTA) framework integrating AST-based smart contract vulnerability detection, CRYSTALS-Dilithium2 post-quantum signatures (NIST FIPS 204), and supervised ML anomaly detection — achieving ~97% F1 score on a simulated Ethereum supply chain.

---

## 📌 Overview

Traditional blockchain-based supply chains rely on ECDSA/RSA cryptography, which is vulnerable to quantum attacks via Shor's algorithm. This project presents a novel, integrated security framework that addresses this threat while simultaneously auditing smart contract vulnerabilities and detecting anomalous supply chain behavior using machine learning.

The system is structured as a **3-layer Zero Trust Architecture**:

| Layer | Component | Description |
|-------|-----------|-------------|
| Layer 1 | Smart Contract Audit | AST-based vulnerability detection on Ethereum contracts |
| Layer 2 | Supply Chain Simulation | Post-quantum signed transactions across 4 organizations |
| Layer 3 | ML Anomaly Detection | SVM-based detection across 20 behavioral features |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│              Zero Trust Architecture                │
│                                                     │
│  Layer 1: Smart Contract Audit                      │
│  ├── AST-based vulnerability detection              │
│  ├── Sampled Ethereum contract dataset              │
│  └── Approved hashes stored on Ganache blockchain   │
│                                                     │
│  Layer 2: Supply Chain Simulation                   │
│  ├── 4-organization supply chain                    │
│  ├── Dilithium2-signed transactions                 │
│  └── Injected anomalies (4 types)                   │
│                                                     │
│  Layer 3: ML Anomaly Detection                      │
│  ├── 20 behavioral features per transaction         │
│  ├── 4 supervised ML models evaluated               │
│  └── SVM best model — ~97% F1 score                 │
└─────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

- 🔍 **AST-based Smart Contract Auditing** — static vulnerability detection on Solidity contracts
- 🔐 **Post-Quantum Cryptography** — CRYSTALS-Dilithium2 (ML-DSA, NIST FIPS 204) signatures replacing ECDSA
- ⛓️ **Persistent Blockchain Storage** — audited contract hashes stored on Ganache with `--db` persistence
- 🏭 **Supply Chain Simulation** — realistic 4-org transaction flow with injected anomaly scenarios
- 🤖 **Supervised ML Detection** — SVM, Decision Tree, Gradient Boosting, and Random Forest evaluated
- 📊 **~97% F1 Score** — across four anomaly types with 20 extracted behavioral features

---

## 🧪 Anomaly Types Detected

| Anomaly Type | Description |
|---|---|
| `unusual_route` | Transaction path deviates from expected supply chain flow |
| `duplicate_submission` | Same transaction submitted more than once |
| `abnormal_size` | LOC or payload size significantly outside normal range |
| `rapid_resubmission` | Transactions submitted with suspiciously short time gaps (1–3s) |

---

## 📊 ML Model Performance

| Model | F1 Score |
|---|---|
| **SVM** *(best)* | **~97%** |
| Gradient Boosting | High |
| Random Forest | High |
| Decision Tree | Moderate |

> ⚠️ Isolation Forest (unsupervised) was evaluated but excluded from final results due to poor performance (~55% F1).

---

## 🛡️ Why Post-Quantum Cryptography?

- **Shor's Algorithm** can break RSA and ECDSA entirely on a sufficiently powerful quantum computer
- **CRYSTALS-Dilithium2** (ML-DSA) is a NIST FIPS 204 standardized lattice-based signature scheme resistant to quantum attacks
- Grover's algorithm only halves SHA-256 effective bits — hashing remains secure
- This system future-proofs supply chain integrity against the quantum threat

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| Language | Python, Solidity |
| Blockchain | Ethereum, Ganache (local) |
| Smart Contracts | Web3.py, solc |
| Post-Quantum Crypto | CRYSTALS-Dilithium2 via `liboqs` (`oqs`) |
| ML | scikit-learn (SVM, DT, GB, RF) |
| Visualization | matplotlib |
| Compiler | solc |

---

## 📁 Project Structure

```
secure-scm-pqc-blockchain/
│
├── layer1_audit/
│   ├── ast_scanner.py          # AST-based vulnerability detection
│   ├── batch_audit.py          # Batch processing of Ethereum contracts
│   └── store_hashes.py         # Store approved hashes to Ganache
│
├── layer2_simulation/
│   ├── supply_chain_sim.py     # 4-org supply chain transaction simulator
│   └── anomaly_injector.py     # Injects 4 types of anomalies
│
├── layer3_ml/
│   ├── feature_extraction.py   # Extract 20 behavioral features
│   ├── train_models.py         # Train and evaluate all ML models
│   └── visualize_results.py    # matplotlib results visualization
│
├── contracts/
│   └── AuditRegistry.sol       # Solidity smart contract
│
├── utils/
│   └── dilithium_signer.py     # Dilithium2 signing/verification wrapper
│
└── README.md
```

## 🚀 Getting Started

### Prerequisites

```bash
pip install web3 pysolc scikit-learn matplotlib oqs
npm install -g ganache
```

### Run Ganache with Persistence

```bash
ganache --db ./ganache-db --deterministic
```

## 🔖 Keywords

`blockchain` `post-quantum cryptography` `supply chain security` `smart contract auditing` `zero trust architecture` `CRYSTALS-Dilithium2` `ML-DSA` `NIST FIPS 204` `anomaly detection` `SVM` `Ethereum` `Ganache`
