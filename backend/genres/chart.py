# backend/genres/chart.py

def to_sunburst_format(tree):
    labels = []
    parents = []
    values = []

    def walk(node, parent=""):
        if "name" in node:
            labels.append(node["name"])
            parents.append(parent)
            values.append(node.get("value", 0))

        for child in node.get("children", []):
            walk(child, node["name"])

    walk(tree)
    return {
        "labels": labels,
        "parents": parents,
        "values": values
    }

def to_bubble_format(genre_freq, color_map=None):
    if color_map is None:
        color_map = {}

    return [
        {
            "genre": genre,
            "value": value,
            "color": color_map.get(genre.lower(), "#cccccc")
        }
        for genre, value in genre_freq.items()
    ]