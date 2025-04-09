# backend/genres/test_genre_wizard.py

import json
from genre_wizard import genre_wizard

# Load the genre ontology
with open("genre-ontology.json", "r") as f:
    GENRE_ONTOLOGY = json.load(f)

# Sample user genre list (flat)
user_genres = [
    "classic rock",
    "alternative rock",
    "classic rock",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "synthpop",
    "techno",
    "house",
    "k-pop",
    "classic rock",
    "techno"
]

# Call the genre wizard
structured = genre_wizard(user_genres, GENRE_ONTOLOGY)

# --------- SUNBURST CHART ---------
import plotly.graph_objects as go

# Flatten the recursive tree into Plotly sunburst format
def flatten_tree(node, parent=None, labels=[], parents=[], values=[]):
    labels.append(node["name"])
    parents.append(parent if parent else "")
    values.append(node.get("value", 0))

    for child in node.get("children", []):
        flatten_tree(child, node["name"], labels, parents, values)

    return labels, parents, values

labels, parents, values = flatten_tree(structured)

# Create the sunburst chart
fig = go.Figure(go.Sunburst(
    labels=labels,
    parents=parents,
    values=values,
    branchvalues="total",
    maxdepth=4
))

fig.update_layout(
    margin=dict(t=10, l=10, r=10, b=10),
    title="Genre Frequency Sunburst"
)

fig.show()