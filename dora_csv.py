import json
import csv
from itertools import combinations

def load_json(filename="control_mapping_dora.json"):
    """
    Load the JSON file containing the control mappings.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return None

def create_mapping_dict(data):
    """
    Create a dictionary mapping standard pairs to their relationships.
    """
    mapping = {}

    # Extract all standard names
    standards = list(data["lists"].keys())

    # Initialize mapping dictionary for all pairs
    for std1, std2 in combinations(standards, 2):
        key = f"{std1}_vs_{std2}"
        mapping[key] = {}

    # Process relationships
    for relationship in data["relationships"]:
        std1, item1, std2, item2 = relationship
        item1 = item1.replace('\xa0', '')
        # Ensure consistent ordering of standards (alphabetical)
        if std1 > std2:
            std1, std2 = std2, std1
            item1, item2 = item2, item1

        key = f"{std1}_vs_{std2}"

        if key not in mapping:
            mapping[key] = {}

        if item1 not in mapping[key]:
            mapping[key][item1] = []

        if item2 not in mapping[key][item1]:
            mapping[key][item1].append(item2)

    return mapping

def export_to_csv(mapping):
    """
    Export each mapping to a separate CSV file.
    """
    for key, items in mapping.items():
        if not items:  # Skip if no mappings exist
            continue

        filename = f"{key}.csv"
        std1, std2 = key.split("_vs_")

        print(f"Creating {filename}...")

        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([std1, std2])  # Header row

            for item1, item2_list in items.items():
                if item2_list:
                    for item2 in item2_list:
                        writer.writerow([item1, item2])
                else:
                    writer.writerow([item1, ""])  # Write unmapped items

def main():
    # Load the JSON data
    data = load_json()
    if not data:
        return

    # Create mapping dictionary
    mapping = create_mapping_dict(data)

    # Export mappings to CSV files
    export_to_csv(mapping)

    print("CSV export complete.")

if __name__ == "__main__":
    main()
