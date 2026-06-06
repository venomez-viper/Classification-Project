import os
import pandas as pd
import networkx as nx
from pyvis.network import Network

# ================= Configuration =================
TASK1_CSV = r"c:\Users\akash\Desktop\capstone MGT 599\data\cleaned\task1_clean.csv"
TASK2_CSV = r"c:\Users\akash\Desktop\capstone MGT 599\data\cleaned\task2_clean.csv"
OUTPUT_DIR = r"c:\Users\akash\Desktop\capstone MGT 599\graph_visualizer"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "classification_graph.html")

# Limit the number of rows to prevent the browser from crashing. 
# Keep it at 1000-2000 for quick fluid physics, or switch to None for the full 27k dataset.
LIMIT = 1000 

KEYWORDS = [
    "cloud", "saas", "brokerage", "logistics", "warehousing", 
    "staffing", "leasing", "software", "retail", "manufacturing", 
    "consulting", "banking", "insurance", "pension", "nutrition", 
    "health", "medical", "industrial", "technology", "financial"
]
# =================================================

def main():
    print("Loading datasets...")
    try:
        # We only need specific columns from Task 1 to get the overarching Industry logic
        df1 = pd.read_csv(TASK1_CSV, usecols=['CompanyId', 'SegmentName', 'MstarGlobal'])
        # Drop duplicates just in case Task 1 has multi-revenue lines for the same segment
        df1 = df1.drop_duplicates(subset=['CompanyId', 'SegmentName'])
        
        df2 = pd.read_csv(TASK2_CSV)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    # Randomly sample the segments from Task 2 to keep the graph interactive and fluid in the browser
    if LIMIT is not None and LIMIT < len(df2):
        print(f"Sampling {LIMIT} segments for visualization...")
        df2 = df2.sample(n=LIMIT, random_state=42)
    else:
        print(f"Processing all {len(df2)} segments...")

    print("Merging Task 1 (Industry) and Task 2 (Subindustry) context...")
    # Left Merge onto Task 2 so we bring in the broad 'MstarGlobal' tag for each segment
    df = pd.merge(df2, df1, on=['CompanyId', 'SegmentName'], how='left')

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    G = nx.Graph()

    print("Building 5-Tier Hierarchical Graph Nodes and Edges...")
    
    # Track additions to avoid duplication
    added_nodes = set()

    def add_node(node_id, label, group, color, size, title):
        if node_id not in added_nodes:
            G.add_node(node_id, label=label, group=group, color=color, size=size, title=title)
            added_nodes.add(node_id)

    for idx, row in df.iterrows():
        comp_id = str(row.get('CompanyId', f"Comp_{idx}")).strip()
        sub_id = str(row.get('Subindustry', "Unknown_Sub")).strip()
        industry_id = str(row.get('MstarGlobal', "Unknown_Ind")).strip()
        
        # Sometimes float NaNs leak through as 'nan' strings
        if industry_id == 'nan' or not industry_id:
            # If Task 1 is missing it, map from the first 8 digits of Subindustry usually (assuming Morningstar hierarchical logic)
            industry_id = sub_id[:8] if len(sub_id) >= 8 else "Unknown_Ind"
            
        seg_name = str(row.get('SegmentName', f"Seg_{idx}")).strip()
        description = str(row.get('SegmentDescription', "")).strip()

        # Define node IDs
        i_node = f"IND_{industry_id}"
        s_node = f"SUB_{sub_id}"
        c_node = f"COMP_{comp_id}"
        seg_node = f"SEG_{idx}" # unique index
        
        # 1. Add Broad Industry Node (Purple - Task 1)
        add_node(
            i_node, 
            label=f"Ind: {industry_id}", 
            group="Industry", 
            color="#9b59b6", 
            size=40, 
            title=f"Industry (Task 1): {industry_id}"
        )
        
        # 2. Add Subindustry Node (Red - Task 2)
        add_node(
            s_node, 
            label=f"Sub: {sub_id}", 
            group="Subindustry", 
            color="#e74c3c", 
            size=30, 
            title=f"Subindustry (Task 2): {sub_id}"
        )
        
        # Connect Subindustry strictly to its overarching Industry!
        G.add_edge(s_node, i_node)

        # 3. Add Company Node (Green)
        add_node(
            c_node, 
            label=f"Co: {comp_id}", 
            group="Company", 
            color="#2ecc71", 
            size=20, 
            title=f"Company ID: {comp_id}"
        )
        
        # 4. Add Segment Node (Blue)
        wrapped_desc = "<br>".join([description[i:i+60] for i in range(0, len(description), 60)])
        add_node(
            seg_node, 
            label=f"{seg_name}"[:15] + ("..." if len(seg_name) > 15 else ""), 
            group="Segment", 
            color="#3498db", 
            size=10, 
            title=f"<b>{seg_name}</b><br>{wrapped_desc}"
        )

        # Connect Segment to its Company and its local Subindustry
        G.add_edge(seg_node, c_node)
        G.add_edge(seg_node, s_node)

        # 5. Extract Keywords and Connect (Yellow)
        desc_lower = description.lower()
        for kw in KEYWORDS:
            if kw in desc_lower:
                kw_node = f"KW_{kw}"
                add_node(
                    kw_node, 
                    label=f"#{kw}", 
                    group="Keyword", 
                    color="#f1c40f", 
                    size=25, 
                    title=f"Keyword Feature: {kw}"
                )
                G.add_edge(seg_node, kw_node)
                
    print(f"Total Combined Nodes: {G.number_of_nodes()}")
    print(f"Total Intricate Edges: {G.number_of_edges()}")

    print("Generating the Master Hierarchy Graph HTML...")
    
    net = Network(height='900px', width='100%', bgcolor='#111111', font_color='white', filter_menu=True, select_menu=True, cdn_resources='remote')
    net.from_nx(G)

    # Physics tweaked to handle massive hierarchical depth
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "centralGravity": 0.005,
          "springLength": 100,
          "springConstant": 0.04,
          "damping": 0.5
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "stabilization": {
            "enabled": true,
            "iterations": 1000
        }
      },
      "nodes": {
        "shape": "dot",
        "font": {
             "size": 12,
             "face": "Tahoma"
        }
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "smooth": {
          "enabled": false,
          "type": "continuous"
        }
      }
    }
    """)

    # Export
    original_cwd = os.getcwd()
    os.chdir(OUTPUT_DIR)
    try:
        net.write_html("classification_graph.html")
    finally:
        os.chdir(original_cwd)
        
    print(f"\nMaster Graph complete! -> {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
