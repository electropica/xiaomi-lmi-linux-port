# L1 charger-inhibition pilot — 17 November 2026

The handset began at 76%, `Charging`, with PM8150B register 0x1042 read as `0x01`. A separately verified monotonic recovery timer and sleep inhibitor were active before the one-minute pilot. Only the `charge_behaviour` interface was written; neither `current_max` nor a raw register was written.

During the pilot, the register read `0x00`, USB input remained online, battery status was `Not charging`, and the mean of ten 5-second samples after the first ten seconds was approximately -3.32 mA. This was not a valid L1 phase under the requested strict `Discharging` criterion. Input online and near-zero battery current do not independently quantify external USB power. The screen/radio/thermal conditions and short duration do not support a direct numerical comparison with a 15-minute physically disconnected reference.

After requesting recovery, the register returned to `0x01`; the first status was still `Not charging`, so the safety guards were retained. Five seconds later the register remained `0x01` and status was `Charging`. Only then were the timer and sleep inhibitor stopped. A subsequent read showed positive battery current. The raw value was checked at 0x1042; this is not a proof that every hardware register was restored.

The pilot log and baseline were copied to private local evidence with matching SHA-256 hashes. No L1/L2 15-minute comparison or L2 data-cut test was performed.
