# Regenerating the poker data

Not needed to run the app. Only for adding flops or changing ranges/bet sizes.

1. `git clone https://github.com/b-inary/postflop-solver` next to this folder's parent (Cargo.toml points at `../postflop-solver`; adjust the path).
2. `RUSTFLAGS="--cap-lints warn" cargo build --release` in this folder.
3. Write the ranges file `run_all.py` reads (line 1 BTN open, 2 BB vs BTN call, 3 UTG open, 4 BB vs UTG call) in solver syntax (`AKs:0.5,...`), exported from `poker_ranges.py`.
4. `python run_all.py` (about 40 seconds and 1.4GB RAM per flop on 2 cores), then `python pack.py`.
5. `pip install eval7` and `python preflop_equity.py` for the preflop matchups.

Paths at the top of each script are from the machine that built the data; edit them for yours.
