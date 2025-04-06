import spacy
import json
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tabulate import tabulate
from colorama import Fore, Style, init
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fallback_rules

# Initialize colorama
init()

def evaluate_model_with_categories(model_path, test_data_by_category):
    """Evaluate model performance by category with more detailed metrics"""
    # Load the model
    try:
        nlp = spacy.load(model_path)
        print(f"Loaded model from {model_path}")
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
    
    # Results structure will be by category and entity type
    results = {}
    
    # Overall stats
    all_stats = {
        "total_entities": defaultdict(int),
        "extracted_ml": defaultdict(int),
        "correct_ml": defaultdict(int),
        "extracted_with_fallback": defaultdict(int),
        "correct_with_fallback": defaultdict(int)
    }
    
    for category_name, test_data in test_data_by_category.items():
        print(f"\nEvaluating category: {category_name}")
        category_results = {
            "total_entities": defaultdict(int),
            "extracted_ml": defaultdict(int),
            "correct_ml": defaultdict(int),
            "extracted_with_fallback": defaultdict(int),
            "correct_with_fallback": defaultdict(int)
        }
        
        for text, annotations in test_data:
            # Get true entities
            true_entities = [(start, end, label) for start, end, label in annotations['entities']]
            true_entities_dict = {(start, end, label): text[start:end] for start, end, label in true_entities}
            
            # Count true entities by type
            for _, _, label in true_entities:
                category_results["total_entities"][label] += 1
                all_stats["total_entities"][label] += 1
            
            # Get ML-only predictions
            doc = nlp(text)
            ml_entities = [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
            ml_entities_dict = {(start, end, label): text[start:end] for start, end, label in ml_entities}
            
            # Count ML extractions by type
            for _, _, label in ml_entities:
                category_results["extracted_ml"][label] += 1
                all_stats["extracted_ml"][label] += 1
            
            # Count correct ML predictions
            for entity in ml_entities:
                if entity in true_entities:
                    category_results["correct_ml"][entity[2]] += 1
                    all_stats["correct_ml"][entity[2]] += 1
            
            # Now apply fallback rules to see what would be caught
            result_dict = {
                "bank": {"value": None, "confidence": 0.0, "source": "none"},
                "amount": {"value": None, "confidence": 0.0, "source": "none"},
                "date": {"value": None, "confidence": 0.0, "source": "none"},
                "payee": {"value": None, "confidence": 0.0, "source": "none"},
                "transaction_type": {"value": None, "confidence": 0.0, "source": "none"},
                "account_from": {"value": None, "confidence": 0.0, "source": "none"},
                "account_to": {"value": None, "confidence": 0.0, "source": "none"}
            }
            
            # Add ML results to the result_dict
            ml_found = set()
            for ent in doc.ents:
                entity_label = ent.label_.lower()
                if entity_label in result_dict:
                    result_dict[entity_label]["value"] = ent.text
                    result_dict[entity_label]["confidence"] = 0.85
                    result_dict[entity_label]["source"] = "ml"
                    ml_found.add(entity_label)
            
            # Apply fallback rules only to fields not found by ML
            fallback_rules.apply_fallback_rules(text, result_dict)
            
            # Create a mapping of entity types between our format and the test data format
            entity_type_mapping = {
                "bank": "BANK",
                "amount": "AMOUNT",
                "date": "DATE",
                "payee": "PAYEE",
                "transaction_type": "TRANSACTION_TYPE",
                "account_from": "ACCOUNT_FROM",
                "account_to": "ACCOUNT_TO"
            }
            
            # Count entities found with fallback rules
            for field, mapping in entity_type_mapping.items():
                if result_dict[field]["value"] is not None and field not in ml_found:
                    # Entity is found by fallback, not ML
                    category_results["extracted_with_fallback"][mapping] += 1
                    all_stats["extracted_with_fallback"][mapping] += 1
                    
                    # Check if it's correct by matching the text
                    fallback_text = result_dict[field]["value"]
                    
                    # Look for a matching true entity based on text overlap
                    # This is more lenient than exact match and better represents real use
                    found_match = False
                    for (start, end, label), true_text in true_entities_dict.items():
                        if label == mapping and (
                            fallback_text in true_text or 
                            true_text in fallback_text or
                            # For dates, allow flexible matching
                            (mapping == "DATE" and any(x in y for x, y in [(fallback_text, true_text), (true_text, fallback_text)]))
                        ):
                            category_results["correct_with_fallback"][mapping] += 1  
                            all_stats["correct_with_fallback"][mapping] += 1
                            found_match = True
                            break
        
        results[category_name] = category_results
    
    results["ALL CATEGORIES"] = all_stats
    return results

def format_metrics_table(results):
    """Create a colorful formatted table of metrics"""
    table_data = []
    headers = ["Entity Type", "ML Only", "With Fallback", "Improvement"]
    
    entity_types = ["BANK", "AMOUNT", "DATE", "PAYEE", "TRANSACTION_TYPE", "ACCOUNT_FROM", "ACCOUNT_TO"]
    all_stats = results["ALL CATEGORIES"]
    
    for entity in entity_types:
        total = all_stats["total_entities"].get(entity, 0)
        if total == 0:
            continue
            
        # ML-only metrics
        ml_extracted = all_stats["extracted_ml"].get(entity, 0)
        ml_correct = all_stats["correct_ml"].get(entity, 0)
        ml_precision = ml_correct / ml_extracted if ml_extracted > 0 else 0
        ml_recall = ml_correct / total if total > 0 else 0
        ml_f1 = 2 * ml_precision * ml_recall / (ml_precision + ml_recall) if (ml_precision + ml_recall) > 0 else 0
        
        # Metrics with fallback
        total_extracted = ml_extracted + all_stats["extracted_with_fallback"].get(entity, 0)
        total_correct = ml_correct + all_stats["correct_with_fallback"].get(entity, 0)
        combined_precision = total_correct / total_extracted if total_extracted > 0 else 0
        combined_recall = total_correct / total if total > 0 else 0
        combined_f1 = 2 * combined_precision * combined_recall / (combined_precision + combined_recall) if (combined_precision + combined_recall) > 0 else 0
        
        # Format with colors
        ml_f1_str = (Fore.RED if ml_f1 < 0.5 else Fore.YELLOW if ml_f1 < 0.75 else Fore.GREEN) + f"{ml_f1:.2f}" + Style.RESET_ALL
        combined_f1_str = (Fore.RED if combined_f1 < 0.5 else Fore.YELLOW if combined_f1 < 0.75 else Fore.GREEN) + f"{combined_f1:.2f}" + Style.RESET_ALL
        
        # Calculate dependency on fallback
        dependency = (total_correct - ml_correct) / total_correct if total_correct > 0 else 0
        dependency_str = (Fore.GREEN if dependency < 0.25 else Fore.YELLOW if dependency < 0.5 else Fore.RED) + f"{dependency:.2%}" + Style.RESET_ALL
        
        table_data.append([
            entity,
            f"F1: {ml_f1_str} (P: {ml_precision:.2f}, R: {ml_recall:.2f})",
            f"F1: {combined_f1_str} (P: {combined_precision:.2f}, R: {combined_recall:.2f})",
            f"Fallback Dependency: {dependency_str}"
        ])
    
    return tabulate(table_data, headers=headers, tablefmt="grid")

def plot_entity_performance(results, output_path="entity_performance.png"):
    """Create a visualization of entity performance with and without fallback rules"""
    entity_types = ["BANK", "AMOUNT", "DATE", "PAYEE", "TRANSACTION_TYPE", "ACCOUNT_FROM", "ACCOUNT_TO"]
    all_stats = results["ALL CATEGORIES"]
    
    ml_f1_scores = []
    combined_f1_scores = []
    dependency_scores = []
    
    for entity in entity_types:
        total = all_stats["total_entities"].get(entity, 0)
        if total == 0:
            ml_f1_scores.append(0)
            combined_f1_scores.append(0)
            dependency_scores.append(0)
            continue
            
        # ML-only metrics
        ml_extracted = all_stats["extracted_ml"].get(entity, 0)
        ml_correct = all_stats["correct_ml"].get(entity, 0)
        ml_precision = ml_correct / ml_extracted if ml_extracted > 0 else 0
        ml_recall = ml_correct / total if total > 0 else 0
        ml_f1 = 2 * ml_precision * ml_recall / (ml_precision + ml_recall) if (ml_precision + ml_recall) > 0 else 0
        
        # Metrics with fallback
        total_extracted = ml_extracted + all_stats["extracted_with_fallback"].get(entity, 0)
        total_correct = ml_correct + all_stats["correct_with_fallback"].get(entity, 0)
        combined_precision = total_correct / total_extracted if total_extracted > 0 else 0
        combined_recall = total_correct / total if total > 0 else 0
        combined_f1 = 2 * combined_precision * combined_recall / (combined_precision + combined_recall) if (combined_precision + combined_recall) > 0 else 0
        
        # Calculate dependency on fallback
        dependency = (total_correct - ml_correct) / total_correct if total_correct > 0 else 0
        
        ml_f1_scores.append(ml_f1)
        combined_f1_scores.append(combined_f1)
        dependency_scores.append(dependency)
    
    # Create the plot
    plt.figure(figsize=(12, 10))
    
    # Plot F1 scores
    plt.subplot(2, 1, 1)
    x = np.arange(len(entity_types))
    width = 0.35
    
    plt.bar(x - width/2, ml_f1_scores, width, label='ML Only F1')
    plt.bar(x + width/2, combined_f1_scores, width, label='With Fallback F1')
    
    plt.ylabel('F1 Score')
    plt.title('Entity Extraction Performance')
    plt.xticks(x, entity_types)
    plt.ylim(0, 1)
    plt.legend()
    
    # Plot dependency on fallback
    plt.subplot(2, 1, 2)
    colors = ['green' if d < 0.25 else 'orange' if d < 0.5 else 'red' for d in dependency_scores]
    
    plt.bar(x, dependency_scores, color=colors)
    plt.axhline(y=0.25, color='green', linestyle='--', alpha=0.7)
    plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.7)
    
    plt.ylabel('Fallback Dependency')
    plt.title('Dependency on Fallback Rules')
    plt.xticks(x, entity_types)
    plt.ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Performance visualization saved to {output_path}")

def create_category_test_data():
    """Create test data organized by categories to match the comprehensive test structure"""
    simple_sms_tests = [
        # Simple SMS tests
        [
            "Sent Rs.73.00 From HDFC Bank A/C x2228 To Marvel On 04/04/25 Ref 509482752071",
            {
                "entities": [
                    [5, 13, "AMOUNT"],
                    [19, 28, "BANK"],
                    [29, 40, "ACCOUNT_FROM"],
                    [44, 50, "PAYEE"],
                    [54, 62, "DATE"],
                    [0, 4, "TRANSACTION_TYPE"]
                ]
            }
        ],
        [
            "Rs.652 spent on HDFC Bank Card x1135 at PAY*Flipkart Internet on 2025-03-25:06:43:19",
            {
                "entities": [
                    [0, 6, "AMOUNT"],
                    [16, 25, "BANK"],
                    [26, 40, "ACCOUNT_FROM"],
                    [44, 64, "PAYEE"],
                    [68, 85, "DATE"],
                    [7, 12, "TRANSACTION_TYPE"]
                ]
            }
        ],
        [
            "Credit Alert! Rs.10.00 credited to HDFC Bank A/c xx2228 on 03-04-25 from VPA one97735@icici",
            {
                "entities": [
                    [14, 22, "AMOUNT"],
                    [35, 44, "BANK"],
                    [45, 56, "ACCOUNT_TO"],
                    [60, 68, "DATE"],
                    [74, 92, "PAYEE"],
                    [23, 31, "TRANSACTION_TYPE"],
                    [0, 13, "TRANSACTION_TYPE"]
                ]
            }
        ]
    ]
    
    complex_sms_tests = [
        [
            "Dear Customer, Your Acct XX5678 is debited with Rs.1,23,456.78 on 05.04.2025 for Flipkart order #FLP87654321 (UPI Ref: 123456789012). Avl Bal: Rs.987654.32",
            {
                "entities": [
                    [24, 34, "ACCOUNT_FROM"],
                    [35, 47, "TRANSACTION_TYPE"],
                    [53, 67, "AMOUNT"],
                    [71, 81, "DATE"],
                    [86, 112, "PAYEE"]
                ]
            }
        ],
        [
            "ALERT: INR 42,599.00 debited from a/c XX3487 on 01-Apr-25 at AMAZON.IN/BILL. Avl bal: INR 15,736.88. Dispute? Call 1800-425-3800 within 7 days.",
            {
                "entities": [
                    [7, 21, "AMOUNT"],
                    [22, 29, "TRANSACTION_TYPE"],
                    [39, 45, "ACCOUNT_FROM"],
                    [49, 58, "DATE"],
                    [62, 75, "PAYEE"]
                ]
            }
        ],
        [
            "SBI: Rs.13750.00 transferred to Mrs. Sharmila J (A/c xxxxxxxx5432) on 04-04-2025 from A/c xxxxxxxx9876 using SBI YONO. Ref # YBT123456789.",
            {
                "entities": [
                    [0, 3, "BANK"],
                    [5, 16, "AMOUNT"],
                    [17, 27, "TRANSACTION_TYPE"],
                    [31, 47, "PAYEE"],
                    [48, 65, "ACCOUNT_TO"],
                    [69, 79, "DATE"],
                    [85, 102, "ACCOUNT_FROM"]
                ]
            }
        ],
        [
            "IDFC FIRST Bank: Your salary of Rs.87,500.00 has been credited to your account XX9876 on 04/04/2025. Subject: APR-25 SALARY. Balance: Rs.1,12,453.28",
            {
                "entities": [
                    [0, 15, "BANK"],
                    [31, 43, "AMOUNT"],
                    [44, 65, "TRANSACTION_TYPE"],
                    [79, 85, "ACCOUNT_TO"],
                    [89, 99, "DATE"]
                ]
            }
        ]
    ]
    
    upi_tests = [
        [
            "UPI transaction successful! Rs.500.00 sent to john.doe@okicici from XX5678 on 05-04-2025.",
            {
                "entities": [
                    [26, 35, "AMOUNT"],
                    [36, 40, "TRANSACTION_TYPE"],
                    [44, 60, "PAYEE"],
                    [66, 72, "ACCOUNT_FROM"],
                    [76, 86, "DATE"]
                ]
            }
        ],
        [
            "Payment of Rs.1,200 to sam.smith@ybl completed via UPI ID Reference: UPI/123456789.",
            {
                "entities": [
                    [11, 20, "AMOUNT"],
                    [24, 37, "PAYEE"],
                    [38, 47, "TRANSACTION_TYPE"],
                    [0, 7, "TRANSACTION_TYPE"]
                ]
            }
        ],
        [
            "SBI Alert: Rs.245.00 debited from account XX1234 to merchant.payment@okaxis via UPI.",
            {
                "entities": [
                    [0, 3, "BANK"],
                    [11, 20, "AMOUNT"],
                    [21, 28, "TRANSACTION_TYPE"],
                    [44, 50, "ACCOUNT_FROM"],
                    [54, 76, "PAYEE"]
                ]
            }
        ],
        [
            "ALERT: Transaction of INR 350.00 to coffee.shop@paytm is successful. UPI Ref: 20250405112233.",
            {
                "entities": [
                    [24, 34, "AMOUNT"],
                    [38, 54, "PAYEE"],
                    [7, 18, "TRANSACTION_TYPE"]
                ]
            }
        ]
    ]
    
    service_payment_tests = [
        [
            "Thank you for paying Rs.1,250.00 towards your Electricity Bill from your ICICI Bank a/c XX5432.",
            {
                "entities": [
                    [21, 32, "AMOUNT"],
                    [41, 57, "PAYEE"],
                    [68, 77, "BANK"],
                    [78, 89, "ACCOUNT_FROM"],
                    [14, 20, "TRANSACTION_TYPE"]
                ]
            }
        ],
        [
            "HDFC Bank: INR 899.00 debited for Mobile Bill Payment to Airtel from XX7654.",
            {
                "entities": [
                    [0, 9, "BANK"],
                    [11, 21, "AMOUNT"],
                    [22, 29, "TRANSACTION_TYPE"],
                    [34, 55, "PAYEE"],
                    [59, 65, "ACCOUNT_FROM"]
                ]
            }
        ],
        [
            "SBI Alert: Rs.450.00 paid for DTH Recharge - Tata Sky from your account XX3456.",
            {
                "entities": [
                    [0, 3, "BANK"],
                    [11, 20, "AMOUNT"],
                    [21, 25, "TRANSACTION_TYPE"],
                    [30, 54, "PAYEE"],
                    [71, 77, "ACCOUNT_FROM"]
                ]
            }
        ],
        [
            "Payment of Rs.2,199.00 towards Broadband Bill - Jio Fiber is complete. Ref: BILL12345.",
            {
                "entities": [
                    [11, 22, "AMOUNT"],
                    [31, 58, "PAYEE"],
                    [0, 7, "TRANSACTION_TYPE"]
                ]
            }
        ]
    ]
    
    # Return a dictionary of test categories
    return {
        "Simple SMS Formats": simple_sms_tests,
        "Complex SMS Formats": complex_sms_tests,
        "UPI Transactions": upi_tests,
        "Service Payments": service_payment_tests
    }

def main():
    print(f"{Fore.CYAN}SMS Transaction Entity Extraction Evaluation{Style.RESET_ALL}\n")
    
    # Create categorized test data matching our comprehensive test
    test_data_by_category = create_category_test_data()
    
    # Evaluate the original model
    print(f"\n{Fore.YELLOW}Evaluating original model...{Style.RESET_ALL}")
    original_model_path = "/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model"
    original_results = evaluate_model_with_categories(original_model_path, test_data_by_category)
    
    if original_results:
        print(f"\n{Fore.GREEN}Original Model Performance by Entity:{Style.RESET_ALL}")
        print(format_metrics_table(original_results))
        plot_entity_performance(original_results, "original_model_performance.png")
    
    # Evaluate the enhanced model
    print(f"\n{Fore.YELLOW}Evaluating enhanced model...{Style.RESET_ALL}")
    enhanced_model_path = "/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model"
    enhanced_results = evaluate_model_with_categories(enhanced_model_path, test_data_by_category)
    
    if enhanced_results:
        print(f"\n{Fore.GREEN}Enhanced Model Performance by Entity:{Style.RESET_ALL}")
        print(format_metrics_table(enhanced_results))
        plot_entity_performance(enhanced_results, "enhanced_model_performance.png")
    
    # Compare before and after for each entity type
    if original_results and enhanced_results:
        print(f"\n{Fore.CYAN}Model Improvement Analysis{Style.RESET_ALL}")
        
        all_entities = ["BANK", "AMOUNT", "DATE", "PAYEE", "TRANSACTION_TYPE", "ACCOUNT_FROM", "ACCOUNT_TO"]
        improvements = []
        
        for entity in all_entities:
            # Calculate ML-only metrics for original model
            orig_stats = original_results["ALL CATEGORIES"]
            orig_total = orig_stats["total_entities"].get(entity, 0)
            if orig_total == 0:
                continue
                
            orig_ml_extracted = orig_stats["extracted_ml"].get(entity, 0) 
            orig_ml_correct = orig_stats["correct_ml"].get(entity, 0)
            orig_ml_precision = orig_ml_correct / orig_ml_extracted if orig_ml_extracted > 0 else 0
            orig_ml_recall = orig_ml_correct / orig_total if orig_total > 0 else 0
            orig_ml_f1 = 2 * orig_ml_precision * orig_ml_recall / (orig_ml_precision + orig_ml_recall) if (orig_ml_precision + orig_ml_recall) > 0 else 0
            
            # Calculate ML-only metrics for enhanced model
            enh_stats = enhanced_results["ALL CATEGORIES"]
            enh_total = enh_stats["total_entities"].get(entity, 0)
            if enh_total == 0:
                continue
                
            enh_ml_extracted = enh_stats["extracted_ml"].get(entity, 0)
            enh_ml_correct = enh_stats["correct_ml"].get(entity, 0)
            enh_ml_precision = enh_ml_correct / enh_ml_extracted if enh_ml_extracted > 0 else 0
            enh_ml_recall = enh_ml_correct / enh_total if enh_total > 0 else 0
            enh_ml_f1 = 2 * enh_ml_precision * enh_ml_recall / (enh_ml_precision + enh_ml_recall) if (enh_ml_precision + enh_ml_recall) > 0 else 0
            
            # Calculate fallback dependency
            orig_total_correct = orig_ml_correct + orig_stats["correct_with_fallback"].get(entity, 0)
            orig_dependency = (orig_total_correct - orig_ml_correct) / orig_total_correct if orig_total_correct > 0 else 0
            
            enh_total_correct = enh_ml_correct + enh_stats["correct_with_fallback"].get(entity, 0) 
            enh_dependency = (enh_total_correct - enh_ml_correct) / enh_total_correct if enh_total_correct > 0 else 0
            
            # Calculate improvements
            f1_improvement = enh_ml_f1 - orig_ml_f1
            dependency_reduction = orig_dependency - enh_dependency
            
            # Color coding
            f1_color = (Fore.GREEN if f1_improvement > 0.1 else 
                        Fore.YELLOW if f1_improvement > 0 else Fore.RED)
            
            dependency_color = (Fore.GREEN if dependency_reduction > 0.1 else
                               Fore.YELLOW if dependency_reduction > 0 else Fore.RED)
            
            improvements.append([
                entity,
                f"ML F1: {orig_ml_f1:.2f} → {enh_ml_f1:.2f} ({f1_color}{f1_improvement:+.2f}{Style.RESET_ALL})",
                f"Fallback Dependency: {orig_dependency:.2%} → {enh_dependency:.2%} ({dependency_color}{dependency_reduction:+.2%}{Style.RESET_ALL})"
            ])
        
        print(tabulate(improvements, 
                      headers=["Entity", "ML Model Improvement", "Fallback Dependency Reduction"],
                      tablefmt="grid"))

if __name__ == "__main__":
    main()