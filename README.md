
# Governance Mega-Map Application

## Overview

The Governance MegaMap Application is a tool for visualising relationships between governance controls from multiple sources. The application takes mapping data from an Excel file and converts it into a JSON file that is then used to generate an interactive chord diagram. This diagram visually represents the relationships between a master control set and various source control sets (e.g., ISO42001, ISO27001, ISO27701, EU AI ACT, NIST RMF, SOC2).

Additional details and extended discussion on the methodology are available at [ethos-ai.org](https://ethos-ai.org).

## Repository Structure

- **Source Data.xlsx**:  
  The Excel file containing the source mapping data. (The relevant data is on the "Mapping" sheet.)

- **conversion.py**:  
  A script that reads the "Mapping" sheet from the Excel file, expands any control ranges (e.g., "7.1-7.3"), processes newline-separated values, and converts the data into a JSON file (`control_mapping.json`).

- **control_mapping.json**:  
  The output JSON file containing processed control lists and relationships. This file is used as input by the visualization application.

- **governance_map.py**:  
  The main application that loads `control_mapping.json` and displays an interactive chord diagram. The diagram groups nodes by source, orders them naturally, and provides interactive controls:
  - **Click on a node** to toggle its incident edges.
  - **Press 'c'** to clear (hide) all edges.
  - **Press 'r'** to restore edges.
  - **Press 's'** to save the current diagram (prompting for a filename with a `.svg` or `.png` extension).

- **Generated Images Folder**:  
  (Optional) A folder where exported chord diagram images are saved.

## Setup Instructions

### Setting Up the Virtual Environment

1. **Create a Virtual Environment:**

   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment:**

   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies:**

   Install the required packages:
   ```bash
   pip install pandas matplotlib networkx openpyxl
   ```
   
   *(Alternatively, if a `requirements.txt` is provided, run: `pip install -r requirements.txt`)*

## Running the Application

### 1. Running the Conversion Script

The `conversion.py` script processes the source data:
- It reads the "Mapping" sheet from **Source Data.xlsx**.
- It expands control ranges (e.g., "7.1-7.3") and processes newline-separated entries.
- It outputs a JSON file named **control_mapping.json**.

To run the conversion script, execute:
```bash
python conversion.py
```
Make sure that **Source Data.xlsx** is in the same directory as the script.

### 2. Running the Governance Map Application

The `governance_map.py` script creates an interactive chord diagram:
- It loads the **control_mapping.json** file.
- It groups nodes by source (with "Master" nodes arranged along a fixed 90° arc on the left and other nodes sharing the remaining 250° of the circle with a 5° gap between groups).
- Nodes within each group are sorted in natural (dotted numeric) order.
- You can interact with the diagram (toggle edges, clear/restore, and save the diagram).

To run the governance map application, execute:
```bash
python governance_map.py
```

## Usage and Customization

- **Tailoring the Output**:  
  You can adjust parameters such as group gaps, arc ranges, node colors, and label offsets by modifying the corresponding values in the source code.

- **Interactive Controls**:  
  - **Click a node**: Toggle visibility of its connecting edges.
  - **Press 'c'**: Clear (hide) all edges.
  - **Press 'r'**: Restore all edges.
  - **Press 's'**: Save the current diagram. When you press 's', you’ll be prompted for a file name (e.g., `diagram.svg` or `diagram.png`). The diagram is then saved using that name.

## License

This project is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

