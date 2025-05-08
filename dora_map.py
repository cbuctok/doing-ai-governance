import json
import re
from bs4 import BeautifulSoup

def parse_table(table_string, headers, standard_name):
    soup = BeautifulSoup(table_string, "html.parser")
    table = soup.find("table")

    standard_items = []
    relationships = []
    all_iso27001_controls = set()
    all_iso27002_controls = set()

    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        try:
            standard_item = cells[0].text.strip()

            # Parse ISO 27001 controls with prefix
            iso_27001_controls = []
            # Split by <br> tags and process each part
            for part in cells[1].find_all(string=True, recursive=False):
                for control in re.finditer(
                    r"(Annex A \d+\.\d+|\d+\.\d+(?:\.\d+)?)", part
                ):
                    iso_27001_controls.append(control.group(0))

            # Parse ISO 27002 controls
            iso_27002_controls = []
            # Split by <br> tags and process each part
            for part in cells[2].find_all(string=True, recursive=False):
                iso_27002_controls.extend(re.findall(r"(\d+\.\d+(?:\.\d+)?)", part))

            # Add item to standard list
            standard_items.append(standard_item)

            # Add controls to respective sets
            all_iso27001_controls.update(iso_27001_controls)
            all_iso27002_controls.update(iso_27002_controls)

            # Create relationships
            for control in iso_27001_controls:
                relationships.append(
                    [standard_name, standard_item, "ISO27001", control]
                )

            for control in iso_27002_controls:
                relationships.append(
                    [standard_name, standard_item, "ISO27002", control]
                )

        except IndexError:
            print(f"Error parsing row: {row}")
            print(
                "Make sure the table structure is consistent and has the expected number of cells."
            )

    return (
        standard_items,
        list(all_iso27001_controls),
        list(all_iso27002_controls),
        relationships,
    )

def main():
    table1_string = """
    <figure class="table" style="float:left;"><table style="border-color:hsl(0, 0%, 30%);border-style:solid;"><thead><tr><th style="vertical-align:top;width:400px;">DORA-area&nbsp;<br><br>&nbsp;</th><th style="vertical-align:top;width:150px;">ISO 27001:2022 Controls</th><th style="vertical-align:top;width:150px;">ISO 27002:2022 &nbsp;Controls</th></tr></thead><tbody><tr><td style="vertical-align:top;width:400px;"><strong>Information and Communication Technology (ICT) risk management &nbsp;- Governance </strong>(Article 5)<br>&nbsp;</td><td style="width:150px;">Annex A 5.31<br>Annex A 5.34<br>Annex A 5.35<br>Annex A 5.36<br>Annex A 6.3&nbsp;</td><td style="vertical-align:top;width:150px;">5.1<br>5.31<br>5.34<br>5.35<br>5.36<br>6.3</td></tr><tr><td style="vertical-align:top;width:400px;"><strong>Information and Communication Technology (ICT) risk management &nbsp;- Risk management </strong>(Article 6, 16)</td><td style="vertical-align:top;width:150px;">&nbsp;5.2<br>6.1.2<br>6.1.3<br>8.2<br>8.3<br>Annex A 5.1</td><td style="vertical-align:top;">A 5.2</td></tr><tr><td style="vertical-align:top;"><strong>Information and Communication Technology (ICT) risk management &nbsp;- Identify, Protect, Detect &nbsp;</strong>(Article 7-10)</td><td>Annex A 5.20<br>Annex A 5.24<br>Annex A 5.37<br>Annex A 6.8<br>Annex A 8.8<br>Annex A 8.9<br>Annex A 8.20<br>Annex A 8.21</td><td>5.20<br>5.24<br>5.37<br>6.8<br>8.8<br>8.9<br>8.20<br>8.21</td></tr><tr><td style="vertical-align:top;"><strong>Information and Communication Technology (ICT) risk management &nbsp;- Business continuity </strong>(Article 11, 12)<br><br>&nbsp;</td><td style="vertical-align:top;">Annex A 5.29<br>Annex A 5.30<br>Annex A 8.13<br>Annex A 8.14<br>Annex A 8.15<br>Annex A 8.16</td><td style="vertical-align:top;">5.29<br>5.30<br>8.13<br>8.14<br>8.15<br>8.16</td></tr><tr><td style="vertical-align:top;"><strong>Information and Communication Technology (ICT) risk management &nbsp;- &nbsp;Learning, communication &nbsp;</strong>(Article 13, 14)</td><td style="vertical-align:top;">7.3<br>7.4<br>Annex A 5.15<br>Annex A 5.16<br>Annex A 5.18<br>Annex A 5.24<br>Annex A 6.3<br>Annex A 6.5<br>Annex A 6.8<br>Annex A 8.2<br>Annex A 8.3<br>Annex A 8.5<br>Annex A 8.7<br>Annex A 8.9<br>Annex A 8.13<br>Annex A 8.15<br>Annex A 5.19<br>Annex A 5.22</td><td style="vertical-align:top;">5.15<br>5.16<br>5.18<br>5.24<br>6.3<br>6.5<br>6.8<br>8.2<br>8.3<br>8.5<br>8.7<br>8.9<br>8.13<br>8.15<br>5.19<br>5.22</td></tr><tr><td style="vertical-align:top;"><span style="background-color:rgb(250,247,245);color:rgb(52,77,87);font-family:&quot;Cera Pro&quot;, ui-sans-serif, system-ui, sans-serif, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;, &quot;Segoe UI Symbol&quot;, &quot;Noto Color Emoji&quot;;"><strong>ICT-related incident management, classification and reporting</strong></span><strong> </strong>(Article 17-23)</td><td style="vertical-align:top;">Annex A 5.14<br>Annex A 6.8<br>&nbsp;</td><td style="vertical-align:top;">5.14<br>6.8<br>&nbsp;</td></tr><tr><td><strong>Digital operational resilience testing </strong>(Article 24 - 27)</td><td style="vertical-align:top;">9.1<br>9.2<br>9.3<br>Annex A 5.35<br>Annex A 5.36</td><td style="vertical-align:top;">5.35<br>5.36<br>&nbsp;</td></tr><tr><td style="vertical-align:top;"><span style="background-color:rgba(105,154,173,0.1);color:rgb(52,77,87);font-family:&quot;Cera Pro&quot;, ui-sans-serif, system-ui, sans-serif, &quot;Apple Color Emoji&quot;, &quot;Segoe UI Emoji&quot;, &quot;Segoe UI Symbol&quot;, &quot;Noto Color Emoji&quot;;"><strong>Managing of ICT third-party risk</strong> (Article 28-44)</span><br>&nbsp;</td><td style="vertical-align:top;">Annex A 5.19<br>Annex A 5.20<br>Annex A 5.21<br>Annex A 5.22<br>Annex A 5.23<br>&nbsp;</td><td style="vertical-align:top;">5.19<br>5.20<br>5.21<br>5.22<br>5.23<br>&nbsp;</td></tr></tbody></table></figure>
    """

    table2_string = """
    <figure class="table" style="float:left;"><table><tbody><tr><td style="background-color:hsl(0, 0%, 90%);vertical-align:top;width:400px;"><strong>NIS2-area&nbsp;</strong><br><br><strong>&nbsp;</strong></td><td style="background-color:hsl(0, 0%, 90%);vertical-align:top;width:150px;"><strong>ISO 27001:2022 Controls</strong></td><td style="background-color:hsl(0, 0%, 90%);vertical-align:top;width:150px;"><strong>ISO 27002:2022 &nbsp;Controls</strong></td></tr><tr><td style="vertical-align:top;">Security risk measures (Article 21)<br><strong>I. Human resources security</strong><br><br>&nbsp;</td><td style="vertical-align:top;">Annex A 5.9<br>Annex A 5.10<br>Annex A 5.11<br>Annex A 5.15<br>Annex A 5.16<br>Annex A 5.17<br>Annex A 5.18<br>Annex A 6.1<br>Annex A 6.2<br>Annex A 6.4<br>Annex A 6.5<br>Annex A 6.6</td><td style="vertical-align:top;">5.9<br>5.10<br>5.11<br>5.15<br>5.16<br>5.17<br>5.18<br>6.1<br>6.2<br>6.4<br>6.5<br>6.6</td></tr><tr><td style="vertical-align:top;">Security risk measures (Article 21)<br><strong>J. Use of multi-factor authentication</strong><br>&nbsp;</td><td style="vertical-align:top;">Annex A 5.14<br>Annex A 5.16<br>Annex A 5.17<br>&nbsp;</td><td style="vertical-align:top;">5.14<br>5.16<br>5.17<br>&nbsp;</td></tr><tr><td style="vertical-align:top;"><strong>Use of European cybersecurity certification schemes</strong> (Article 24)</td><td style="vertical-align:top;">Annex A 5.20</td><td style="vertical-align:top;">5.20</td></tr></tbody></table></figure>
    """

    table1_headers = ["DORA-area", "ISO 27001:2022 Controls", "ISO 27002:2022 Controls"]
    table2_headers = ["NIS2-area", "ISO 27001:2022 Controls", "ISO 27002:2022 Controls"]

    dora_items, dora_iso27001, dora_iso27002, dora_relationships = parse_table(
        table1_string, table1_headers, "DORA"
    )
    nis2_items, nis2_iso27001, nis2_iso27002, nis2_relationships = parse_table(
        table2_string, table2_headers, "NIS2"
    )

    # Combine all controls and relationships
    all_iso27001_controls = list(set(dora_iso27001 + nis2_iso27001))
    all_iso27002_controls = list(set(dora_iso27002 + nis2_iso27002))
    all_relationships = dora_relationships + nis2_relationships

    # Create final JSON structure
    result = {
        "lists": {
            "DORA": dora_items,
            "NIS2": nis2_items,
            "ISO27001": all_iso27001_controls,
            "ISO27002": all_iso27002_controls,
        },
        "relationships": all_relationships,
    }

    json_output = json.dumps(result, indent=2)
    print(json_output)

if __name__ == "__main__":
    main()
