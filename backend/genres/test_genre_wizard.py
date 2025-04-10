# backend/genres/test_genre_wizard.py

import json
import requests
from genre_wizard import genre_wizard
import os
import plotly.graph_objects as go

# --- Load ontology ---
file_path = os.path.join(os.path.dirname(__file__), "genre_list.json")
with open(file_path, "r") as f:
    GENRE_ONTOLOGY = json.load(f)

# --- Fetch genres from your running FastAPI server ---
USER_ID = "courtad123"
response = requests.get(f"http://localhost:8000/user-genres?user_id={USER_ID}")

if response.status_code != 200:
    print("❌ Failed to fetch genres:", response.text)
    exit(1)

user_genres = set(response.json().get("genres", []))

# --- Generate structured genre data ---
structured = genre_wizard(user_genres, GENRE_ONTOLOGY)

# --- Sunburst chart helper ---
def flatten_tree(node, parent=None, labels=[], parents=[], values=[]):
    labels.append(node["name"])
    parents.append(parent if parent else "")
    values.append(node.get("value", 0))
    for child in node.get("children", []):
        flatten_tree(child, node["name"], labels, parents, values)
    return labels, parents, values

# --- Plot Sunburst ---
labels, parents, values = flatten_tree(structured)

fig = go.Figure(go.Sunburst(
    labels=labels,
    parents=parents,
    values=values,
    branchvalues="total",
    maxdepth=4
))

fig.update_layout(
    margin=dict(t=10, l=10, r=10, b=10),
    title="User Genre Sunburst (Top 100 Tracks - Last Month)"
)

fig.show()