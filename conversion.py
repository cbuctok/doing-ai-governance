import pandas as pd
import json

def expand_range(val):
    """
    Expands a range string into a list of individual control values.
    E.g., "7.1-7.3" -> ["7.1", "7.2", "7.3"]
          "A.7.4.6-A.7.4.8" -> ["A.7.4.6", "A.7.4.7", "A.7.4.8"]
    If no '-' is found, returns a list containing the original value.
    """
    val_str = str(val).strip()
    if '-' not in val_str:
        return [val_str]
    try:
        left, right = val_str.split('-', 1)
        left_parts = left.split('.')
        right_parts = right.split('.')
        # Only expand if all segments except the last are identical.
        if len(left_parts) != len(right_parts) or left_parts[:-1] != right_parts[:-1]:
            return [val_str]
        start = int(left_parts[-1])
        end = int(right_parts[-1])
        return [".".join(left_parts[:-1] + [str(i)]) for i in range(start, end + 1)]
    except Exception:
        return [val_str]

def process_cell(cell):
    """
    Splits a cell by newline characters, then expands ranges for each non-empty part.
    Returns a list of individual control values.
    """
    controls = []
    for part in str(cell).splitlines():
        part = part.strip()
        if part:  # skip empty lines
            controls.extend(expand_range(part))
    return controls

# Read the Excel file (adjust sheet name/path as needed)
df = pd.read_excel("Source Data.xlsx", sheet_name="Mapping")

df.columns = df.columns.str.strip().str.upper()
print(df.columns)

# Define the expected columns.
master_col = "MASTER"
source_cols = ["ISO42001", "ISO27001", "ISO27701", "EU AI ACT", "NIST RMF", "SOC2"]

# Build the lists dictionary while expanding ranges and splitting on newlines.
lists = {}
for col in [master_col] + source_cols:
    control_set = set()
    for val in df[col].dropna():
        controls = process_cell(val)
        control_set.update(controls)
    key = "Master" if col == master_col else col
    lists[key] = sorted(control_set)

# Build relationships by expanding any ranges/newlines in the cells.
relationships = []
for _, row in df.iterrows():
    master_controls = process_cell(row[master_col])
    for col in source_cols:
        if pd.notnull(row[col]):
            source_controls = process_cell(row[col])
            for m in master_controls:
                for s in source_controls:
                    relationships.append(["Master", m, col, s])

# Combine lists and relationships into one JSON structure.
data = {"lists": lists, "relationships": relationships}
with open("control_mapping.json", "w") as f:
    json.dump(data, f, indent=4)

print("Data successfully converted to control_mapping.json")
