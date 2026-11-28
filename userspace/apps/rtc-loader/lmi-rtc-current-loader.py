#!/usr/bin/env python3
"""Load the tested RTC only with the expected kernel and synchronized time."""
import hashlib
import os
from pathlib import Path
import subprocess
import time

module = Path('/usr/local/lib/lmi-rtc/rtc-pm8xxx.ko')
expected = '73bc870ded5a61e6c0d382cb73c6bb0a3e55b25fd01db4df253a2ee338958b49'
kernel = 'kernel_sha=a7c53444cda24011a821031829219056e5d948b55536a0e6e3d0734baa3264b7'
if kernel not in Path('/proc/cmdline').read_text().split():
    raise SystemExit('Unexpected kernel; RTC module not loaded')
if hashlib.sha256(module.read_bytes()).hexdigest() != expected:
    raise SystemExit('RTC module checksum mismatch')
if Path('/sys/module/rtc_pm8xxx').exists():
    print('RTC module already loaded')
    raise SystemExit(0)
if list(Path('/sys/class/rtc').iterdir()):
    raise SystemExit('Another RTC already exists')
ntp = subprocess.check_output(['timedatectl', 'show', '-p', 'NTPSynchronized', '--value'], text=True).strip()
if ntp != 'yes' or time.time() < 1577836800:
    raise SystemExit('Waiting for synchronized system time')
fd = os.open('/sys/kernel/debug/regmap/0-00/registers', os.O_RDONLY | os.O_CLOEXEC)
try:
    rtc = os.pread(fd, 9, 0x6046 * 9).decode().strip()
    alarm = os.pread(fd, 9, 0x6146 * 9).decode().strip()
finally:
    os.close(fd)
if rtc != '6046: 80' or alarm != '6146: 00':
    raise SystemExit(f'Unexpected RTC state: {rtc}, {alarm}')
subprocess.run(['/sbin/insmod', str(module)], check=True)
rtc_time = int(Path('/sys/class/rtc/rtc0/since_epoch').read_text())
if abs(rtc_time - time.time()) > 5:
    raise SystemExit('RTC time differs from system time')
print('RTC loaded and time checked')
