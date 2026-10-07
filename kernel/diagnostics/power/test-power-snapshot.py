#!/usr/bin/env python3
"""Fixture-only tests: no device, services or privileged filesystem reads."""
import gzip
import hashlib
import importlib.util
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('reader', Path(__file__).with_name('read-power-snapshot.py'))
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
with tempfile.TemporaryDirectory(prefix='lmi-power-snapshot-test-') as tmp:
    root = Path(tmp)
    battery = root / 'sys/class/power_supply/battery'
    battery.mkdir(parents=True)
    (battery / 'capacity').write_text('88\n')
    (battery / 'current_now').write_text('-698241\n')
    (battery / 'charge_counter').write_text('2273114\n')
    (battery / 'status').write_text('Charging\n')
    (battery / 'temp').write_text('not a number\n')
    (root / 'proc').mkdir()
    config = b'CONFIG_DEBUG_FS=y\nCONFIG_CPU_IDLE=y\n'
    (root / 'proc/config.gz').write_bytes(gzip.compress(config))
    result = reader.snapshot(root)
    assert result['supplies']['battery']['capacity_pct'] == 88
    assert result['supplies']['battery']['current_now_uA'] == -698241
    assert result['supplies']['battery']['charge_counter_uAh'] == 2273114
    assert result['supplies']['battery']['status'] == 'Charging'
    assert result['supplies']['battery']['temperature_deciC']['unavailable'] == 'invalid_integer'
    assert result['supplies']['usb']['online']['unavailable'] == 'FileNotFoundError'
    assert result['ikconfig']['sha256'] == hashlib.sha256(config).hexdigest()
    (root / 'proc/config.gz').write_bytes(b'broken gzip')
    assert reader.config_identity(root)['unavailable'] == 'invalid_gzip'
    (root / 'proc/config.gz').write_bytes(b'\x1f\x8b\x08\x00' + b'\x00' * 6 + b'\x07' + b'\x00' * 8)
    assert reader.config_identity(root)['unavailable'] == 'invalid_gzip'
    (root / 'proc/config.gz').write_bytes(gzip.compress(b''))
    assert reader.config_identity(root)['unavailable'] == 'empty_config'
    (root / 'proc/config.gz').write_bytes(gzip.compress(b'x' * (4 * 1024 * 1024 + 1)))
    assert reader.config_identity(root)['unavailable'] == 'expanded_size_limit'
    oversized = root / 'oversized'
    oversized.write_bytes(b'x' * 4097)
    assert reader.read_bytes(oversized)['unavailable'] == 'size_limit'
    print('PASS: signed units, missing/invalid fields, config identity and bounded decompression')
