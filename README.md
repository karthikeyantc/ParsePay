# ParsePay

A personal finance app that reads debit/credit SMS messages, extracts transaction details, lets you review and categorize them, and sends them to the Cashew Finance app via deep linking. Built with React Native (Expo) using a TDD approach.

## Project Overview

ParsePay is designed to simplify financial tracking by automatically extracting transaction details from SMS messages. The system uses both rule-based approaches and machine learning models to effectively handle a wide variety of SMS formats from different financial institutions.

## Project Structure

The project has been organized into a clear, modular structure:

```
ParsePay/
├── sms_transaction_detector/    # Main transaction detection package
│   ├── core/                    # Core functionality
│   │   ├── extractor/           # Rule-based extraction logic
│   │   └── utils/               # Utility functions
│   ├── models/                  # ML models for transaction detection
│   │   ├── classifier/          # Basic transaction classifier
│   │   ├── ner/                 # Named Entity Recognition model
│   │   └── training_data/       # Training data for models
│   └── tests/                   # Test suites
│       ├── rule_based/          # Tests for rule-based components
│       └── ml/                  # Tests for ML-based components
│
└── sms-ml/                      # Additional ML components for SMS processing
    ├── data/                    # SMS data for training
    ├── models/                  # Trained models
    ├── notebooks/               # Data analysis notebooks
    └── scripts/                 # Training and evaluation scripts
```

## Current Implementations

### Rule-Based Extraction (sms_transaction_detector/core/extractor)
- Transaction detail extraction using regex patterns
- Support for various SMS formats from different banks
- Extraction of key transaction elements:
  - Transaction amount
  - Date and time
  - Merchant/payee information
  - Account details
  - Transaction type (debit/credit)

### Machine Learning Models

#### Basic Transaction Classifier (sms_transaction_detector/models/classifier)
- Identifies if an SMS message is transaction-related
- Uses scikit-learn for classification
- Trained on labeled SMS data

#### Named Entity Recognition (sms_transaction_detector/models/ner)
- Uses spaCy for entity extraction
- Trained to recognize financial entities in text
- Enhanced model with additional training data for improved performance
- Fallback to rule-based extraction when confidence is low

### Testing Framework
- Comprehensive test suite covering both rule-based and ML approaches
- Test cases for various SMS formats and edge cases
- Performance evaluation metrics for ML models

## Performance Comparison
The project includes performance evaluations comparing the original and enhanced models:
- Original model performance metrics (see original_model_performance.png)
- Enhanced model performance metrics (see enhanced_model_performance.png)
- Significant improvements in entity recognition accuracy

## Getting Started

### Prerequisites
- Python 3.x
- Dependencies listed in requirements.txt

### Installation
```bash
pip install -r sms_transaction_detector/requirements.txt
```

### Usage
Refer to specific module documentation for usage examples.

## Future Development
- Integration with more banking institutions
- Improved categorization of transactions
- Enhanced UI for transaction review
- Direct integration with additional financial apps

## License
This project is licensed under the terms included in the LICENSE file.
