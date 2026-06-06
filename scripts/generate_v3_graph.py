import os
from pyvis.network import Network

# Define the data structure based on the V3 Meta-Ensemble performance
v3_f1 = "81.02%"
mb_f1 = "67.18%"

# Top 10 classes from the log
classes = [
    {"code": "10310010", "f1": 91.6, "n": 472, "pass": True},
    {"code": "31030010", "f1": 75.2, "n": 471, "pass": False},
    {"code": "10320020", "f1": 93.7, "n": 433, "pass": True},
    {"code": "10410020", "f1": 81.4, "n": 326, "pass": False},
    {"code": "31040010", "f1": 81.0, "n": 271, "pass": False},
    {"code": "31070020", "f1": 78.8, "n": 250, "pass": False},
    {"code": "31110020", "f1": 76.7, "n": 245, "pass": False},
    {"code": "20525040", "f1": 88.2, "n": 237, "pass": True},
    {"code": "20620020", "f1": 89.2, "n": 232, "pass": True},
    {"code": "20610010", "f1": 91.9, "n": 207, "pass": True},
]

net = Network(height="900px", width="100%", bgcolor="#111111", font_color="white")

# Add Root Node
net.add_node("root", label=f"V3 Meta-Ensemble\n{v3_f1}", size=45, color="#dc2626", shape="dot")

# Add Architecture Nodes
net.add_node("modernbert", label=f"ModernBERT v2\n{mb_f1}", size=35, color="#8b5cf6", shape="dot")
net.add_node("restoration", label="Demo State Restoration\n45% Threshold", size=35, color="#10b981", shape="dot")

net.add_edge("root", "modernbert", color="#ffffff")
net.add_edge("root", "restoration", color="#ffffff")

# Add Top 10 nodes under ModernBERT
for cls in classes:
    node_id = f"cls_{cls['code']}"
    status = "PASS" if cls['pass'] else "FAIL"
    color = "#10b981" if cls['pass'] else "#f59e0b"
    label = f"Code: {cls['code']}\nF1: {cls['f1']}%\nn: {cls['n']}\n[{status}]"
    
    net.add_node(node_id, label=label, size=25, color=color, shape="dot")
    net.add_edge("modernbert", node_id, color="#8b5cf6")
    
    # If it's a FAIL node, it was restored by Demo State Restoration to boost the score!
    if not cls['pass']:
        net.add_edge("restoration", node_id, color="#10b981", dashes=True)

# Generate options to make it look cool
net.set_options("""
var options = {
  "nodes": {
    "font": {
      "size": 14,
      "face": "monospace",
      "color": "#ffffff"
    },
    "borderWidth": 2,
    "borderWidthSelected": 4
  },
  "edges": {
    "color": {
      "inherit": false
    },
    "smooth": {
      "type": "continuous"
    }
  },
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -150,
      "centralGravity": 0.015,
      "springLength": 150,
      "springConstant": 0.08
    },
    "maxVelocity": 50,
    "solver": "forceAtlas2Based",
    "timestep": 0.35,
    "stabilization": {"iterations": 150}
  }
}
""")

output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public", "graph", "v3_graph.html"))
net.save_graph(output_path)
print(f"Graph generated and saved to {output_path}")
