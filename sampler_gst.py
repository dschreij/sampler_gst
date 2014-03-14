#-*- coding:utf-8 -*-

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Daniel Schreij"
__license__ = "GPLv3"

import os
import sys

# Import OpenSesame specific items
from libopensesame import item, debug, generic_response
from libqtopensesame.items.qtautoplugin import qtautoplugin

# The `osexception` class is only available as of OpenSesame 2.8.0. If it is not
# available, fall back to the regular `Exception` class.
try:
	from libopensesame.exceptions import osexception
except:
	osexception = Exception

# Gstreamer components

# If The Gstreamer SDK is found in the plugin folder, add the relevant paths
# so that we use this framework. This is Windows only.
if os.name == "nt":
	if hasattr(sys,"frozen") and sys.frozen in ("windows_exe", "console_exe"):
		exe_path = os.path.dirname(sys.executable)
		os.environ["PATH"] = os.path.join(exe_path, "gstreamer", "dll") + ';' + os.environ["PATH"]
		os.environ["GST_PLUGIN_PATH"] = os.path.join(exe_path, "gstreamer", "plugins")
		sys.path.append(os.path.join(exe_path, "gstreamer", "python"))		
	else:
		os.environ["PATH"] = os.path.join(os.environ["GSTREAMER_SDK_ROOT_X86"],"bin") + ';' + os.environ["PATH"]
		sys.path.append(os.path.join(os.environ["GSTREAMER_SDK_ROOT_X86"],"lib","python2.7","site-packages"))
if os.name == "posix" and sys.platform == "darwin":
	# For OS X
	# When installed with the GStreamer SDK installers from GStreamer.com
	sys.path.append("/Library/Frameworks/GStreamer.framework/Versions/Current/lib/python2.7/site-packages")
		
# Try to load Gstreamer
try:
	import pygst
	pygst.require("0.10")
	import gst
except:
	raise osexception("OpenSesame could not find the GStreamer framework!")

from libqtopensesame.misc import _
from libqtopensesame.items import qtitem
from libqtopensesame.ui import sampler_widget_ui
from libqtopensesame.widgets import pool_widget
from PyQt4 import QtGui

class sampler_gst(item.item, generic_response.generic_response):

	"""Sound playback item"""

	description = u'Plays a sound file in .wav or .ogg format'

	def __init__(self, name, experiment, string = None):

		"""
		Constructor.

		Arguments:
		name 		--	The name of the item.
		experiment 	--	The experiment.

		Keyword arguments:
		string		-- 	The item definition string. (default=None)
		"""

		self.sample = u''
		self.pan = 0
		self.pitch = 1
		self.fade_in = 0
		self.volume = 1.0
		self.stop_after = 0
		self.duration = u'sound'
		self.block = False
		item.item.__init__(self, name, experiment, string)

	def prepare_duration_sound(self):

		"""Sets the duration function for 'sound' duration."""

		self.block = True
		self._duration_func = self.dummy

	def prepare(self):

		"""Prepares for playback."""

		item.item.prepare(self)
		if self.sample.strip() == u'':
			raise osexception( \
				u'No sample has been specified in sampler "%s"' % self.name)
		sample = self.experiment.get_file(self.eval_text(self.sample))
		if debug.enabled:
			self.sampler = openexp.sampler.sampler(self.experiment, sample)
		else:
			try:
				self.sampler = openexp.sampler.sampler(self.experiment, sample)
			except Exception as e:
				raise osexception( \
					u'Failed to load sample in sampler "%s": %s' % (self.name, \
					e))

		pan = self.get(u'pan')
		if pan == -20:
			pan = u'left'
		elif pan == 20:
			pan = u'right'

		self.sampler.pan(pan)
		self.sampler.volume(self.get(u'volume'))
		self.sampler.pitch(self.get(u'pitch'))
		self.sampler.fade_in(self.get(u'fade_in'))
		self.sampler.stop_after(self.get(u'stop_after'))
		generic_response.generic_response.prepare(self)

	def run(self):

		"""Plays the sample."""

		self.set_item_onset(self.time())
		self.set_sri()
		self.sampler.play(self.block)
		self.process_response()

	def var_info(self):

		"""
		Give a list of dictionaries with variable descriptions

		Returns:
		A list of (name, description) tuples
		"""		

		return item.item.var_info(self) + \
			generic_response.generic_response.var_info(self)



class qtsampler_gst(sampler_gst, qtautoplugin):	

	"""GUI controls for the sampler item"""

	def __init__(self, name, experiment, string=None):
	
		"""
		Constructor
		
		Arguments:
		name -- the item name
		experiment -- the experiment
		
		Keywords arguments:
		string -- definition string (default=None)
		"""
		
		qtitem.qtitem.__init__(self)	
		self.lock = False			
				
	def init_edit_widget(self):
	
		"""Build the GUI controls"""
		
		qtitem.qtitem.init_edit_widget(self, False)
				
		self.sampler_widget = QtGui.QWidget()
		self.sampler_widget.ui = sampler_widget_ui.Ui_sampler_widget()
		self.sampler_widget.ui.setupUi(self.sampler_widget)
		self.experiment.main_window.theme.apply_theme(self.sampler_widget)
		
		self.sampler_widget.ui.spin_pan.valueChanged.connect( \
			self.apply_edit_changes)
		self.sampler_widget.ui.spin_volume.valueChanged.connect( \
			self.apply_edit_changes)
		self.sampler_widget.ui.spin_pitch.valueChanged.connect( \
			self.apply_edit_changes)
		self.sampler_widget.ui.spin_stop_after.valueChanged.connect( \
			self.apply_edit_changes)		
		self.sampler_widget.ui.spin_fade_in.valueChanged.connect( \
			self.apply_edit_changes)
		self.sampler_widget.ui.edit_duration.editingFinished.connect( \
			self.apply_edit_changes)		
		self.sampler_widget.ui.edit_sample.editingFinished.connect( \
			self.apply_edit_changes)			
		self.sampler_widget.ui.button_browse_sample.clicked.connect( \
			self.browse_sample)
		self.sampler_widget.ui.dial_pan.valueChanged.connect(self.apply_dials)
		self.sampler_widget.ui.dial_volume.valueChanged.connect( \
			self.apply_dials)
		self.sampler_widget.ui.dial_pitch.valueChanged.connect(self.apply_dials)
							
		self.edit_vbox.addWidget(self.sampler_widget)
		self.edit_vbox.addStretch()
					
	def browse_sample(self):
	
		"""Present a file dialog to browse for the sample"""
		
		s = pool_widget.select_from_pool(self.experiment.main_window)
		if unicode(s) == "":
			return			
		self.sampler_widget.ui.edit_sample.setText(s)
		self.apply_edit_changes()
		
	def edit_widget(self):
	
		"""
		Refresh the GUI controls
		
		Returns:
		A QWidget with the controls
		"""	
		
		self.lock = True		
		qtitem.qtitem.edit_widget(self)						
		if self.variable_vars(["sample", "duration"]):			
			self.user_hint_widget.add_user_hint(_( \
				'The controls are disabled, because one of the settings is defined using variables.'))
			self.user_hint_widget.refresh()
			self.sampler_widget.ui.frame_controls.setVisible(False)			
		else:		
			self.sampler_widget.ui.frame_controls.setVisible(True)					
			self.sampler_widget.ui.edit_sample.setText(self.unistr(self.get( \
				'sample', _eval=False)))
			self.sampler_widget.ui.edit_duration.setText(self.unistr(self.get( \
				'duration', _eval=False)))		
			self.sampler_widget.ui.spin_pan.setValue(self.get('pan', _eval= \
				False))
			self.sampler_widget.ui.spin_volume.setValue(100.0 * self.get( \
				'volume', _eval=False))
			self.sampler_widget.ui.spin_pitch.setValue(100.0 * self.get( \
				'pitch', _eval=False))
			self.sampler_widget.ui.spin_fade_in.setValue(self.get('fade_in', \
				_eval=False))
			self.sampler_widget.ui.spin_stop_after.setValue(self.get( \
				'stop_after', _eval=False))
			self.sampler_widget.ui.dial_pan.setValue(self.get('pan', _eval= \
				False))
			self.sampler_widget.ui.dial_volume.setValue(100.0 * self.get( \
				'volume', _eval=False))
			self.sampler_widget.ui.dial_pitch.setValue(100.0 * self.get( \
				'pitch', _eval=False))
		self.lock = False		
		return self._edit_widget

	def apply_edit_changes(self, dummy1=None, dummy2=None):
	
		"""
		Apply the GUI controls
		
		Keywords arguments:
		dummy1 -- a dummy argument (default=None)
		dummy2 -- a dummy argument (default=None)
		"""	
		
		if not qtitem.qtitem.apply_edit_changes(self, False) or self.lock:
			return		
		self.set("sample", unicode(self.sampler_widget.ui.edit_sample.text()))		
		dur = self.sanitize(self.sampler_widget.ui.edit_duration.text(), \
			strict=True)
		if dur == "":
			dur = "sound"
		self.set("duration", dur)					
		self.set("pan", self.sampler_widget.ui.spin_pan.value())
		self.set("pitch", .01 * self.sampler_widget.ui.spin_pitch.value())
		self.set("volume", .01 * self.sampler_widget.ui.spin_volume.value())
		self.set("fade_in", self.sampler_widget.ui.spin_fade_in.value())
		self.set("stop_after", self.sampler_widget.ui.spin_stop_after.value())
		
		self.experiment.main_window.refresh(self.name)			
						
	def apply_dials(self, dummy=None):
	
		"""
		Set the spinbox values based on the dials
		
		Keywords arguments:
		dummy -- a dummy argument (default=None)
		"""
		
		if self.lock:
			return
		self.set("pan", self.sampler_widget.ui.dial_pan.value())
		self.set("pitch", .01 * self.sampler_widget.ui.dial_pitch.value())
		self.set("volume", .01 * self.sampler_widget.ui.dial_volume.value())		
		self.edit_widget()
