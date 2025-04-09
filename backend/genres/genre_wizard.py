# backend/genres/genre_wizard.py

# Takes flat lists of user genres (from song metadata) and maps them up to a
# recursive genre ontology, returning a structured frequency tree for
# sunburst charting. 

# The Challenge:
# 1. The ontology has zeroed values, since they depend on the user input.
# 2. The genre array triggers incremental frequency propagation up the tree.
# 3. The output is a recursive genre tree with frequencies, ready for a sun-burst chart.

from collections import defaultdict

def genre_wizard(user_genres, ontology, should_abort=lambda: False):
    """
    Builds a recursive frequency tree from user genre data.

    Args:
        user_genres (list of str): Flat list of genres from song metadata.
        ontology (dict): The genre ontology tree.
        should_abort (func): Optional callback that returns True if processing should stop (e.g. user disconnected).

    Returns:
        dict: A recursive genre tree with frequency counts for sunburst charting.
    """

    def normalize_genre_name(name):
        return name.strip().lower()

    def build_genre_map(node, parent=None, mapping=None):
        if mapping is None:
            mapping = {}

        name = node["name"]
        mapping[name] = {
            "parent": parent,
            "children": [child["name"] for child in node.get("children", [])]
        }

        for child in node.get("children", []):
            build_genre_map(child, name, mapping)

        return mapping

    def get_ancestors(genre, genre_map):
        ancestors = []
        while genre:
            ancestors.append(genre)
            genre = genre_map.get(genre, {}).get("parent")
        return ancestors[::-1]

    def build_frequency_tree(user_genres, ontology):
        genre_map = build_genre_map(ontology)
        freq_map = defaultdict(int)

        for genre in user_genres:
            if should_abort():
                raise RuntimeError("Genre Wizard aborted: user cancelled the request.")

            norm_genre = normalize_genre_name(genre)
            if norm_genre in genre_map:
                for ancestor in get_ancestors(norm_genre, genre_map):
                    freq_map[ancestor] += 1
            else:
                print(f"Unknown Genre: {genre}")

        def attach_freq(node):
            if should_abort():
                raise RuntimeError("Genre Wizard aborted during tree reconstruction.")

            name = node["name"]
            new_node = {
                "name": name,
                "value": freq_map.get(name, 0)
            }
            if "children" in node:
                new_node["children"] = [attach_freq(child) for child in node["children"]]
            return new_node

        return attach_freq(ontology)

    return build_frequency_tree(user_genres, ontology)

# Run sunburst_data = build_frequency_tree(user_genres, GENRE_ONTOLOGY)
# This gets you a recusive structre with frequency.