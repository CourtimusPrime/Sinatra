# backend/services/genre_service.py

import json
from collections import defaultdict, Counter
import os


def load_genre_hierarchy():
    filepath = os.path.join(os.path.dirname(__file__), "../genres/genre_list.json")
    with open(filepath, "r") as f:
        return json.load(f)


GENRE_TREE = load_genre_hierarchy()
genre_lineage = {}


def parse_genres(node, path=None):
    if path is None:
        path = []

    name = node.get("name")
    full_path = path + [name]
    genre_lineage[name] = full_path

    for child in node.get("genres", []):
        parse_genres(child, full_path)


# Build lineage map
for genre in GENRE_TREE.get("genres", []):
    parse_genres(genre)


def genre_frequency(genre_inputs, limit=20):
    if not isinstance(genre_inputs, list):
        raise ValueError("Expected a list of genres.")
    frequency_counter = Counter(genre_inputs)
    top_genres = frequency_counter.most_common(limit)
    return dict(top_genres)


def get_lineage(genre):
    return genre_lineage.get(genre, ["other", genre])


def tag_genre_levels(genre_inputs):
    result = []
    for genre in genre_inputs:
        lineage = get_lineage(genre)
        level = len(lineage)
        label = (
            "meta-genre"
            if level == 1
            else "genre" if level == 2 else "sub-genre" if level == 3 else "micro-genre"
        )
        result.append(
            {"genre": genre, "level": level, "tag": label, "lineage": lineage}
        )
    return result


def build_sunburst_tree(genre_freq):
    tree = {"name": "music", "children": []}

    def insert_path(root, path, value):
        node = root
        for genre in path[:-1]:
            # Only search children if node has children
            if "children" not in node:
                node["children"] = []

            found = next(
                (child for child in node["children"] if child["name"] == genre), None
            )
            if not found:
                new_node = {"name": genre, "children": []}
                node["children"].append(new_node)
                node = new_node
            else:
                node = found

        final_name = path[-1]
        # Ensure this node can hold children
        if "children" not in node:
            node["children"] = []

        # Now safely search children
        existing_leaf = next(
            (child for child in node["children"] if child["name"] == final_name), None
        )
        if existing_leaf:
            if "value" in existing_leaf:
                existing_leaf["value"] += value
            else:
                existing_leaf["value"] = value
        else:
            node["children"].append({"name": final_name, "value": value})

    for genre, freq_val in genre_freq.items():
        lineage = get_lineage(genre)
        insert_path(tree, lineage, freq_val)

    return tree


def genre_highest(genre_inputs):
    if isinstance(genre_inputs, dict):
        inputs = genre_inputs
    elif isinstance(genre_inputs, list):
        inputs = Counter(genre_inputs)
    else:
        raise ValueError("genre_inputs must be a list or a dict.")

    result = defaultdict(int)

    for genre, count in inputs.items():
        lineage = genre_lineage.get(genre)
        if lineage and len(lineage) > 0:
            top = lineage[0]
            result[top] += count
        else:
            result["other"] += count

    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


def generate_user_summary(genre_freq):
    highest = genre_highest(genre_freq)
    total = sum(highest.values())

    if not highest or total == 0:
        return "We couldn’t find enough genre data to summarize your taste 😢"

    top = sorted(highest.items(), key=lambda x: x[1], reverse=True)

    primary = top[0][0]
    primary_pct = round(top[0][1] / total * 100)

    if len(top) > 1:
        secondary = top[1][0]
        secondary_pct = round(top[1][1] / total * 100)
        detail = f"You also listen to a lot of {secondary} ({secondary_pct}%)."
    else:
        detail = ""

    return f"🎧 You mostly listen to {primary} music ({primary_pct}%). {detail}"
