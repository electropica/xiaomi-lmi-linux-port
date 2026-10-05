# Preview publication telemetry only; this observer never starts acquisition.
import json,time,statistics
from pathlib import Path
p=Path('/run/lmi-camera/live.json');points=[];previous=None;deadline=time.monotonic()+50
while time.monotonic()<deadline:
 try:
  obj=json.loads(p.read_text())
  if obj.get('ended'):break
  seq=obj.get('sequence')
  if isinstance(seq,int) and seq!=previous:
   points.append((time.monotonic(),seq));previous=seq
 except (OSError,ValueError):pass
 time.sleep(.01)
if len(points)>2:
 gaps=[(b[0]-a[0])*1000 for a,b in zip(points,points[1:])]
 gaps.sort();elapsed=points[-1][0]-points[0][0];delta=points[-1][1]-points[0][1]
 print('ROOT_PUBLICATION_RATE',delta/elapsed,'SECONDS',elapsed,'FRAMES',delta)
 print('OBSERVED_UPDATE_GAP_MS mean=%.2f p95=%.2f max=%.2f'%(statistics.mean(gaps),gaps[int(.95*(len(gaps)-1))],max(gaps)))
else:print('INSUFFICIENT_PREVIEW_UPDATES',len(points))
