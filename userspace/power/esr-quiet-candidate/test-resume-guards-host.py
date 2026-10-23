"""Differential qualification-helper matrix. No package build, D-Bus or phone."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,tempfile

TASK=Path(__file__).resolve().parent
ROOT=Path('/home/linuxagent/phosh-gauge-wake-build/rootfs/build')
manifest=json.loads((TASK/'identity.json').read_text())

def extract(text,name):
 at=text.index('\n'+name+' (');start=text.rfind('static ',0,at);brace=text.index('{',at);level=0
 for pos in range(brace,len(text)):
  if text[pos]=='{':level+=1
  elif text[pos]=='}':
   level-=1
   if not level:return text[start:pos+1]+'\n'
 raise ValueError(name)

PREFIX=r'''
#include <glib.h>
static const char *capacity="65\n", *status="Discharging\n";
static gboolean fail_read;
static gboolean fixture_read(const gchar *path,gchar **out,gsize *length,GError **error){
 const char *s;
 if(fail_read)return FALSE;
 if(g_str_has_suffix(path,"/capacity"))s=capacity;
 else if(g_str_has_suffix(path,"/status"))s=status;
 else return FALSE;
 *out=g_strdup(s);if(length)*length=strlen(s);return TRUE;
}
#define g_file_get_contents fixture_read
'''

MAIN=r'''
int main(void){
 const char *reasons[]={"438 msoc-delta","441 msoc-high","445 esr-delta",
 "445 esr-delta+438 msoc-delta","311 pon_kpdpwr_status","323 pm8xxx_rtc_alarm","",NULL};
 const char *usb[]={"0","1","0\n","",NULL};
 gint64 gaps[]={-1,0,1,49999,50000,50001,1000000};
 const char *caps[]={"65\n","29\n","30\n","100\n","101\n","invalid\n","65\n","65\n","65\n","-1\n"};
 const char *states[]={"Discharging\n","Discharging\n","Discharging\n","Discharging\n","Discharging\n","Discharging\n","Charging\n","Unknown\n","Discharging\n","Discharging\n"};
 guint64 cases=0,esr_allowed=0;
 capacity="65\n";status="Discharging\n";fail_read=FALSE;
 g_assert_false(old_call(ALL_BITS,1000000,"445 esr-delta","0"));
 g_assert_true(new_call(ALL_BITS,1000000,"445 esr-delta","0"));
 for(guint f=0;f<G_N_ELEMENTS(caps);f++){
  capacity=caps[f];status=states[f];fail_read=(f==8);
  for(guint mask=0;mask<=ALL_BITS;mask++)
   for(guint g=0;g<G_N_ELEMENTS(gaps);g++)
    for(guint r=0;r<G_N_ELEMENTS(reasons);r++)
     for(guint u=0;u<G_N_ELEMENTS(usb);u++){
      gboolean before=old_call(mask,gaps[g],reasons[r],usb[u]);
      gboolean after=new_call(mask,gaps[g],reasons[r],usb[u]);
      if(g_strcmp0(reasons[r],"445 esr-delta")==0){
       g_assert_false(before);
       /* Reuse the existing guarded441 semantics, not a duplicated predicate. */
       g_assert_cmpint(after,==,old_call(mask,gaps[g],"441 msoc-high",usb[u]));
       if(after)esr_allowed++;
      }else g_assert_cmpint(after,==,before);
      cases++;
     }
 }
 g_print("{\"cases\":%"G_GUINT64_FORMAT",\"esr_allowed_cases\":%"G_GUINT64_FORMAT",\"result\":\"PASS\"}\n",cases,esr_allowed);
 return 0;
}
'''

reports=[]
with tempfile.TemporaryDirectory(prefix='lmi-esr-guard-matrix-') as td:
 tmp=Path(td);before=tmp/'before';after=tmp/'after'
 for spec in manifest['sources']:
  raw=(ROOT/spec['tree']/spec['file']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==spec['before'],'Run before modifying package sources'
  for tree in (before,after):
   p=tree/spec['file'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(TASK/'esr-delta-accept.patch')],cwd=after,check=True)
 for spec in manifest['sources']:
  phosh=spec['package']=='phosh';name='lmi_gauge_resume_matches' if phosh else 'lmi_quiet_resume_matches'
  code=PREFIX
  for tree,prefix in ((before,'old'),(after,'new')):
   text=(tree/spec['file']).read_text()
   functions=extract(text,'lmi_quiet_reason_allowed')+extract(text,name)
   code+=functions.replace('lmi_quiet_reason_allowed',prefix+'_reason').replace(name,prefix+'_matches')
   if phosh:
    args='!!(m&1),!!(m&2),!!(m&4),!!(m&8),100000,100000+d,r,u'
   else:
    args='!!(m&1),!!(m&2),!!(m&4),!(m&8),!!(m&16),!!(m&32),!!(m&64),100000,100000+d,r,u'
   code+='static gboolean '+prefix+'_call(guint m,gint64 d,const char*r,const char*u){return '+prefix+'_matches('+args+');}\n'
  code+='#define ALL_BITS '+('15' if phosh else '127')+'\n'+MAIN
  cfile=tmp/(spec['package']+'.c');binary=tmp/(spec['package']+'-guards');cfile.write_text(code)
  flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','glib-2.0'],text=True))
  subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(cfile),'-o',str(binary),*flags],check=True,timeout=30)
  result=json.loads(subprocess.check_output([str(binary)],text=True,timeout=30));result['component']=spec['package']
  reports.append(result)
record={'checks':reports,'result':'PASS','total_cases':sum(r['cases'] for r in reports),
 'scope':'Extracted reason and qualification helpers with isolated sysfs fixtures; no D-Bus/event-loop/package/device validation',
 'phone_contact':False,'package_build':False}
(TASK/'resume-guard-checks.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
