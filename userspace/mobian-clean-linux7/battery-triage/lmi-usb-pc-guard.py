#!/usr/bin/env python3
"""Keep logind awake only while an externally powered USB gadget is active."""
import logging
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

INTERVAL = 3
REQUIRED_POSITIVES = 2
MIN_VBUS_UV = 4_000_000
SYS = Path('/sys')


def notify(message):
    address = os.environ.get('NOTIFY_SOCKET')
    if not address:
        return
    if address.startswith('@'):
        address = '\0' + address[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(address)
            sock.sendall(message.encode('ascii'))
    except OSError as exc:
        logging.error('systemd notification failed: %s', exc)


def read(path):
    try:
        return path.read_text(encoding='ascii').strip()
    except (OSError, UnicodeError):
        return None


def qualifies(values):
    try:
        vbus = int(values.get('vbus') or '')
    except (TypeError, ValueError):
        return False
    return (values.get('online') == '1' and values.get('udc') == 'configured'
            and values.get('carrier') == '1' and values.get('partner') is True
            and vbus >= MIN_VBUS_UV)


def snapshot(root=SYS, held=False):
    values = {
        'online': read(root / 'class/power_supply/pm8150b-charger/online'),
        'udc': read(root / 'class/udc/a600000.usb/state'),
        'carrier': read(root / 'class/net/usb0/carrier'),
        'partner': (root / 'class/typec/port0-partner').exists(),
    }
    candidate = (values['online'] == '1' and values['udc'] == 'configured'
                 and values['carrier'] == '1' and values['partner'])
    values['vbus'] = (read(root / 'bus/iio/devices/iio:device1/in_voltage_usbin_v_input')
                      if candidate or held else None)
    values['vbus_skipped'] = not (candidate or held)
    return values


class Guard:
    def __init__(self):
        self.child = None
        self.positives = 0

    def release(self):
        child, self.child = self.child, None
        if child is None:
            return
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        logging.info('USB maintenance sleep inhibition released')

    def update(self, valid):
        if not valid:
            self.positives = 0
            self.release()
            return
        self.positives = min(self.positives + 1, REQUIRED_POSITIVES)
        if self.child is not None and self.child.poll() is not None:
            logging.warning('USB maintenance inhibitor exited; retrying')
            self.child = None
        if self.child is None and self.positives >= REQUIRED_POSITIVES:
            self.child = subprocess.Popen([
                '/usr/bin/systemd-inhibit', '--what=sleep', '--mode=block',
                '--who=lmi-usb-pc-guard', '--why=USB maintenance connection',
                '/usr/bin/sleep', 'infinity',
            ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            logging.info('USB maintenance sleep inhibitor starting')


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    guard = Guard()
    ready = False
    try:
        while not stopping:
            values = snapshot(held=guard.child is not None)
            valid = qualifies(values)
            if guard.child is not None and not valid:
                logging.info('USB signals at release: %s', values)
            guard.update(valid)
            if not ready:
                notify('READY=1')
                ready = True
            notify('WATCHDOG=1')
            time.sleep(INTERVAL)
    finally:
        guard.release()


if __name__ == '__main__':
    main()
