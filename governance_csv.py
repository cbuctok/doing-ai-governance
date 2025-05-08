import json
import csv
from itertools import combinations

def load_data(json_file="control_mapping.json"):
    """
    Loads the JSON file with structure:
      {
        "lists": {
            "Master": [...],
            "ISO42001": [...],
            "ISO27001": [...],
            "ISO27701": [...],
            "EU AI ACT": [...],
            "NIST RMF": [...],
            "SOC2": [...]
        },
        "relationships": [
            ["Master", "GL-1", "ISO42001", "4.1"],
            ...
        ]
      }
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data['lists'], data['relationships']
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error: Could not load or parse data from {json_file}.  Error Details: {e}")
        return {}, [] # Return empty dicts to avoid errors later

def export_to_csv(primary_list_name, secondary_list_name, mapping, lists):
    """
    Exports the relationship between two lists to a CSV file.

    Args:
        primary_list_name (str): The name of the primary list.
        secondary_list_name (str): The name of the secondary list.
        mapping (dict): A dictionary representing the mapping between the two lists.
        lists (dict):  The dictionary containing all the lists.
    """
    filename = f"{primary_list_name}_vs_{secondary_list_name}.csv"
    print(f"Exporting to {filename}")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([primary_list_name, secondary_list_name])  # Write header row
            for primary_item, secondary_items in mapping.items():
                if secondary_items:
                    for secondary_item in secondary_items:
                        writer.writerow([primary_item, secondary_item])
                else:
                    writer.writerow([primary_item, ""]) #handles empty relationships
    except Exception as e:
        print(f"Error exporting to CSV: {e}")

def main():
    """
    Main function to load data and export list combinations to CSV files.
    """
    lists, relationships = load_data()
    if not lists:
        print("No data loaded. Exiting.")
        return

    # Build mappings
    master_to_others = {}  # {master_item: {list_name: set(list_items)}}
    others_to_master = {}  # {list_name: {list_item: set(master_items)}}
    
    for relationship in relationships:
        l1, item1, l2, item2 = relationship
        if l1 == "Master":
            # Map Master items to other list items
            if item1 not in master_to_others:
                master_to_others[item1] = {}
            if l2 not in master_to_others[item1]:
                master_to_others[item1][l2] = set()
            master_to_others[item1][l2].add(item2)
            
            # Reverse mapping: other list items to Master items
            if l2 not in others_to_master:
                others_to_master[l2] = {}
            if item2 not in others_to_master[l2]:
                others_to_master[l2][item2] = set()
            others_to_master[l2][item2].add(item1)
    
    list_names = list(lists.keys())
    for primary_list_name, secondary_list_name in combinations(list_names, 2):
        mapping = {}
        primary_list_items = lists[primary_list_name]
        
        # Initialize mapping with items from the primary list
        for item in primary_list_items:
            mapping[item] = set()
        
        # Build the mapping based on list types
        if primary_list_name == "Master":
            # Master to other mapping (direct)
            for master_item in primary_list_items:
                if master_item in master_to_others and secondary_list_name in master_to_others[master_item]:
                    mapping[master_item].update(master_to_others[master_item][secondary_list_name])
        elif secondary_list_name == "Master":
            # Other to Master mapping (direct)
            for primary_item in primary_list_items:
                if primary_list_name in others_to_master and primary_item in others_to_master[primary_list_name]:
                    mapping[primary_item].update(others_to_master[primary_list_name][primary_item])
        else:
            # Non-Master to non-Master mapping (via Master)
            for primary_item in primary_list_items:
                if primary_list_name in others_to_master and primary_item in others_to_master[primary_list_name]:
                    # Find all Master items linked to this primary item
                    master_items = others_to_master[primary_list_name][primary_item]
                    # For each Master item, find all secondary items linked to it
                    for master_item in master_items:
                        if master_item in master_to_others and secondary_list_name in master_to_others[master_item]:
                            mapping[primary_item].update(master_to_others[master_item][secondary_list_name])
        
        export_to_csv(primary_list_name, secondary_list_name, mapping, lists)

if __name__ == "__main__":
    main()
