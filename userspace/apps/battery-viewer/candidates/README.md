# One-hour view and multiple sleep boundaries

`sleep-1h-20261127.patch` is a candidate against the repository's viewer 0.1.13. It adds a one-hour period, displays multiple complete sleep boundary pairs and avoids drawing interpolated lines through recorded sleep. It has added Rust tests but was not built or installed at the time of publication. The handset was running viewer 0.1.10; a matching 0.1.10 package was retained for rollback. Apply and review the patch in a disposable checkout, run the tests and validate the small-screen layout before deploying a separately versioned package.
