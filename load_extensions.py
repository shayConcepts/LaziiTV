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

    :return: List of file extensions
    :rtype: list
    """

    json_string = open("file_extensions.json", "r").read()
    extension_json = json.loads(json_string)

    print("Loading File Extensions")
    file_extensions = extension_json["extensions"]
    print("\tSuccess -- File Extensions Loaded")

    return file_extensions
