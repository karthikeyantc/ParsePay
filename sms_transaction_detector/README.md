# SMS Transaction Detector

A lightweight local AI tool to classify financial SMS messages and extract transaction details (amount, date, payee).

## 💡 Features

- Classifies whether an SMS is a financial transaction or not
- Extracts amount, date, and payee using regex
- Trained with scikit-learn (very lightweight)

## 🚀 Setup

```bash
pip install -r requirements.txt
python test/test_sms_model.py
```

## 📁 Folder Structure

- `model/` – Contains trained ML model and training script
- `extractor/` – Regex-based transaction extractor
- `test/` – Testing script
- `data/` – For future SMS data samples

## 🛠 Tech Stack

- Python
- scikit-learn
- joblib
