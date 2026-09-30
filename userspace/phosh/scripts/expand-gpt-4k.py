#!/usr/bin/env python3
import binascii
import struct
import sys

path, start_arg, blocks_arg = sys.argv[1:]
sector = 4096
root_start = int(start_arg)
root_blocks = int(blocks_arg)

with open(path, "r+b") as image:
    image.seek(0, 2)
    final_lba = image.tell() // sector - 1
    image.seek(sector)
    original = bytearray(image.read(92))
    if original[:8] != b"EFI PART":
        raise SystemExit("invalid primary GPT signature")
    header_size = struct.unpack_from("<I", original, 12)[0]
    entries_lba = struct.unpack_from("<Q", original, 72)[0]
    entry_count, entry_size = struct.unpack_from("<II", original, 80)
    entries_bytes = entry_count * entry_size
    entries_sectors = (entries_bytes + sector - 1) // sector
    image.seek(entries_lba * sector)
    entries = bytearray(image.read(entries_bytes))
    second = entry_size
    struct.pack_into("<QQ", entries, second + 32, root_start, root_start + root_blocks - 1)
    entries_crc = binascii.crc32(entries) & 0xFFFFFFFF
    last_usable = final_lba - entries_sectors - 1

    def header(current, backup, table_lba):
        out = bytearray(original[:header_size])
        struct.pack_into("<QQ", out, 24, current, backup)
        struct.pack_into("<Q", out, 48, last_usable)
        struct.pack_into("<Q", out, 72, table_lba)
        struct.pack_into("<I", out, 88, entries_crc)
        struct.pack_into("<I", out, 16, 0)
        struct.pack_into("<I", out, 16, binascii.crc32(out) & 0xFFFFFFFF)
        return out

    backup_table_lba = final_lba - entries_sectors
    image.seek(446 + 12)
    image.write(struct.pack("<I", min(final_lba, 0xFFFFFFFF)))
    image.seek(entries_lba * sector)
    image.write(entries)
    image.seek(sector)
    image.write(header(1, final_lba, entries_lba))
    image.seek(backup_table_lba * sector)
    image.write(entries)
    image.seek(final_lba * sector)
    image.write(header(final_lba, 1, backup_table_lba))
