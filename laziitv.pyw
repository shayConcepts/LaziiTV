# ---------------------
# LaziiTV v1.0.1
# http://shayConcepts.com
# Andrew Shay
# ---------------------

# import external libraries
import wx  # 2.8
import vlc

# import standard libraries
import os
import sys
import time
import random
import thread

import load_bindings
import load_channels
import load_extensions

from os import listdir
from os.path import isfile, join

# -------- Global Vars --------
video_data = []  # The modes, channels, dirs
current_mode = 0  # The current mode that is playing
current_channel = 0  # The current channel that is playing
current_video_name = ""  # The name of the current video playing
current_video_path = None  # Path and file name of current video playing
previous_video_path = None  # Path and file name of previously played video
current_display = 0  # Current montior LaziiTV is on
user_stop = True  # The user has forced stopped player

# List containing the names of the modes in order from channels.xml
mode_names = []
channel_names = []  # 2 dim list containing channel names for each mode

file_extensions = []
key_bindings = {}


class PopUpWin(wx.Frame):
    """ Popup window at the bottom of the screen when a new video is played """

    def __init__(self):
        style = (wx.CLIP_CHILDREN | wx.STAY_ON_TOP |
                 wx.NO_BORDER | wx.FRAME_SHAPED)
        wx.Frame.__init__(self, None, title='LaziiTV', style=style)
        dw, dh = wx.DisplaySize()  # Get dimesions of screen
        self.SetTransparent(200)  # Set transparecy of popup window

    def set_text(self, text):
        '''
        self.defaultstyle = wx.richtext.RichTextAttr()
        self.GetStyle(self.GetInsertionPoint(), self.defaultstyle)
        self.defaultsize = self.defaultstyle.GetFont().GetPointSize()
        '''

        ''' Sets the text of the popup window and displays it'''

        current_dim = wx.Display.GetGeometry(wx.Display(current_display))
        display_width = current_dim[2]
        display_height = current_dim[3]
        dc = wx.MemoryDC()
        font = wx.Font(25, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD, False)

        dc.SetFont(font)
        tw, th = dc.GetTextExtent(text)  # Get font dimensions

        # Set size of popup based on screen width and font height
        self.SetSize((display_width, th * 3))
        w, h = self.GetSize()  # Get dimensions of popup
        # Set popup to bottom of window
        self.SetPosition((current_dim[0], display_height - h))

        bmp = wx.EmptyBitmap(w, h)

        white_color = wx.Colour(255, 255, 255)
        black_color = wx.Colour(0, 0, 0)
        black_brush = wx.Brush(black_color, style=wx.BRUSHSTYLE_SOLID)
        dc.SetBackground(black_brush)
        dc.SetTextForeground(white_color)
        dc.SetTextBackground(black_color)

        dc.SelectObject(bmp)
        dc.Clear()
        dc.DrawText(text, (w-tw)/2,  (h-th)/2)
        dc.SelectObject(wx.NullBitmap)
        wx.StaticBitmap(self, -1, bmp)

        self.SetBackgroundColour('black')

        # Hides cursor
        self.cursor = wx.StockCursor(wx.CURSOR_BLANK)
        # set the cursor for the window
        self.SetCursor(self.cursor)

        self.Show()

    def hide(self):
        ''' Hides the popup window'''
        self.Destroy()


class Player(wx.Frame):
    """ The main window that has to deal with events """

    msg_text = ""  # The text for the popup message

    def __init__(self, title):

        self.load_settings()

        wx.Frame.__init__(self, None, 2, title,
                          pos=wx.DefaultPosition,
                          size=(500, 500),
                          style = wx.DEFAULT_FRAME_STYLE & ~wx.CAPTION)
        # The DEFAULT_FRAME STYLE & CAPTION from above makes it full screen,
        # covering taskbar too!

        favicon = wx.Icon('icon_big.ico', wx.BITMAP_TYPE_ANY)
        wx.Frame.SetIcon(self, favicon)

        # Set msg_win to be a popup window
        self.msg_win = PopUpWin()

        # Panels
        # The first panel holds the video and it's all black
        self.videopanel = wx.Panel(self, -1)
        self.videopanel.SetBackgroundColour(wx.BLACK)

        # Put everything togheter
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.videopanel, 1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize((350, 300))

        # VLC player controls
        self.Instance = vlc.Instance()

        # Create the player
        self.player = self.Instance.media_player_new()

        dw, dh = wx.DisplaySize()  # Get dimesions of screen

        # Captures key presses
        # Why create cap_panel? When the popup appears, videopanel loses focus
        # Since videopanel is a panel, focus cannot be directly set to it.
        # Instead when focus is called on it, its first child component
        # receives focus. Therefore cap_panel is a child of videopanel
        # and is used to capture key presses because it actually
        # receives the focus. It is made the size of the screen to
        # capture key presses as well.

        self.cap_panel = wx.Panel(self.videopanel, size=((dw, dh)))

        # Listen for key presses
        self.cap_panel.Bind(wx.EVT_KEY_UP, self.on_key_press)

        # Respond to mouse clicks
        self.cap_panel.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left)
        self.cap_panel.Bind(wx.EVT_LEFT_DCLICK, self.on_mouse_leftd)
        self.cap_panel.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right)
        self.cap_panel.Bind(wx.EVT_MIDDLE_DOWN, self.on_mouse_middle)
        self.cap_panel.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

        # self.ShowFullScreen(True)
        self.Maximize()  # Use this

        # Hides cursor
        self.cursor = wx.StockCursor(wx.CURSOR_BLANK)
        # set the cursor for the window
        self.SetCursor(self.cursor)

        # Play the first channel on the first mode
        print("Playing first channel on first mode")
        self.play(0, 0)

        # Check when video has finished
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.check_video_finished, self.timer)
        self.timer.Start(milliseconds=1000, oneShot=wx.TIMER_CONTINUOUS)

    def load_settings(self):
        global key_bindings, mode_names, channel_names, video_data
        global file_extensions

        try:
            load_channels.load_channel_data()
            video_data = load_channels.video_data
            channel_names = load_channels.channel_names
            mode_names = load_channels.mode_names

        except Exception, e:
            error_msg = str(e)
            if "No such file" in error_msg:
                print str(e)
                self.error_dialog("No channel data. Create it with LaziiTV Configure.")
            else:
                print str(e)
                self.error_dialog("channel_data.json is not correctly\
                                  constructed")

        try:
            key_bindings = load_bindings.load_key_bindings()
        except Exception, e:
            error_msg = str(e)
            if "No such file" in error_msg:
                print str(e)
                self.error_dialog("key_bindings.json does not exist")
            else:
                print str(e)
                self.error_dialog("key_bindings.json is not\
                                  correctly formatted")

        try:
            file_extensions = load_extensions.load_file_extensions()
        except Exception, e:
            error_msg = str(e)
            if "No such file" in error_msg:
                print str(e)
                self.error_dialog("file_extensions.json does not exist")
            else:
                print str(e)
                self.error_dialog("file_extensions.json is not\
                                  correctly formatted")

    def check_video_finished(self, event):
        """ If a video has ended, start a new one """
        global user_stop
        if self.player.is_playing() == 0 and user_stop is False:
            user_stop = True
            self.refresh_channel()

    def on_mouse_wheel(self, event):
        """ Action when scroll wheel is scrolled """
        if event.GetWheelRotation() > 0:
            self.play_pause()
        elif event.GetWheelRotation() < 0:
            self.video_stop()
        else:
            event.Skip()

    def on_mouse_left(self, event):
        """ Action on left click """
        self.channel_up()
        event.Skip()

    def on_mouse_leftd(self, event):
        """ Action on double left click """
        self.channel_down()
        self.channel_down()
        event.Skip

    def on_mouse_right(self, event):
        """ Action on right click """
        self.change_mode()
        event.Skip()

    def on_mouse_middle(self, event):
        """ Action on middle click """
        self.refresh_channel()
        event.Skip()

    def play_pause(self):
        """ Play/Pause video """
        global user_stop
        if self.player.is_playing():
            user_stop = True
        else:
            user_stop = False
        print("Pause/Play video")
        self.player.pause()

    def video_stop(self):
        """ Stops video """
        global user_stop
        user_stop = True
        print("Stop video")
        self.player.stop()

    def refresh_channel(self):
        """ Refreshes channel """
        global current_mode
        global current_channel
        global user_stop
        print("Refresh Channel")
        user_stop = False
        self.play(current_mode, current_channel)

    def channel_up(self):
        """ Goes up one channel """
        global current_mode
        global current_channel
        global video_data

        print("Channel Up")
        new_channel = current_channel + 1
        if len(video_data[current_mode]) - 1 < new_channel:
            new_channel = 0

        current_channel = new_channel
        self.play(current_mode, current_channel)

    def channel_down(self):
        """ Go down one channel """
        global current_mode
        global current_channel
        global video_data

        print("Channel Down")
        new_channel = current_channel - 1
        if new_channel < 0:
            new_channel = len(video_data[current_mode]) - 1

        current_channel = new_channel
        self.play(current_mode, current_channel)

    def change_mode(self):
        """ Changes mode """
        global current_mode
        global current_channel
        global video_data

        print("Change modes")
        new_mode = current_mode + 1
        if len(video_data) - 1 < new_mode:
            new_mode = 0

        current_channel = 0  # When a new mode is loaded, reset the channel
        current_mode = new_mode

        self.play(current_mode, 0)

    def on_key_press(self, event):
        """ Perform action on certain key presses """

        global current_mode
        global current_channel
        global video_data
        global user_stopped
        global key_bindings
        global current_display
        global previous_video_path

        keycode = event.GetKeyCode()
        print keycode  # DELETE

        # Refresh channel
        if keycode == key_bindings["refresh_bind"]:  # R
            self.refresh_channel()

        # Channel up wx.WXK_UP
        elif keycode == key_bindings["channel_up_bind"]:  # Q
            self.channel_up()

        # Channel down
        elif keycode == key_bindings["channel_down_bind"]:  # A
            self.channel_down()

        # Chane mode
        elif keycode == key_bindings["change_mode_bind"]:  # M
            self.change_mode()

        # Pause/Play video
        elif keycode == key_bindings["play_pause_bind"]:
            self.play_pause()

        # Stop video
        elif keycode == key_bindings["stop_bind"]:
            self.video_stop()

        # Close program
        elif keycode == key_bindings["quit_bind"]:
            print "Close program"
            self.video_stop()
            sys.exit(0)

        # Go back 30 seconds
        elif keycode == key_bindings["skip_backward_bind"]:  # W
            print "Go back 30 seconds"

            current_time = self.player.get_time()  # ms
            current_time = current_time / 1000  # seconds

            new_time = current_time - 30
            new_time = new_time * 1000  # back to ms

            if new_time < 0:
                self.player.set_time(0)
            else:
                self.player.set_time(new_time)

        # Go forward 30 seconds
        elif keycode == key_bindings["skip_forward_bind"]:  # E
            print("Skip ahead 30 seconds")

            current_time = self.player.get_time()  # ms
            current_time = current_time / 1000  # seconds

            new_time = current_time + 30
            new_time = new_time * 1000  # back to ms

            if new_time > self.player.get_length():
                self.play(current_mode, current_channel)
            else:
                self.player.set_time(new_time)

        # Changes the display that LaziiTV appears on
        elif keycode == key_bindings["change_display"]:  # D
            current_dim = wx.Display.GetGeometry(wx.Display(current_display))
            shift_right = current_dim[0] + current_dim[2]

            self.Maximize(False)
            self.SetPosition((shift_right, 0))
            self.Maximize(True)

            current_display += 1
            # Reset monitor if you go passed the max count
            if current_display >= wx.Display.GetCount():
                current_display = 0

        # Load previous video
        elif keycode == key_bindings["previous_video"]:
            if previous_video_path is not None:
                # Get the name first because once the show_msg is run,
                # previous_video_path is switched and the wrong file name
                # is shown
                # Split the path to just get the file name itself
                file_name = previous_video_path.split(os.path.sep)[-1]
                # Get filename without extension
                file_name = os.path.splitext(file_name)[-2]
                self.load_vlc_media(previous_video_path)
                self.show_msg(file_name, True)
                print previous_video_path
            else:
                self.show_msg("There is no previous video to play", True)

        # Displays popup window
        elif keycode == key_bindings["info_bind"]:  # I
            self.show_msg(None, False)

        else:
            print("No key binding")
            event.Skip()

    def on_exit(self, evt):
        """ Closes the window. """
        self.Close()

    def on_play(self, evt):
        """ Toggle the status to Play/Pause. """

        if self.player.play() == -1:
            print("Cannot play video")
            self.error_dialog("Unable to play current file")

    def error_dialog(self, errormessage):
        """ Display error message """

        wx.MessageBox(errormessage, 'Error',
                      wx.OK | wx.ICON_ERROR)
        sys.exit(0)

    def get_sub_dirs(self, dir_path):
        """
        Returns list of sub directories of a given path

        Keyword arguments:
        dir_path -- String. Path to check for sub directories

        Returns:
        List of sub directories
        """
        sub_dirs = []
        for f in listdir(dir_path):
            current_path = join(dir_path, f)
            if not isfile(current_path):
                sub_dirs.append(current_path)
        return sub_dirs

    def check_file_extension(self, filepath):
        """
        Checks that the extension of the video file is an approved extension

        Keyword arguments:
        filepath -- String.  The path and name of the file

        Returns:
        True -- The extension is allowed
        False -- The extension is not allowed
        """
        global file_extensions

        if filepath == "":
            return False

        extension = os.path.splitext(filepath)[-1]
        extension = extension.lower()
        if extension in file_extensions:
            return True
        else:
            return False

    def get_files_from_dir(self, dir_path):
        """
        Returns list of files fromthe given directory

        Keyword arguments:
        dir_path -- String.  Path to get list of files from

        Returns:
        List of files from given directory
        """

        all_files = []
        for video in listdir(dir_path):
            if isfile(join(dir_path, video)):
                all_files.append(join(dir_path, video))

        return all_files

    def load_vlc_media(self, video_path):
        """
        Loads video into VLC and starts media

        Keyword arguments:
        video_path -- String. Path to video file to play
        """
        global current_video_path
        global previous_video_path
        global user_stop

        previous_video_path = current_video_path
        current_video_path = video_path
        self.Media = self.Instance.media_new(unicode(
                                             os.path.join(video_path)))

        try:
            self.player.set_media(self.Media)
        except:
            print "Failed video"
        self.player.set_hwnd(self.videopanel.GetHandle())

        try:
            self.on_play(None)  # This also plays a file
            user_stop = False
        except:
            print "Cannot PLAY"

    def play(self, mode, channel):
        """ Plays a specific mode and channel """
        global video_data, user_stop

        try:
            # Pick a random folder in a channel
            random_folder = random.randint(0, len(video_data[mode][channel])-1)
            # The path of that folder
            dir_path = video_data[mode][channel][random_folder]

            # Get all sub folders from a channel's folder
            all_folders = self.get_sub_dirs(dir_path)

            # All videos from the folders
            all_videos = []

            # There are no sub directories, look for video files in dir_path
            # eg Movie folder with just movies
            if len(all_folders) == 0:
                # Get all video files from dir_path
                all_videos = self.get_files_from_dir(dir_path)

            # There are sub directories, scan them
            # eg TV show, so scan the season folders
            else:
                # Get all video files from the above folders
                for folder in all_folders:
                    all_videos += self.get_files_from_dir(folder)

            random_video = ""
            tries = 0  # After 100,000 tries, quit
            while not self.check_file_extension(random_video):
                # Generate a random number to pick a video file
                random_number = random.randint(0, len(all_videos)-1)

                # Grab the random video file
                random_video = all_videos[random_number]
                tries += 1
                if tries == 100000:
                    msg = "Could not find video with valid extension"\
                          " after 100,000 attempts"
                    self.error_dialog(msg)
                    sys.exit(1)

            # Start video
            self.load_vlc_media(random_video)

            # Split the path to just get the file name itself
            file_name = random_video.split(os.path.sep)[-1]
            # Get filename without extension
            file_name = os.path.splitext(file_name)[-2]
            self.show_msg(mode_names[current_mode] + " - " +
                          channel_names[current_mode][current_channel] +
                          " - " + file_name, False)
            print(random_video.encode('ascii', 'ignore'))

        except Exception, e:
            print str(e)
            self.error_dialog("channels_data.json is not properly constructed")

    def show_msg(self, text_dis, is_temp=False):
        """
        Shows the popup window

        Keyword arguments:
        text_dis -- String. Message to display
        is_temp -- Boolean. If this is a temporary message
        """

        # If a message wasn't sent in, reuse old message
        # Else set the new global message
        if text_dis is not None and is_temp is False:
            self.msg_text = text_dis

        try:
            self.msg_win.hide()  # Hide current msg_win
        except:
            pass

        self.msg_win = PopUpWin()  # Make a new one
        if is_temp is True:
            self.msg_win.set_text(text_dis)  # Set its text and display
        else:
            self.msg_win.set_text(self.msg_text)  # Set its text and display
        # Thread to hide
        thread.start_new_thread(hide_msg_thread, (self, self.msg_win))
        self.cap_panel.SetFocus()  # Return focus to listen to key events


def hide_msg_thread(main_player, msg_win):
    """ Hides the popup message window """
    time.sleep(3)

    try:
        if msg_win is not None:
            msg_win.hide()

    # This seems to happen on a bad file
    except:
        pass


if __name__ == "__main__":
    app = wx.App()

    main_player = Player("LaziiTV")
    # show the player window centred and run the application
    main_player.Centre()
    main_player.Show()

    app.MainLoop()
