#!/usr/bin/python3
"""Explicitly started user recorder. No suspend calls, alarms, inhibitors or media."""
import fcntl, json, os, signal, sys, uuid
from pathlib import Path
from model import STATE, snapshot

def main():
    if sys.argv[1:]==['--once']:
        print(json.dumps(snapshot()));return
    if sys.argv[1:]!=['--run']:raise SystemExit('Use --run or --once')
    import gi
    gi.require_version('Gio','2.0')
    from gi.repository import Gio,GLib
    os.umask(0o077);STATE.mkdir(parents=True,exist_ok=True)
    lock=(STATE/'recorder.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    folder=STATE/'sessions';folder.mkdir(exist_ok=True)
    session=folder/(uuid.uuid4().hex+'.jsonl');output=session.open('x')
    loop=GLib.MainLoop();bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
    try:screenbus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
    except Exception:screenbus=None
    def record(event,active=True,**extra):
        row=snapshot(event);row.update(extra);output.write(json.dumps(row)+'\n');output.flush()
        state={'active':active,'pid':os.getpid(),'session':session.name,'last_epoch':row['epoch'],'interval_seconds':60}
        temp=STATE/'status.tmp';temp.write_text(json.dumps(state));temp.replace(STATE/'status.json')
    def pm(conn,sender,path,iface,name,params,data):
        record('prepare-sleep' if params.unpack()[0] else 'resume-signal')
    def screen(conn,sender,path,iface,name,params,data):record('screen-signal',signal=name,values=params.unpack())
    bus.signal_subscribe('org.freedesktop.login1','org.freedesktop.login1.Manager','PrepareForSleep','/org/freedesktop/login1',None,Gio.DBusSignalFlags.NONE,pm,None)
    if screenbus:
        for name in ('ActiveChanged','WakeUpScreen'):
            screenbus.signal_subscribe('org.gnome.ScreenSaver','org.gnome.ScreenSaver',name,'/org/gnome/ScreenSaver',None,Gio.DBusSignalFlags.NONE,screen,None)
    def sample():record('sample');return True
    def stop():loop.quit();return False
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,stop)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGINT,stop)
    # A GLib timer does not wake a suspended system. There is no WakeSystem timer.
    GLib.timeout_add_seconds(60,sample)
    record('started',kernel=Path('/proc/version').read_text().strip(),limits='Counter estimates are differently modelled; no per-app power attribution. No wake alarm, inhibitor or power policy changes.')
    try:loop.run()
    finally:record('stopped',active=False);output.close();lock.close()

if __name__=='__main__':main()
