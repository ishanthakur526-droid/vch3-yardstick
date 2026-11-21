# HANDOVER (updated hourly)

Last update: 12:30 IST, Sat 21 Nov 2026.

## Where things stand
- **Pick:** Lumino Industries, "1,700 Poles" (picked at 11:00). Product name: **Yardstick**.
- **Repo:** https://github.com/ishanthakur526-droid/vch3-yardstick (public, created 11:02 IST).
- **Live app:** https://vch3-yardstick-mvluj7jtvsgdnkqbw8kuqh.streamlit.app/ (Ishan deployed it at about 12:05; repo `vch3-yardstick`, branch `main`, file `app.py`, Python 3.12, secret `LUMINO_BUNDLE`). Every push to `main` redeploys it. Check it with `python tests/smoke_live.py <url>`; on Streamlit Cloud the app sits in an iframe, so the script opens the `/~/+/` route.
- **Built and tested (38 tests, all green):**
  - `core/ledger.py` monthly ledger; `app.py` **See it** screen.
  - `core/planner.py` replay with no look-ahead, order/hold/move, purchase cap, shortage check; **Plan it** screen with reasons per godown and Excel export.
  - `core/sets.py` ratio check against real use and a per-godown running account; **Match the sets** screen.
  - `core/requisition.py` BOQ to buy list (BOQ line wins; set ratio from the file or the site; per-pole estimate; stock in hand at the last month; order-by from lead time); **Requisition** screen with Excel buy list and a BOQ upload (CSV or Excel). Added at 12:30 after the desk visit.
  - **Plan it** also shows what no spare stock would cost on a continuous plan: safety margin 0 keeps 5 of 16 items supplied, 1.0 keeps 9, the default 2.33 keeps 13.
- **Headline (default settings):** 13 of 16 items keep shortage under 1% and cut average idle stock by a median 54%. Poles: 29,572 → 15,347 average idle, peak 48,991 → 32,490, no shortage.

## The data (never commit it)
- Raw files stay outside the repo: `F:\ClacuttaAIClub_Hackathon\data-lumino\pack\lumino-vch3-data\csv\`. The pack's `README.md` sits one level up.
- `python tools/make_bundle.py <csv folder>` writes `data_local/bundle.txt` (git-ignored). The same text goes into the host secret `LUMINO_BUNDLE`; `data_local/streamlit_secrets.toml` holds the ready-to-paste secrets block.
- Rules from the pack: do not dedupe rows; ignore zero rows; clip small negative stock to 0; no order dates; usage has no godown.
- Set ratios in `sets.csv` disagree with real use for 7 of 8 pairs. Asked at Lumino's desk (11:47): no direct answer. Their rule: a line on the BOQ is the requirement, and the file's ratios come from the tendering engineers' experience. Still open: ring lugs 0.25 vs 5.7 per three-phase box, single-phase lugs 0.25 vs 0.65, whether the three bolt types are alternatives or all needed, tonnes vs kg. So Requisition shows the file's ratio and the site's side by side and never overwrites either.
- Other desk answers (11:47): the user is head-office procurement, who work per project from a BOQ (sites and poles); they keep no spare stock and cannot miss the deadline; the data lives in their ERP, updated daily and checked weekly. No clear OK yet to show real numbers on the public link (the pack says it is one real Lumino project): ask at the 13:20 visit; if no, mask names and scale quantities.

## Decisions worth knowing
- Replay is whole-site for scoring (idle and shortage), with orders and moves decided per godown. Use per godown is an estimate (usage has no godown).
- The first 9 months run on the original plan (what really arrived); scoring starts when the planner's own first order could land.
- A plan counts only if under 1% of use is left unsupplied. The planner never buys more in total than the project really bought.
- Only children that follow their parent closely (monthly correlation 0.8+) are judged for set balance.

## Plan (times IST)
- 12:30 Requisition pushed; confirm the live link after the redeploy; 13:15 phone click path for Lumino (type the poles, read the buy list, open the ratio table).
- 13:15-15:00 accuracy panel, desk answers as data, a mask switch if Lumino says so. The Hindi store-keeper note is cut: the store-keeper is not the user.
- **15:45 feature stop. 16:44 last push. Nothing after 16:45.**

## If Claude is unavailable
1. Open Antigravity (`%LOCALAPPDATA%\Programs\antigravity`), then File > Open Folder > `F:\ClacuttaAIClub_Hackathon\everything build day`.
2. Paste this prompt into its agent:

> You are continuing a hackathon build in this folder (public repo vch3-yardstick). Read HANDOVER.md and README.md first. Hard rules: never commit keys, `.env`, `secrets.toml` or any raw Lumino data (CSV, XLSX, ZIP); commit small and often with clear messages; no commits or pushes after 16:45 IST; feature stop at 15:45 IST, fixes only after that; the live link must keep working without sign-in. Continue from "Where things stand", test locally with `streamlit run app.py` and `pytest`, and tell me exactly what to click for any deploy step.
