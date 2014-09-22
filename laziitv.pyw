'''
LaziiTV v0.5.0
http://shayConcepts.com
Andrew Shay
'''

# import external libraries
import wx # 2.8
import vlc

# import standard libraries
import os
import user
import time
import thread
import sys
import random

from os import listdir
from os.path import isfile, join

from xml.dom import minidom


'''-------- End Global Vars --------'''
video_data = [] #The modes, channels, dirs
current_mode = 0 #The current mode that is playing
current_channel = 0 #The current channel that is playing
current_video_name = "" #The name of the current video playing
mode_names = [] #List containing the names of the modes in order from channels.xml
channel_names = [] #2 dim list containing channel names for each mode

''' Key bindings '''
play_pause_bind = 0
stop_bind = 0
refresh_bind = 0
channel_up_bind = 0
channel_down_bind = 0
change_mode_bind = 0
skip_forward_bind = 0
skip_backward_bind = 0
quit_bind = 0
info_bind = 0

'''-------- End Global Vars --------'''

def load_settings():
	''' Loads settings from Settings.txt '''
	
	global play_pause_bind, stop_bind, refresh_bind, channel_up_bind, channel_down_bind
	global change_mode_bind, skip_forward_bind, skip_backward_bind, quit_bind, info_bind
	
	print "Loading settings"
	
	settings = open("Settings.txt")
	settings_lines = settings.readlines()
	settings.close()
	
	for setting in settings_lines:
		split = setting.split("=")
		command = split[0].strip()
		binding = int(split[1].strip())
		
		if command == "Play/Pause":
			play_pause_bind = binding
		
		elif command == "Stop":
			stop_bind = binding
		
		elif command == "Refresh":
			refresh_bind = binding
			
		elif command == "Channel Up":
			channel_up_bind = binding
		
		elif command == "Channel Down":
			channel_down_bind = binding
		
		elif command == "Change Mode":
			change_mode_bind = binding
		
		elif command == "Skip Forward":
			skip_forward_bind = binding
		
		elif command == "Skip Backward":
			skip_backward_bind = binding
		
		elif command == "Quit":
			quit_bind = binding
			
		elif command == "Info":
			info_bind = binding
			
	'''
	print play_pause_bind
	print stop_bind
	print refresh_bind
	print channel_up_bind
	print channel_down_bind
	print change_mode_bind
	print skip_forward_bind
	print skip_backward_bind
	print quit_bind
	print info_bind
	'''
	
	print "Settings loaded"

def load_channels_xml():
	'''Loads the video data from channels.xml'''
	
	global video_data
	
	'''----------- loads folders into video_data ---------------'''
	doc = minidom.parse("channels.xml")
	node = doc.documentElement
	modes = doc.getElementsByTagName("mode")
	
	#Get mode and channel names
	for mode in modes:
		mode_names.append(mode.attributes['name'].value)
		channels = mode.getElementsByTagName("channel")
		temp_channel_names = []
		for channel in channels:
			temp_channel_names.append(channel.attributes['name'].value)
		channel_names.append(temp_channel_names)
		

	#Reads in the modes
	for mode in modes:
		channels = mode.getElementsByTagName("channel")

		modes_channels = []
		del modes_channels[:]
		
		#Reads in the channels
		for channel in channels:
			folders = channel.getElementsByTagName("folder")
			channels_folders = []
			del channels_folders[:]
			
			#Reads in the folders
			for folder in folders:
				folder_locs = folder.childNodes
				#folders_dirs = []
				#del folders_dirs[:]
				
				#Reads in the directories
				for folder_loc in folder_locs:
					#folders_dirs.append(folder_loc.data)
					channels_folders.append(folder_loc.data)
				#channels_folders.append(folders_dirs)
			modes_channels.append(channels_folders)
		video_data.append(modes_channels)


class PopUpWin(wx.Frame):
	''' Popup window at the bottom of the screen when a new video is played '''
	
	def __init__(self):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP |
				  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title='LaziiTV', style = style)
		dw, dh = wx.DisplaySize() #Get dimesions of screen
		self.SetTransparent(200) #Set transparecy of popup window
		

	
	def set_text(self, text):
		'''
		self.defaultstyle = wx.richtext.RichTextAttr()
		self.GetStyle(self.GetInsertionPoint(), self.defaultstyle)
		self.defaultsize = self.defaultstyle.GetFont().GetPointSize()
		'''
	
		''' Sets the text of the popup window and displays it'''
		dw, dh = wx.DisplaySize() #Get dimesions of screen
		dc = wx.MemoryDC()
		font = wx.Font(25, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
		#font.SetPixelSize((12,35))
		dc.SetFont(font)
		tw, th = dc.GetTextExtent(text) #Get font dimensions
		
		self.SetSize((dw, th * 3)) #Set size of popup based on screen width and font height
		w, h = self.GetSize() #Get dimensions of popup
		self.SetPosition((0, dh - h)) #Set popup to bottom of window
		
		bmp = wx.EmptyBitmap(w, h)	

		white_color = wx.Colour(255,255,255)
		black_color = wx.Colour(0,0,0)
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
		
		#Hides cursor
		self.cursor = wx.StockCursor(wx.CURSOR_BLANK) 
		# set the cursor for the window
		self.SetCursor(self.cursor)
		
		self.Show()
		
	def hide(self):
		''' Hides the popup window'''
		self.Destroy()
		

	
class Player(wx.Frame):
	"""The main window has to deal with events."""

	
	
	msg_text = "" #The text for the popup message
	
	def __init__(self, title):
		print "Loading modes and channels"
		try:
			load_channels_xml()
		except Exception, e:
			error_msg = str(e)
			if "No such file" in error_msg:
				print str(e)
				self.error_dialog("channels.xml does not exist")
			else:
				print str(e)
				self.error_dialog("channels.xml is not correctly constructed or a non-video file is in the directory")
		print "Modes and channels loaded"
		
		
		try:
			load_settings()
		except Exception, e:
			error_msg = str(e)
			if "No such file" in error_msg:
				print str(e)
				self.error_dialog("Settings.txt does not exist")
			else:
				print str(e)
				self.error_dialog("Settings.txt is not correctly constructed")
		
		wx.Frame.__init__(self, None, 2, title,
		pos=wx.DefaultPosition, size=(500, 500),style = wx.DEFAULT_FRAME_STYLE & ~wx.CAPTION)
		#The DEFAULT_FRAME STYLE & CAPTION from above makes it full screen, covering taskbar too!
		
		favicon = wx.Icon('icon_big.ico', wx.BITMAP_TYPE_ANY)
		wx.Frame.SetIcon(self, favicon)
		
		#Set msg_win to be a popup window
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
		
		#Create the player
		self.player = self.Instance.media_player_new()
		
		dw, dh = wx.DisplaySize() #Get dimesions of screen
		
		#Captures key presses
		#Why create cap_panel? When the popup appears, videopanel loses focus
		#Since videopanel is a panel, focus cannot be directly set to it. Instead when
		#focus is called on it, its first child component receives focus. Therefore cap_panel
		#is a child of videopanel and is used to capture key presses because it actually
		#receives the focus. It is made the size of the screen to capture key presses as well.
		
		self.cap_panel = wx.Panel(self.videopanel, size=((dw,dh)))
			
		#Listen for key presses
		self.cap_panel.Bind(wx.EVT_KEY_UP, self.on_key_press)
		
		#Respond to mouse clicks
		self.cap_panel.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left)
		self.cap_panel.Bind(wx.EVT_LEFT_DCLICK, self.on_mouse_leftd)			
		self.cap_panel.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right)	
		self.cap_panel.Bind(wx.EVT_MIDDLE_DOWN, self.on_mouse_middle)
		self.cap_panel.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
		
		#self.ShowFullScreen(True)
		self.Maximize() #Use this
		
		#Hides cursor
		self.cursor = wx.StockCursor(wx.CURSOR_BLANK) 
		# set the cursor for the window
		self.SetCursor(self.cursor)
		
		#Play the first channel on the first mode
		print "Playing first channel on first mode"
		self.play(0 , 0)
		
		#Check when video has finished
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.check_video_finished, self.timer)
		self.timer.Start(milliseconds=400, oneShot=wx.TIMER_CONTINUOUS)
		
	def check_video_finished(self, event):
		'''If a video has ended, start a new one'''
		if self.player.get_position() >= 0.9999:
			self.refresh_channel()

	def on_mouse_wheel(self, event):
		''' Action when scroll wheel is scrolled '''
		if event.GetWheelRotation() > 0:
			self.play_pause()
		elif event.GetWheelRotation() < 0:
			self.video_stop()
		else:
			event.Skip()

	def on_mouse_left(self, event):
		''' Action on left click '''
		self.channel_up()
		event.Skip()
		
	
	def on_mouse_leftd(self, event):
		''' Action on double left click '''
		self.channel_down()
		self.channel_down()
		event.Skip
	
	
	def on_mouse_right(self, event):
		''' Action on right click '''
		self.change_mode()
		event.Skip()
	
	
	def on_mouse_middle(self, event):
		''' Action on middle click '''
		self.refresh_channel()
		event.Skip()
	
	
	def play_pause(self):
		''' Play/Pause video '''
		print "Pause/Play video"
		self.player.pause()
	
	
	def video_stop(self):
		''' Stops video '''
		print "Stop video"
		self.player.stop()
	
	
	def refresh_channel(self):
		'''Refreshes channel'''
		global current_mode
		global current_channel
		
		print "Refresh Channel"
		self.play(current_mode, current_channel)
		
	
	def channel_up(self):
		'''Goes up one channel'''
		global current_mode
		global current_channel
		global video_data
		
		print "Channel Up"
		new_channel = current_channel + 1
		if len(video_data[current_mode]) - 1 < new_channel:
			new_channel = 0
		
		current_channel = new_channel
		self.play(current_mode, current_channel)
		
		
	def channel_down(self):
		'''Go down one channel'''
		global current_mode
		global current_channel
		global video_data
		
		print "Channel Down"
		new_channel = current_channel - 1
		if new_channel < 0:
			new_channel = len(video_data[current_mode]) - 1
		
		current_channel = new_channel
		self.play(current_mode, current_channel)	
		
		
	def change_mode(self):
		'''Changes mode'''
		global current_mode
		global current_channel
		global video_data
		
		print "Change modes"
		new_mode = current_mode + 1
		if len(video_data) -1 < new_mode:
			new_mode = 0
		
		current_channel = 0 #When a new mode is loaded, reset the channel
		current_mode = new_mode
		
		self.play(current_mode, 0)
	

	def on_key_press(self, event):
		'''Perform action on certain key presses'''
		
		global current_mode
		global current_channel
		global video_data
		global user_stopped
		
		global play_pause_bind, stop_bind, refresh_bind, channel_up_bind, channel_down_bind
		global change_mode_bind, skip_forward_bind, skip_backward_bind, quit_bind, info_bind
	
		
		keycode = event.GetKeyCode()
		print keycode # DELETE		
		
		#Refresh channel
		if keycode == refresh_bind: #R
			self.refresh_channel()
		
		#Channel up wx.WXK_UP
		elif keycode == channel_up_bind: #Q
			self.channel_up()
				
		#Channel down
		elif keycode == channel_down_bind: #A
			self.channel_down()
		
		#Chane mode
		elif keycode == change_mode_bind: #M
			self.change_mode()
		
		#Pause/Play video
		elif keycode == play_pause_bind:
			self.play_pause()
		
		#Stop video
		elif keycode == stop_bind:
			self.video_stop()
		
		#Close program
		elif keycode == quit_bind:
			print "Close program"
			self.video_stop()
			sys.exit(0)
			
		#Go back 30 seconds
		elif keycode == skip_backward_bind: #W
			print "Go back 30 seconds"
		
			current_time = self.player.get_time() #ms
			current_time = current_time / 1000 #seconds
			
			new_time = current_time - 30
			new_time = new_time * 1000 #back to ms
			
			if new_time < 0:
				self.player.set_time(0)
			else:
				self.player.set_time(new_time)
		
		#Go forward 30 seconds		
		elif keycode == skip_forward_bind: #E
			print "Skip ahead 30 seconds"
			
			current_time = self.player.get_time() #ms
			current_time = current_time / 1000 #seconds
			
			new_time = current_time + 30
			new_time = new_time * 1000 #back to ms
			
			if new_time > self.player.get_length():
				self.play(current_mode, current_channel)
			else:
				self.player.set_time(new_time)
		
		#Displays popup window
		if keycode == info_bind: #I
			self.show_msg(None)
		
		else:
			print "No key binding"
			event.Skip()

			
			
	def on_exit(self, evt):
		"""Closes the window."""
		self.Close()

		
		
	def on_play(self, evt):
		"""Toggle the status to Play/Pause."""		
		if self.player.play() == -1:
			print "Cannot play video"
			self.error_dialog("Unable to play current file")
			
	
			
	def error_dialog(self, errormessage):
		'''Display error message'''
		wx.MessageBox(errormessage, 'Error', 
            wx.OK | wx.ICON_ERROR)
		sys.exit(0)
		
	
	
	def play(self, mode, channel):
		'''Plays a specific mode and channel'''	
		global video_data
		
		try:
			#Pick a random folder in a channel
			random_folder = random.randint(0, len(video_data[mode][channel])-1)
			
			#The path of that folder
			dir_path = video_data[mode][channel][random_folder]

			#Get all sub folders from a channel's folder
			all_folders = [] #All sub folders in a channel's folder
			for f in listdir(dir_path):
				current_path = join(dir_path,f)
				if not isfile(current_path):
					all_folders.append(current_path)
					
			
			all_videos = [] #All videos from the folders
			
			#There are no sub directories, look for video files in dir_path
			#eg Movie folder with just movies
			if len(all_folders) == 0:
				#Get all video files from dir_path
				for video in listdir(dir_path):
					if isfile(join(dir_path,video)):
						all_videos.append(join(dir_path,video))
						#print join(folder,video)
						
			#There are sub directories, scan them
			#eg TV show, so scan the season folders
			else:
				#Get all video files from the above folders
				for folder in all_folders:
					for video in listdir(folder):
						if isfile(join(folder,video)):
							all_videos.append(join(folder,video))
							#print join(folder,video)
			
			#Generate a random number to pick a video file
			random_number = random.randint(0, len(all_videos)-1)
			
			#Grab the random video file
			random_video = all_videos[random_number]
			
			#Play random_video file
			self.Media = self.Instance.media_new(unicode(os.path.join(random_video)))
			try:
				self.player.set_media(self.Media)
			except:
				print "Failed video"
			self.player.set_hwnd(self.videopanel.GetHandle())

			try:
				self.on_play(None) #This also plays a file
			except:
				print "Cannot PLAY"

			
			splitter = random_video.split(os.sep) # Split the path to just get the file name itself
			self.show_msg(mode_names[current_mode] + " - " + channel_names[current_mode][current_channel] + " - " + splitter[len(splitter)-1])
			print random_video
			
		except Exception, e:
			error_msg = str(e)
			print str(e)
			self.error_dialog("channels.xml is not properly constructed")

	def show_msg(self, text_dis):	
		'''Shows the popup window'''
		
		#If a message wasn't sent in, reuse old message
		#Else set the new global message
		if text_dis is not None:
			self.msg_text = text_dis
		
		try:
			self.msg_win.hide()#Hide current msg_win
		except:
			pass
			
		self.msg_win = PopUpWin() #Make a new one
		self.msg_win.set_text(self.msg_text) #Set its text and display
		thread.start_new_thread(hide_msg_thread, (self,self.msg_win)) #Thread to hide
		self.cap_panel.SetFocus() #Return focus to listen to key events
		
		

def hide_msg_thread(main_player, msg_win):
	'''Hides the popup message window'''
	time.sleep(3)
	
	try:
		if msg_win is not None:
			msg_win.hide()
	
	#This seems to happen on a bad file
	except:
		pass
	

if __name__ == "__main__":
	app = wx.App()	
	
	main_player = Player("LaziiTV")
	# show the player window centred and run the application
	main_player.Centre()
	main_player.Show()
	
	app.MainLoop()