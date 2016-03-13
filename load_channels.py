# ---------------------
# load_channels.py
# Description: Loads the mode and channel data for LaziiTV
# http://shayConcepts.com
# Andrew Shay
# ---------------------

import json

# List containing the names of the modes in order from channels.xml
mode_names = []
# 2 dim list containing channel names for each mode
channel_names = []
# The modes, channels, dirs in a multi dim list
video_data = []

"""
channel_data.json format

{
    "MODE ONE":[{
        "Channel One":[
            "C:\\Users\\John\\TV\\Some Show",
            "C:\\Users\\John\\TV\\Some Show"
        ],
        "Channel Two":[
            "C:\\Users\\John\\TV\\Some Show",
            "C:\\Users\\John\\TV\\Some Show"
        ]
    }],

    "MODE TWO":[{
        "Channel One":[
            "C:\\Users\\John\\TV\\Some Show"
        ],
        "Channel Two":[
            "C:\\Users\\John\\TV\\Some Show"
        ]
    }]

}

"""


def load_mode_channel_names(channel_json):
    """
    Loads modes and channels names

    :param channel_json: Channel json
    :type channel_json: dict
    """

    global mode_names, channel_names

    print("\tLoading Mode Channel Names")

    for mode in channel_json:
        # mode is a dict
        mode_name = mode.keys()[0]
        mode_names.append(mode_name)
        temp_channels = [channel.keys()[0] for channel in mode[mode_name]]
        channel_names.append(temp_channels)

    print("\tSuccess")


def load_folders(channel_json):
    """
    Reads in the folders

    :param channel_json: Channel json
    :type channel_json: dict
    """

    global mode_names, channel_names, video_data

    print("\tLoading Folders")

    for mode in channel_json:
        modes_channels = []
        mode_name = mode.keys()[0]
        mode_names.append(mode_name)

        for channel in mode[mode_name]:
            channel_name = channel.keys()[0]
            current_channel = channel[channel_name]
            channels_folders = [folder.replace("\\\\", "\\") for folder in current_channel]
            modes_channels.append(channels_folders)
        video_data.append(modes_channels)

    print("\tSuccess")


def load_channel_data():
    """ Loads channel and mode data from channel_data.json """

    json_string = open("channel_data.json", "r").read()
    channel_json = json.loads(json_string)

    print("Loading Channel Data")
    load_mode_channel_names(channel_json)
    load_folders(channel_json)
    print("Success -- Channel Data Loaded")
