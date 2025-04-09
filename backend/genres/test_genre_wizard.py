# backend/genres/test_genre_wizard.py
import requests

ACCESS_TOKEN = "AQBbeGjFK7Fn3pW3-YaxiwJ6Jo5z0vVWw8tRFx6YWzAbMuW8OrsIv1s3d4ZShiMk_mS3SAFibZUelXNs3DBtGRhS7AlVqmg9eNyidZx2kdFL4FJEYJdlUhBlDmt4eNyeuz-WLSgWqSUy9gVA0ivo3q-7qQITE29QtW3JbgA1Y7xaglNpUU5d_XxrB7US64fIOCesSRRcNkKx1iAlTJZkTdNuJLl2m1GMKqI_fdtnEzhPIiUpvanb-XlruZ66UwiOM4s6pNzcHnAWER9mZpomxLROyeuhQ7WtK2JYwOYQtaw0nWqKTjUMyEh0IlJ8Md_1YnvPfeyigWQeuGmHnAfujXhqbrPpT8deiQt0OGekbfqoqge_EldM4YhWfV4a"

response = requests.get(
    "http://localhost:8000/me",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
)

print("Status Code:", response.status_code)
print("Response:", response.text)

"""
import json
import requests
from genre_wizard import genre_wizard
import os

file_path = os.path.join(os.path.dirname(__file__), "genre-ontology.json")
# --- Load the genre ontology ---
with open(file_path, "r") as f:
    GENRE_ONTOLOGY = json.load(f)

# --- Config ---
# Replace with your access token (or pull dynamically in real scenario)
ACCESS_TOKEN = "AQBbeGjFK7Fn3pW3-YaxiwJ6Jo5z0vVWw8tRFx6YWzAbMuW8OrsIv1s3d4ZShiMk_mS3SAFibZUelXNs3DBtGRhS7AlVqmg9eNyidZx2kdFL4FJEYJdlUhBlDmt4eNyeuz-WLSgWqSUy9gVA0ivo3q-7qQITE29QtW3JbgA1Y7xaglNpUU5d_XxrB7US64fIOCesSRRcNkKx1iAlTJZkTdNuJLl2m1GMKqI_fdtnEzhPIiUpvanb-XlruZ66UwiOM4s6pNzcHnAWER9mZpomxLROyeuhQ7WtK2JYwOYQtaw0nWqKTjUMyEh0IlJ8Md_1YnvPfeyigWQeuGmHnAfujXhqbrPpT8deiQt0OGekbfqoqge_EldM4YhWfV4a"

# --- Get flat genre list from main.py ---
response = requests.get(
    "http://localhost:8000/user-genres",
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
)

if response.status_code != 200:
    print("❌ Failed to fetch genres:", response.text)
    exit(1)

user_genres = response.json()["genres"]
print(f"✅ Retrieved {len(user_genres)} genres")

# --- Call the genre wizard ---
structured = genre_wizard(user_genres, GENRE_ONTOLOGY)

# --- Generate Sunburst Chart ---
import plotly.graph_objects as go

def flatten_tree(node, parent=None, labels=[], parents=[], values=[]):
    labels.append(node["name"])
    parents.append(parent if parent else "")
    values.append(node.get("value", 0))

    for child in node.get("children", []):
        flatten_tree(child, node["name"], labels, parents, values)

    return labels, parents, values

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
"""