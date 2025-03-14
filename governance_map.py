import matplotlib.pyplot as plt
import networkx as nx
import math
import json
from matplotlib.patches import FancyArrowPatch, Circle

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
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data['lists'], data['relationships']

# ----------------------------------------------------------------
# 1. Load the data
# ----------------------------------------------------------------
lists, relationships = load_data()

# ----------------------------------------------------------------
# 2. Define a color lookup (customise as desired)
# ----------------------------------------------------------------
color_lookup = {
    "Master": "grey",
    "ISO42001": "blue",
    "ISO27001": "green",
    "ISO27701": "red",
    "EU AI ACT": "purple",
    "NIST RMF": "orange",
    "SOC2": "cyan"
}

# ----------------------------------------------------------------
# 3. Relationship Table Function
# ----------------------------------------------------------------
def show_relationship_table():
    """
    Prompts for primary and secondary lists and prints a table of their relationships.
    """
    print("\nAvailable list labels:")
    for label in lists.keys():
        print("  " + label)
    print()
    primary = input("Enter primary list label: ").strip()
    secondary = input("Enter secondary list label: ").strip()
    if primary not in lists or secondary not in lists:
        print("Invalid list label(s). Please try again.")
        return
    if primary == secondary:
        print("Primary and secondary lists must be different.")
        return

    mapping = {item: set() for item in lists[primary]}
    for (l1, item1, l2, item2) in relationships:
        if {l1, l2} == {primary, secondary}:
            if l1 == primary:
                mapping[item1].add(item2)
            else:
                mapping[item2].add(item1)

    print(f"\nRelationships between {primary} (primary) and {secondary} (associated):")
    print(f"{primary:<20} | {secondary}")
    print("-" * 60)
    for item in lists[primary]:
        associated = ", ".join(sorted(mapping[item])) if mapping[item] else "-"
        print(f"{item:<20} | {associated}")
    print()

# ----------------------------------------------------------------
# 4. Helper function to parse dotted strings naturally.
# ----------------------------------------------------------------
def parse_dotted(s):
    """
    Splits s on '.' and returns a list of tuples (tag, value) where:
      - tag 0 means the segment is an integer,
      - tag 1 means the segment is a string.
    e.g. "4.1" -> [(0, 4), (0, 1)]
         "27.4" -> [(0, 27), (0, 4)]
         "A.7.4.6" -> [(1, "A"), (0, 7), (0, 4), (0, 6)]
    """
    parts = s.split(".")
    out = []
    for p in parts:
        try:
            num = int(p)
            out.append((0, num))
        except ValueError:
            out.append((1, p))
    return out

# ----------------------------------------------------------------
# 5. Chord Diagram Function with grouped layout and interactive save.
# ----------------------------------------------------------------
def show_chord_diagram():
    """
    Prompts for list labels (comma separated) or press Enter for ALL.
    Displays an interactive chord diagram:
      • "Master" nodes are arranged along a fixed 90° arc on the left (from 135° to 225°).
      • Non‑Master nodes are arranged along the remaining 250° of the circle,
        with a 5° gap on each side between the Master arc and the others.
      • Nodes within each group are sorted in natural (dotted numeric) order.
      • Edge colors are determined as follows:
            - If one node is from Master and the other is not, use the non‑Master node’s color.
            - Otherwise, use the color of the node with the larger x-coordinate.
      • Node labels are offset radially (no extra vertical offset).
      • Press 'c' to clear edges, 'r' to restore edges.
      • Press 's' to save the current diagram: you will be prompted for a file name.
    """
    print("\nAvailable list labels:")
    for label in lists.keys():
        print("  " + label)
    print()
    selected_input = input("Enter list labels to include (comma separated) or press Enter for ALL: ").strip()
    if not selected_input:
        selected_sources = list(lists.keys())
    else:
        selected_sources = [x.strip() for x in selected_input.split(",") if x.strip()]
    for s in selected_sources:
        if s not in lists:
            print(f"Invalid list label: {s}")
            return

    # Build graph: nodes are "Source: Item"
    G = nx.Graph()
    node_to_data = {}
    for source in selected_sources:
        for item in lists[source]:
            node_id = f"{source}: {item}"
            G.add_node(node_id)
            node_to_data[node_id] = (source, item)
    for (l1, item1, l2, item2) in relationships:
        if l1 in selected_sources and l2 in selected_sources:
            n1 = f"{l1}: {item1}"
            n2 = f"{l2}: {item2}"
            if n1 in G and n2 in G:
                G.add_edge(n1, n2)
    if G.number_of_edges() == 0:
        print("No relationships found among the selected lists.")
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')

    # Group nodes by their source.
    groups = {}
    for node in G.nodes():
        source = node_to_data[node][0]
        groups.setdefault(source, []).append(node)
    
    # Order groups by the order in selected_sources.
    ordered_sources = [s for s in selected_sources if s in groups]

    pos = {}
    gap_deg = 5  # Reduced gap between groups (5 degrees)
    # If "Master" is one of the groups, assign it a fixed 90° arc from 135° to 225°.
    if "Master" in ordered_sources:
        master_nodes = sorted(groups["Master"], key=lambda n: parse_dotted(n.split(": ", 1)[1]))
        nM = len(master_nodes)
        master_start = math.radians(135)
        master_end = math.radians(225)
        if nM > 1:
            angles_master = [master_start + i*((master_end - master_start)/(nM - 1)) for i in range(nM)]
        else:
            angles_master = [math.radians(180)]
        for i, node in enumerate(master_nodes):
            pos[node] = (math.cos(angles_master[i]), math.sin(angles_master[i]))
    
    # Non-master groups: remaining sources.
    non_master_sources = [s for s in ordered_sources if s != "Master"]
    # Total available angle for non-master nodes: 250° (leaving a 5° gap on each side).
    total_non_master_deg = 250
    total_non_master_rad = math.radians(total_non_master_deg)
    gap_rad = math.radians(gap_deg)
    nGroups = len(non_master_sources)
    if nGroups > 0:
        total_gap = (nGroups - 1) * gap_rad
        angle_per_group = (total_non_master_rad - total_gap) / nGroups
        # The non-master arc starts at 225°+5°
        current_start = math.radians(225 + gap_deg)
        for source in non_master_sources:
            nodes = sorted(groups[source], key=lambda n: parse_dotted(n.split(": ", 1)[1]))
            nNodes = len(nodes)
            group_start = current_start
            group_end = current_start + angle_per_group
            if nNodes > 1:
                angles = [group_start + i*((group_end - group_start)/(nNodes - 1)) for i in range(nNodes)]
            else:
                angles = [(group_start + group_end) / 2]
            for i, node in enumerate(nodes):
                a = angles[i] % (2 * math.pi)
                pos[node] = (math.cos(a), math.sin(a))
            current_start += angle_per_group + gap_rad

    # Precompute node angles (for edge drawing)
    node_angles = {}
    for node in G.nodes():
        x, y = pos[node]
        node_angles[node] = math.atan2(y, x)

    # Draw nodes & labels (without extra vertical offset)
    node_artists = {}
    for node, (x, y) in pos.items():
        source = node_to_data[node][0]
        col = color_lookup.get(source, "gray")
        circle = Circle((x, y), 0.015, color=col, zorder=3, picker=True)
        ax.add_patch(circle)
        node_artists[node] = circle

        r = math.sqrt(x**2 + y**2)
        offset_r = 0.05
        x_label = x + offset_r * (x / r)
        y_label = y + offset_r * (y / r)
        ha = 'left' if x >= 0 else 'right'
        item_label = node.split(": ", 1)[1]
        ax.text(x_label, y_label, item_label, fontsize=8, ha=ha, va='center', zorder=4)

    # Define edge color logic:
    # If one node is from Master and the other is not, use the non-master node's color.
    # Otherwise, use the color of the node with the larger x-coordinate.
    def get_edge_color(u, v):
        source_u = node_to_data[u][0]
        source_v = node_to_data[v][0]
        if source_u == "Master" and source_v != "Master":
            return color_lookup.get(source_v, "gray")
        elif source_v == "Master" and source_u != "Master":
            return color_lookup.get(source_u, "gray")
        else:
            if pos[u][0] >= pos[v][0]:
                return color_lookup.get(source_u, "gray")
            else:
                return color_lookup.get(source_v, "gray")

    # Draw edges as curved arcs.
    edge_artists = {}
    node_to_edges = {node: [] for node in G.nodes()}
    arc_radius = 0.2
    for u, v in G.edges():
        edge_color = get_edge_color(u, v)
        angle_u = node_angles[u]
        angle_v = node_angles[v]
        delta = angle_v - angle_u
        if delta > math.pi:
            delta -= 2 * math.pi
        elif delta < -math.pi:
            delta += 2 * math.pi
        sign = -1 if abs(delta) > math.pi / 2 else 1
        conn_style = f"arc3,rad={sign * arc_radius}"
        edge_patch = FancyArrowPatch(pos[u], pos[v],
                                     connectionstyle=conn_style,
                                     arrowstyle='-',
                                     color=edge_color,
                                     linewidth=1.5,
                                     alpha=0.7,
                                     zorder=1)
        ax.add_patch(edge_patch)
        edge_artists[frozenset([u, v])] = edge_patch
        node_to_edges[u].append(edge_patch)
        node_to_edges[v].append(edge_patch)

    # Interactivity: clicking on a node toggles its incident edges.
    def on_pick(event):
        for node, patch in node_artists.items():
            if event.artist == patch:
                for e in node_to_edges[node]:
                    e.set_visible(not e.get_visible())
                fig.canvas.draw()
                break

    fig.canvas.mpl_connect('pick_event', on_pick)

    # Key press: 'c' clears edges, 'r' restores them.
    # Also, pressing 's' will prompt to save the diagram.
    def on_key_press(event):
        if event.key == 'c':
            for e in edge_artists.values():
                e.set_visible(False)
            fig.canvas.draw()
        elif event.key == 'r':
            for e in edge_artists.values():
                e.set_visible(True)
            fig.canvas.draw()
        elif event.key == 's':
            # Use a blocking input to ask for file name and format.
            fname = input("Enter file name (with extension .svg or .png): ").strip()
            if fname:
                try:
                    plt.savefig(fname)
                    print(f"Diagram saved as '{fname}'.")
                except Exception as ex:
                    print("Error saving file:", ex)

    fig.canvas.mpl_connect('key_press_event', on_key_press)

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis('off')
    plt.title(
        "Interactive Chord Diagram\n"
        "Click on a node to toggle its edges; press 'c' to clear, 'r' to restore, and 's' to save.",
        fontsize=12
    )
    plt.show()

# ----------------------------------------------------------------
# 7. Main CLI
# ----------------------------------------------------------------
def main():
    while True:
        print("\nSelect an option:")
        print("  1) Show table of relationships between two lists")
        print("  2) Show interactive chord diagram for selected lists")
        print("  3) Quit")
        choice = input("Enter choice (1/2/3): ").strip()
        if choice == '1':
            show_relationship_table()
        elif choice == '2':
            show_chord_diagram()
        elif choice == '3':
            print("Exiting application.")
            break
        else:
            print("Invalid option. Please try again.\n")

if __name__ == '__main__':
    main()
