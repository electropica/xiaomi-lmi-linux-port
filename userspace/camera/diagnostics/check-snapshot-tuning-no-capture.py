import gi
gi.require_version('Gst','1.0');from gi.repository import Gst
Gst.init(None)
a=Gst.ElementFactory.make('pulsesrc');print('PULSE',a.get_property('latency-time'),a.get_property('buffer-time'))
v=Gst.ElementFactory.make('pipewiresrc');print('VIDEO',v.get_property('use-bufferpool'),v.get_property('do-timestamp'))
c=Gst.ElementFactory.make('camerabin');print('CAPS',c.get_property('audio-capture-caps').to_string());print('CLOCK',c.get_pipeline_clock().get_name())
e=Gst.ElementFactory.make('vp8enc');print('VP8',e.get_property('target-bitrate'),e.get_property('deadline'),e.get_property('threads'));print('NO_PIPELINE_STARTED')
