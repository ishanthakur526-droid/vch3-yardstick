# HANDOVER (updated hourly)

Last update: 11:50 IST, Sat 21 Nov 2026.

## Where things stand
- **Pick:** Lumino Industries, "1,700 Poles" (picked at 11:00). Product name: **Yardstick**.
- **Repo:** https://github.com/ishanthakur526-droid/vch3-yardstick (public, created 11:02 IST).
- **Live app:** not confirmed yet. Ishan was asked at 11:30 to deploy on Streamlit Cloud (repo `vch3-yardstick`, branch `main`, file `app.py`, Python 3.12, secret `LUMINO_BUNDLE`).
- **Built and tested (25 tests, all green):**
  - `core/ledger.py` monthly ledger; `app.py` **See it** screen.
  - `core/planner.py` replay with no look-ahead, order/hold/move, purchase cap, shortage check; **Plan it** screen with reasons per godown and Excel export.
  - `core/sets.py` ratio check against real use and a per-godown running account; **Match the sets** screen.
- **Headline (default settings):** 13 of 16 items keep shortage under 1% and cut average idle stock by a median 54%. Poles: 29,572 → 15,347 average idle, peak 48,991 → 32,490, no shortage.

## The data (never commit it)
- Raw files stay outside the repo: `F:\ClacuttaAIClub_Hackathon\data-lumino\pack\lumino-vch3-data\csv\`. The pack's `README.md` sits one level up.
- `python tools/make_bundle.py <csv folder>` writes `data_local/bundle.txt` (git-ignored). The same text goes into the host secret `LUMINO_BUNDLE`; `data_local/streamlit_secrets.toml` holds the ready-to-paste secrets block.
- Rules from the pack: do not dedupe rows; ignore zero rows; clip small negative stock to 0; no order dates; usage has no godown.
- Set ratios in `sets.csv` disagree with real use for 7 of 8 pairs. Asked at Lumino's desk; record the answer here: _(not yet received)_.

## Decisions worth knowing
- Replay is whole-site for scoring (idle and shortage), with orders and moves decided per godown. Use per godown is an estimate (usage has no godown).
- The first 9 months run on the original plan (what really arrived); scoring starts when the planner's own first order could land.
- A plan counts only if under 1% of use is left unsupplied. The planner never buys more in total than the project really bought.
- Only children that follow their parent closely (monthly correlation 0.8+) are judged for set balance.

## Plan (times IST)
- 12:00 live link confirmed; 12:00-13:15 polish and desk answers as data; 13:15 phone click path for Lumino.
- 13:15-15:00 optional Hindi store-keeper note via Sarvam, accuracy panel, desk answers.
- **15:45 feature stop. 16:44 last push. Nothing after 16:45.**

## If Claude is unavailable
1. Open Antigravity (`%LOCALAPPDATA%\Programs\antigravity`), then File > Open Folder > `F:\ClacuttaAIClub_Hackathon\everything build day`.
2. Paste this prompt into its agent:

> You are continuing a hackathon build in this folder (public repo vch3-yardstick). Read HANDOVER.md and README.md first. Hard rules: never commit keys, `.env`, `secrets.toml` or any raw Lumino data (CSV, XLSX, ZIP); commit small and often with clear messages; no commits or pushes after 16:45 IST; feature stop at 15:45 IST, fixes only after that; the live link must keep working without sign-in. Continue from "Where things stand", test locally with `streamlit run app.py` and `pytest`, and tell me exactly what to click for any deploy step.
