import os


def print_tree(dir_path, indent=""):
    for i, item in enumerate(sorted(os.listdir(dir_path))):
        if item in {"__pycache__", ".git", ".pytest_cache", ".vscode"} or item.endswith(
            ".pyc"
        ):
            continue
        path = os.path.join(dir_path, item)
        is_last = i == len(os.listdir(dir_path)) - 1
        print(indent + ("└── " if is_last else "├── ") + item)
        if os.path.isdir(path):
            print_tree(path, indent + ("    " if is_last else "│   "))


print_tree(".")
