# ---------------------
# load_settings.py
# Description: Loads the settings for LaziiTV
# http://shayConcepts.com
# Andrew Shay
# ---------------------

import json


def load_key_bindings():
    """
    Loads settings from key_bindings.json

    Returns
    key_bindings -- Dict. All key bindings
    """

    print "Loading Key Bindings"

    json_string = open("key_bindings.json", "r").read()
    key_bindings = json.loads(json_string)

    print "\tSuccess -- Key Bindings Loaded"

    return key_bindings


if __name__ == "__main__":
    key_bindings = load_key_bindings()
    print(key_bindings)
