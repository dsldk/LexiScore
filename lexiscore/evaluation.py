"""Evaluation of the Lexiscore algorithm"""
import csv
import os
import requests
from lexiscore import CONFIG

# Load CSS file with evaluation data
with open(os.path.join(CONFIG.get("general", "data_dir"), "evaluation_data.csv")) as f:
    reader = csv.reader(f, delimiter=";")
    data = list(reader)[0:]  # No header row

# Send requests to FastAPI webservice and compare with expected output
tp = 0  # True positives
fp = 0  # False positives
fn = 0  # False negatives
tn = 0  # True negatives

false_positives = []
false_negatives = []

for query, expected_output in data:
    params = {}
    response = requests.get(f"http://localhost:8000/lang/{query}", params=params)
    if response.status_code == 200:
        result = response.json()
        actual_output = result and result[0][0] or ""
    else:
        actual_output = ""
    print(actual_output)

    if actual_output:
        if actual_output == expected_output:
            tp += 1
        else:
            fp += 1
            false_positives.append((query, expected_output, actual_output))
    else:
        if actual_output == expected_output:
            tn += 1
        else:
            fn += 1
            false_negatives.append((query, expected_output, actual_output))

# Calculate precision and recall
precision = tp / (tp + fp)
recall = tp / (tp + fn)

# Print results
print("False positives:")
for query, expected_output, actual_output in false_positives:
    #    if not expected_output:
    #        continue
    print(
        f"Query: {query}, Expected output: {expected_output}, Actual output: {actual_output}"
    )
print("False negatives:")
for query, expected_output, actual_output in false_negatives:
    print(
        f"Query: {query}, Expected output: {expected_output}, Actual output: {actual_output}"
    )

print(f"True positives: {tp}")
print(f"True negatives: {tn}")
print(f"Total: {tp + tn + fp + fn}")
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
