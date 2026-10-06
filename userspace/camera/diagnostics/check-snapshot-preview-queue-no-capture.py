import gi,os
gi.require_version('Gst','1.0')
from gi.repository import Gst,GObject
Gst.init(None)
import ctypes
ptr=ctypes.pythonapi.PyCapsule_GetPointer
ptr.restype=ctypes.c_void_p;ptr.argtypes=[ctypes.py_object,ctypes.c_char_p]
add=ctypes.CDLL(None).gst_bin_add
add.argtypes=[ctypes.c_void_p,ctypes.c_void_p];add.restype=ctypes.c_int
def attach(parent,child):
 assert add(ptr(parent.__gpointer__,None),ptr(child.__gpointer__,None))
class PreviewBin(Gst.Bin):
 __gtype_name__='AperturePipelineTee'
GObject.type_register(PreviewBin)
parent=PreviewBin(); q=Gst.ElementFactory.make('queue');attach(parent,q)
a=tuple(q.get_property(k) for k in ('max-size-buffers','max-size-bytes','max-size-time','leaky'))
ordinary=Gst.Bin.new('ordinary'); other=Gst.ElementFactory.make('queue');attach(ordinary,other)
b=tuple(other.get_property(k) for k in ('max-size-buffers','max-size-bytes','max-size-time','leaky'))
print('PREVIEW_QUEUE',a,'ORDINARY_QUEUE',b,flush=True)
if os.environ.get('LMI_PREVIEW_QUEUE_TRIAL')=='1':
 assert a==(1,0,0,2),a
 assert b==(200,10485760,1000000000,0),b
else: assert a==b
print('SCOPE_CHECK_OK_NO_PIPELINE_STARTED',flush=True)
