# ---------------------
# load_extensions.py
# Description: Loads the approved file extensions
# http://shayConcepts.com
# Andrew Shay
# ---------------------

import json


def load_file_extensions():
    """
    Loads file extensions from file_extensions.json

    Returns:
    List of file extensions
    """

    json_string = open("file_extensions.json", "r").read()
    extension_json = json.loads(json_string)

    print("Loading File Extensions")
    file_extensions = extension_json["extensions"]
    print("\tSuccess -- File Extensions Loaded")

    return file_extensions

if __name__ == "__main__":
    extensions = load_file_extensions()
    print(extensions)
