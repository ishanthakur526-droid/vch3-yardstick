# Yardstick

**A stock and ordering planner that runs on what the site actually uses.**

Built in one day at Vibe Coders Hackathon 3 (Kolkata, 21 Nov 2026) for Lumino Industries' problem statement **"1,700 Poles"**: a fixed supply plan kept sending material while the site used far less, and the surplus sat idle in a yard.

On Lumino's real project data (Kanpur, Mar 2023 to Oct 2026, 16 items, 6 godowns, 2.3 lakh stock movements) Yardstick shows what happened, replays the project month by month with a planner that only sees the past, and compares the two honestly.

## The three jobs from the brief

| Job | Screen | What it does |
|---|---|---|
| 1. See it | **See it** | For every item and godown, month by month: what came in, what went to contractors, what was actually used, what sat idle. Poles peaked at 48,991 idle in Feb 2025, the month the site used 1,859. |
| 2. Plan it | **Plan it** | Replays the project. Each month the planner sees only what was known by then and says what to **order** (because of lead time), **hold**, or **move** from another godown, with a one-line reason per godown. Then it is scored against what really happened: idle stock **and** shortage. A saving that starves the site does not count. |
| 3. Match the sets | **Match the sets** | Compares Lumino's set ratios with what the site really used, and tracks each child item against its parents godown by godown. Only items that follow their parent closely are judged; the rest are listed for Lumino to explain. |

## Results (default settings, real data)
- 13 of 16 items: median **54% less idle stock** with under 1% of use unsupplied.
- Poles: average idle stock 29,572 → 15,347 (−48%), peak 48,991 → 32,490, zero shortage.
- Honest limits: three items ran short and are marked "does not count"; the first 9 months run on the original plan because a forecast needs history; use per godown is estimated because Lumino records usage for the whole project only.
- Only 1 of 8 stated set ratios agrees with real use (the eye hook). Ring lugs were used at 22 times the stated rate.

## How it is built
- `core/ledger.py`: the monthly ledger from the data pack's own two sums (godown stock, stock with contractors).
- `core/planner.py`: the replay. At month *t* it reads only months before *t* (tests change the future and check nothing earlier moves). Orders cover lead time plus a month of forecast use plus a safety margin, never more in total than the project really bought; stock above one godown's need moves to a godown about to run short.
- `core/sets.py`: ratio calibration against real use, pairing strength, running account per godown.
- `core/explain.py`, `core/export.py`: the reasons per godown and the Excel export.
- `app.py`: the Streamlit screens. No logic in it.
- `tests/`: 25 tests on made-up scenarios and, when the data is present, on Lumino's real numbers.

No AI model sits in the numbers: every figure is computed by code and can be traced to the records.

## Data
The project data belongs to Lumino Industries Limited and is **not in this repository**. `tools/make_bundle.py` sums the raw files to month × item × godown and packs them into one text blob. The app reads that blob from a host secret (`LUMINO_BUNDLE`), the environment, or a git-ignored local file. Without it the app says so instead of crashing.

## Run it
```
pip install -r requirements.txt
python tools/make_bundle.py <folder with the Lumino csv files>   # writes data_local/bundle.txt (git-ignored)
streamlit run app.py
pytest
```
