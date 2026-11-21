# HANDOVER (updated hourly)

Last update: 11:05 IST, Sat 21 Nov 2026.

## Where things stand
- **Pick:** Lumino Industries, "1,700 Poles" (picked at 11:00).
- **Repo:** https://github.com/ishanthakur526-droid/vch3-yardstick (public, created 11:02 IST).
- **Live app:** not deployed yet (target 12:00, organisers' deadline 13:00).
- **Built so far:** `.gitignore`, `README.md`, `requirements.txt`. No app code yet.

## The data (never commit it)
- Local copy, outside the repo: `F:\ClacuttaAIClub_Hackathon\data-lumino\pack\lumino-vch3-data\csv\` (`items`, `sets`, `receipts`, `contractor_moves`, `transfers`, `data_dictionary`). The pack's own `README.md` sits one level up; read it first.
- 16 items, 6 godowns (Kanpur districts) plus `KANPUR CLOSER` (closing store, transfers only), Mar 2023 to Oct 2026. `contractor_moves` has 2.3 lakh rows (ISSUE, RETURN, CONSUMPTION).
- Godown stock = receipts + transfers IN - transfers OUT - ISSUE + RETURN (cumulative from zero). Stock with contractors = ISSUE - RETURN - CONSUMPTION, **project-wide only** (CONSUMPTION has no godown).
- Don't dedupe identical rows. Ignore qty 0. Clip small negative stock to 0 (late entries). No order dates: order date = receipt date - lead time. Receipts stop Jul 2026; usage runs to Oct 2026.
- Poles at the Feb 2025 peak: about 35,500 in godowns plus about 13,500 with contractors, while the site used about 1,900 that month.
- `sets.csv` ratio_of_parent doesn't match real use (e.g. 0.25 ring lugs per 3-phase box vs about 5.7 used). Asked at Lumino's desk; record the answer here.
- Deployed app: the data travels as an encrypted bundle in `data/`; the key lives only in Streamlit secrets and the local `.streamlit/secrets.toml` (ignored).

## Plan (times IST)
- 11:05-11:40 data layer + tests; 11:40-12:00 "See it" screen; ~11:55 Ishan deploys on Streamlit.
- 12:00-13:15 "Plan it": month-by-month replay with no look-ahead; order/hold/move list; plan vs what really happened.
- 13:15-15:00 "Match the sets", forecast accuracy, Excel export, desk answers as data.
- 15:00-15:45 Hindi one-line briefs (Sarvam), polish. **15:45 feature stop. 16:44 last push. Nothing after 16:45.**

## If Claude is unavailable
1. Open Antigravity (`%LOCALAPPDATA%\Programs\antigravity`), then File > Open Folder > `F:\ClacuttaAIClub_Hackathon\everything build day`.
2. Paste this prompt into its agent:

> You are continuing a hackathon build in this folder (public repo vch3-yardstick). Read HANDOVER.md and README.md first. Hard rules: never commit keys, `.env`, `secrets.toml` or any raw Lumino data (CSV, XLSX, ZIP); commit small and often with clear messages; no commits or pushes after 16:45 IST; feature stop at 15:45 IST, fixes only after that; the live link must keep working without sign-in. Continue from "Where things stand", test locally with `streamlit run app.py`, and tell me exactly what to click for any deploy step.
