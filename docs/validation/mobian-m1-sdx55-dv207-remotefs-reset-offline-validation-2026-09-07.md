# Mobian M1 SDX55 DV207 remotefs RESET offline validation — 2026-09-07

## Scope

This note records the static and offline validation work performed after the nominal SDX55 ESOC and mission-mode milestone.

The objective was to determine how the Qualcomm remote-filesystem Sahara path should terminate, while preserving a strict write-none property on the AP side.

No phone interaction was performed for DV207.

This milestone does not authorize a real MHI probe and does not claim cellular registration, voice, SMS or packet data.

## Historical remotefs failure

The SDX55 firmware crash history contained:

```text
ssr:AP:remotefs_sahara.c:850:
Assertion remotefs_sahara_info.sahara_status == SAHARA_END_OF_IMG_TRANSFER failed
```

Static analysis of the exact Xiaomi SDX55 `apps.mbn` established that this assertion belongs to Qualcomm's firmware-side:

```text
apps_proc/core/storage/remotefs/src/remotefs_sahara.c
```

The exact firmware also contains diagnostics for:

```text
SAHARA_READY
SAHARA_MEM_DBG_START
SAHARA_MEM_DBG
SAHARA_CMD_EXEC_READY
SAHARA_END_OF_IMG_TRANSFER
```

and terminal diagnostics including:

```text
remotefs_sahara.c:mem_dbg_core: Done. Reset received. Status %d
remotefs_sahara.c:reset_resp: remotefs_sio_tx failed %d
remotefs_sahara.c:end_of_transfer: remotefs_sio_tx failed %d
```

This established that the remotefs Sahara state machine distinguishes image transfer completion, end-of-transfer processing and RESET response handling.

## Exact Xiaomi ks audit

The exact Xiaomi `/vendor/bin/ks` was extracted offline from:

```text
lmi_global_images_V14.0.1.0.SJKMIXM_20230317.0000.00_12.0_global
```

Identity:

```text
SIZE=42024
SHA256=fe613f93096d42b71a6ed9b8b1929a84592e6a44157383ddfe75d153d69cdb80
BUILD_ID=d65b613adf8f78e85a64354504131d6d
ARCH=AARCH64
ANDROID_API_LEVEL=30
```

The helper invocation historically used for EFS synchronization is:

```text
/vendor/bin/ks
-m
-p /dev/mhi_0306_02.01.00_pipe_10
-w /dev/block/bootdevice/by-name/
-t -1
-l
-g mdm1
```

Static analysis proved that this invocation receives modem memory regions and writes them to destinations derived from:

```text
path_to_save_files
+
saved_file_prefix
+
filename supplied by the modem
```

With the lmi configuration this can address:

```text
/dev/block/bootdevice/by-name/mdm1m9kefs1
/dev/block/bootdevice/by-name/mdm1m9kefs2
/dev/block/bootdevice/by-name/mdm1m9kefs3
```

The exact binary performs open, write, fsync and close operations on the received data.

Therefore the historical Qualcomm EFS invocation is not a read-only operation and was not executed during this investigation.

## Why table-only termination was rejected

A first offline design considered requesting only the Sahara memory-debug table and then closing the transport.

Static firmware analysis showed that this would stop the session before the firmware reaches its expected `SAHARA_END_OF_IMG_TRANSFER`.

No source or static control flow demonstrated that closing the transport after receiving only the table constitutes a successful Sahara termination.

The table-only strategy was therefore rejected.

## Consume-all write-none design

DV196 introduced a pure in-memory Sahara model that:

```text
HELLO
→ HELLO_RESPONSE memory-debug
→ MEMORY_DEBUG
→ MEMORY_READ table
→ parse table
→ MEMORY_READ every region
→ consume every byte
→ discard received data
→ TRANSFER_COMPLETE
```

The implementation has no filesystem, device or MHI transport capability. It contains no open/openat/fopen/write/pwrite/fwrite/fsync/ioctl operations, no `/dev/mhi` path, no `by-name` path and no `mdm1m9kefs` destination.

Region bytes are used only for exact coverage accounting and a volatile digest before being discarded.

DV196 validated this model offline with:

```text
TEST_COUNT=170
FAILURE_COUNT=0
SYNTHETIC_TESTS=PASS
```

However, DV196 deliberately omitted RESET.

## Why close without RESET was rejected

DV198 through DV205 statically traced the firmware-side SIO layer and the AP-side Linux MHI path.

The firmware remotefs receive function waits only for `RX_DATA=0x00040000` and `TIMEOUT=0x00020000`. An auxiliary MHI control-state callback can produce `0x00080000`, but this bit is not consumed by `remotefs_sio_rx`.

The AP-side EFS device is handled by `mhi_uci`. The final Linux close path performs:

```text
mhi_uci_release
→ mhi_unprepare_from_transfer
→ channel reset and queue cleanup
```

Static analysis found no automatic generation of a `"CTRL"` destination `0x0a` state message from open, release, unprepare, reset or link-down. The only AP-side producer of the relevant `"CTRL"` message is the explicit `TIOCMSET` path through `mhi_dtr_tiocmset`.

Therefore `consume-all → close without RESET` has no demonstrated path to a successful remotefs Sahara completion. It remains unsuitable for a real probe.

## DV207 RESET extension

DV207 was created as an isolated extension of DV196. The original DV196 files were not modified.

DV207 adds only:

```text
SC_WAIT_RESET_RESP
SC_PROTOCOL_COMPLETE
SAHARA_RESET=0x07
SAHARA_RESET_RESP=0x08
sc_build_reset()
sc_receive_reset_resp()
sc_protocol_finish()
```

The earlier HELLO, memory-debug, table validation, region parsing and consumption code remains unchanged.

The terminal state machine is:

```text
SC_TRANSFER_COMPLETE
→ build SAHARA_RESET
→ SC_WAIT_RESET_RESP
→ validate SAHARA_RESET_RESP
→ SC_PROTOCOL_COMPLETE
```

`sc_build_reset()` refuses to construct RESET unless `state == SC_TRANSFER_COMPLETE`, `current_region == region_count` and `total_consumed == total_expected`.

The generated RESET packet is exactly command `0x07`, length `8`.

`sc_receive_reset_resp()` accepts only state `SC_WAIT_RESET_RESP`, size `8`, command `0x08`, length `8`. Any mismatch moves the model to `SC_FAILED`.

Only `sc_build_reset()` can enter `SC_WAIT_RESET_RESP`. Only `sc_receive_reset_resp()` can enter `SC_PROTOCOL_COMPLETE`. No generic opcode constructor exists.

## Reference cross-check

The local QDL Sahara implementation independently defines:

```text
SAHARA_RESET_CMD=0x07
SAHARA_RESET_RESP_CMD=0x08
SAHARA_RESET_LENGTH=0x08
```

The exact Xiaomi `ks` binary contains the direct strings:

```text
SENDING --> SAHARA_RESET
STATE <-- SAHARA_WAIT_RESET_RESP
RECEIVED <-- SAHARA_RESET_RESP
```

It also contains:

```text
-n
--noreset
Disable sending the sahara reset PKT
Skipping SAHARA_WAIT_RESET_RESP
Sending sahara reset pkt disabled by '-n or --noreset'
```

This confirms that RESET followed by RESET_RESP is the normal terminal path, while no-reset is an explicit alternate behavior.

The exact SDX55 firmware independently contains:

```text
Assertion remotefs_sahara_info.sahara_status == SAHARA_END_OF_IMG_TRANSFER failed
remotefs_sahara.c:mem_dbg_core: Done. Reset received. Status %d
remotefs_sahara.c:reset_resp: remotefs_sio_tx failed %d
remotefs_sahara.c:end_of_transfer: remotefs_sio_tx failed %d
```

These sources are consistent with the DV207 terminal model.

## Synthetic validation

The DV207 nominal path was tested for both Sahara table formats.

```text
COMPLETE_BITS=32 TRANSFER_COMPLETE=YES PROTOCOL_RESET_COMPLETE=YES DIGEST=eb6c7f9cd19bf634
COMPLETE_BITS=64 TRANSFER_COMPLETE=YES PROTOCOL_RESET_COMPLETE=YES DIGEST=eb6c7f9cd19bf634
TEST_COUNT=302
FAILURE_COUNT=0
SYNTHETIC_TESTS=PASS
```

The suite covers the pre-existing DV196 cases and additional RESET cases, including RESET before any region, RESET between regions, RESET in the middle of a region, RESET_RESP before RESET, wrong RESET_RESP command, wrong RESET_RESP length, duplicate RESET_RESP, data after transfer completion and data after protocol completion.

The RESET test suite is invoked directly from `main()`.

## Sanitizer validation

DV207 was rebuilt with:

```text
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer
```

with leak detection disabled for the sanitizer run because the environment is not suitable for ASan leak checking.

The result remained:

```text
COMPLETE_BITS=32 TRANSFER_COMPLETE=YES PROTOCOL_RESET_COMPLETE=YES DIGEST=eb6c7f9cd19bf634
COMPLETE_BITS=64 TRANSFER_COMPLETE=YES PROTOCOL_RESET_COMPLETE=YES DIGEST=eb6c7f9cd19bf634
TEST_COUNT=302
FAILURE_COUNT=0
SYNTHETIC_TESTS=PASS
```

Compiler identity:

```text
cc (Ubuntu 15.2.0-16ubuntu1) 15.2.0
```

## Frozen DV207 identities

Sources:

```text
sahara_consume.c
SHA256=92fc08e0cda62ba6480246bf9ce8dfa3a57797ded78a7b47da518176231bdb53

sahara_consume.h
SHA256=8ef0dac9135325ba2f25f4d47e224067dfe96445c918b593d5f625f1ac09f521

test_sahara_consume.c
SHA256=58c89b501ebf6b8f6f08329bf8f29d572f3baf7f62d4edaf32fb9086d89e0947
```

Validated executables:

```text
test_sahara_consume
SHA256=92d221926391a69843217eaaa48a2d6019b59298b364a3edba69fb19b5ba6337

test_sahara_consume_asan
SHA256=89fa66d87aef1b27614dc7880b0e59e13da5ba298a0738e6fdd81279da529867
```

The source hashes were checked again after the sanitizer run and were unchanged.

## Validation boundary

DV207 validates offline that:

- all declared EFS regions can be consumed without filesystem writes;
- RESET cannot be constructed before exact transfer completion;
- RESET has command `0x07` and length `8`;
- RESET_RESP must have command `0x08` and length `8`;
- protocol completion is distinct from image-transfer completion;
- no alternate path can directly enter the RESET-wait or protocol-complete states;
- the extension is isolated from the historical DV196 parsing and consumption logic;
- the complete synthetic path passes 290 tests in normal and sanitizer builds.

DV207 does not validate:

- opening the real MHI EFS endpoint;
- framing boundaries on the real transport;
- interaction with a live SDX55 remotefs session;
- the runtime effect of RESET on the modem;
- EFS persistence semantics during a write-none session;
- ESOC notification timing after EFS synchronization;
- cellular registration, voice, SMS or packet data.

No real probe is authorized by this milestone.

```text
REAL_PROBE=NOT_SAFE
```

## Result marker

```text
DV207_CONSUME_ALL_WRITE_NONE_RESET_OFFLINE_VALIDATION=COMPLETE
PHONE_ACCESSED=NO
REAL_MHI_PORT_OPENED=NO
REAL_MHI_PACKET_SENT=NO
REAL_SAHARA_PACKET_SENT=NO
QMI_MESSAGE_SENT=NO
ESOC_NOTIFICATION_SENT=NO
MODEM_RESET_REQUESTED=NO
KS_EXECUTED=NO
EFS_PARTITION_WRITTEN=NO
PRODUCTION_SOURCE_MODIFIED=NO
PHONE_BUILD_STARTED=NO
DV196_CORE_PRESERVED=YES
WRITE_NONE_STRUCTURAL=YES
RESET_PATH_PRESENT=YES
RESET_BEFORE_TRANSFER_COMPLETE=REJECTED
RESET_RESP_VALIDATION=STRICT
TRANSFER_COMPLETION_VALIDATED=YES
PROTOCOL_RESET_COMPLETION_VALIDATED=YES
SYNTHETIC_TEST_COUNT=302
SYNTHETIC_FAILURE_COUNT=0
SYNTHETIC_TESTS=PASS
ASAN_UBSAN=PASS
REAL_PROBE=NOT_SAFE
DECISION=OFFLINE_RESET_MODEL_VALIDATED
```

## Next step

Before any real MHI adaptation, perform a final static review of the host-side transport adapter requirements for DV207, including exact read boundaries, partial-read handling, timeout policy and lifecycle behavior, while preserving the structural write-none property and without accessing the phone.
