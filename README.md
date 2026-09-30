# CyberClaw — AI-Assisted Ransomware Detection

A Flask web app that classifies Windows executables as benign or malicious by extracting structural features from their PE (Portable Executable) headers and running them through a trained XGBoost model — not by watching file-system activity in real time.

Live demo: [ransomeware-detection-tool.onrender.com](https://ransomeware-detection-tool.onrender.com/login)
**Demo login:** `admin` / `password` (this app has no real user accounts — see [Security notes](#security-notes))

> Free-tier hosting: the instance spins down after inactivity, so the first request after a while can take up to ~50 seconds to respond.

---

## What this is

Upload a `.exe`, and the app parses its PE header with [`pefile`](https://github.com/erocarrera/pefile), extracts fifteen structural features (section counts, linker version, debug/export table info, and similar low-level metadata), and passes them to a classifier trained on a labeled dataset of benign and malicious executables. It returns a verdict through both a browser dashboard and a JSON API.

This is a portfolio/learning project built to practice applied ML, Flask deployment, and — as it turned out — real production debugging. It is **not** a production security tool.

## What this doesn't do

Being upfront about this matters more than the detection itself:

- **It doesn't monitor anything in real time.** There's no file-system watcher, no live process monitoring. It classifies one uploaded file at a time, on demand.
- **`BitcoinAddresses` is a placeholder, not a real feature.** `feature_extractor.py` hardcodes this value to `0` for every file — actual bitcoin-address detection (e.g. via a YARA rule or regex scan) was never implemented, so this is effectively a dead feature in the current build.
- **Accuracy is measured on the training distribution only.** The ~99.6% figure below comes from cross-validation on the training dataset — it says nothing about how the model performs against obfuscated, packed, or genuinely novel malware it's never seen a relative of. No held-out, independently sourced test set has been used.
- **No input validation on file type or size.** Uploading a non-PE file causes `pefile` to raise inside a caught exception, which silently returns an all-zero feature vector rather than rejecting the upload outright — meaning a bad file gets a prediction anyway instead of a clear error.
- **The login is a fixed demo credential, not real authentication.** There's no user database, no password hashing, no account system — `admin`/`password` is intentionally public so anyone can try the live demo. Don't extend this auth pattern to anything handling real accounts.
- **The dataset's feature schema is a well-established public pattern, not something collected from scratch for this project** — this exact set of PE-header fields (debug size/RVA, linker versions, section count, DLL characteristics, bitcoin-address flag, etc.) matches long-standing public research and tooling on PE-header-based ransomware detection. What's original here is the model training, the Flask deployment, the API.

## Architecture

```
Upload (.exe)
     │
     ▼
feature_extractor.py  ──  pefile.PE(file) → 15 structural features
     │
     ▼
server.py  ──  builds a labeled feature DataFrame → model.predict()
     │
     ├──  /predict       → session-based result → home.html dashboard
     └──  /api/predict   → JSON response
     │
     ▼
model1.pkl  (trained XGBoost classifier)
features.pkl (ordered list of the 15 feature names, used to label input correctly)
```

## Features extracted

| Feature | What it captures |
|---|---|
| `Machine` | Target CPU architecture code from the file header |
| `DebugSize` / `DebugRVA` | Size and address of the debug directory, if present |
| `MajorImageVersion` / `MajorOSVersion` | Declared image/OS version fields — often unusual in packed or hand-crafted binaries |
| `ExportRVA` / `ExportSize` | Location and size of the export table |
| `IatVRA` | Address of the import address table |
| `MajorLinkerVersion` / `MinorLinkerVersion` | Compiler/linker version that built the binary |
| `NumberOfSections` | Section count — packers often produce atypical counts |
| `SizeOfStackReserve` | Reserved stack size from the optional header |
| `DllCharacteristics` | DLL characteristic flags (e.g. ASLR/DEP-related bits) |
| `ResourceSize` | Size of the resource directory |
| `BitcoinAddresses` | **Not implemented** — hardcoded to `0` (see limitations above) |

## Results

Cross-validated accuracy (`RepeatedStratifiedKFold`, 10 splits × 3 repeats) on the training dataset, across different tree counts:

| Trees | Accuracy |
|---|---|
| 10 | 0.993 (±0.001) |
| 50 | 0.996 (±0.001) |
| 100 | 0.996 (±0.001) |
| 250 | 0.997 (±0.001) |

Precision, recall, and F1 were also computed during training and saved as plots (`model_performance_metrics.png`, `confusion_matrix.png`) rather than logged as numbers — worth pulling the exact figures from those if you want them stated here. These are cross-validation numbers on the training distribution — see limitations above for what they don't tell you.

## Tech stack

- **Backend:** Python, Flask, `pefile`, `pandas`, `joblib`
- **Model:** XGBoost (`XGBClassifier`), trained via scikit-learn's `train_test_split` / `RepeatedStratifiedKFold`
- **Frontend:** Bootstrap 5, Jinja2 templates
- **Hosting:** Render (free tier)

## Setup

```bash
git clone https://github.com/Hacker0306/Ransomware-Detection-Tool.git
cd Ransomware-Detection-Tool
pip install -r requirements.txt
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
python server/server.py
```
Then open `http://localhost:5000` and log in with the demo credentials above.

## API

```bash
curl -X POST -F "file=@/path/to/file.exe" https://ransomeware-detection-tool.onrender.com/api/predict
```
Returns:
```json
{
  "value": 1,
  "output": "Not Detected",
  "message": "✅ File is safe. No ransomware detected."
}
```
`value` is the raw model output — `1` = benign, `0` = malicious, per the training labels.

## Security notes

- The Flask session secret is loaded from an environment variable (`SECRET_KEY`), not hardcoded — it was hardcoded and committed to this public repo earlier in development; that value has been rotated and is no longer in use.
- Authentication is a single hardcoded demo credential, intentionally public for demo purposes — this is not a pattern to reuse for anything handling real user data.
- Uploaded files are removed from the server before/after use but there's currently no restriction on file type or size at the upload layer itself.

## What I'd improve next

- Implement real Bitcoin-address detection instead of the hardcoded placeholder.
- Add file-type and size validation on upload, with a clear rejection message instead of a silent zero-vector fallback.
- Validate the model against an independently sourced test set, not just cross-validation on the training data.
- Replace the demo login with real authentication if this ever needs to handle actual users.
- Add automated tests — the two bugs above would both have been caught immediately by a single test asserting that two different input files produce different feature vectors.

## Author

Siddharth Yadav — Security Researcher | Bug Bounty Hunter on HackerOne & Bugcrowd
[LinkedIn](https://linkedin.com/in/siddharth-yadav2714) · [GitHub](https://github.com/Hacker0306)
