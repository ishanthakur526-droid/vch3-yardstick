"""Excel export of the plan: the list to approve, the replay, the scoreboard and the assumptions."""

from __future__ import annotations

import io

import pandas as pd

from . import explain
from .fmt import month_label
from .planner import MAX_SHORTAGE_SHARE, Replay, Settings


def assumptions(r: Replay, name: str) -> list[str]:
    s = r.settings
    return [
        f"Item: {name} ({r.unit}); lead time {r.lead_months} months.",
        f"The first {s.takeover} months run on what really arrived (a forecast needs history). Scored from {month_label(r.summary['eval_from'])}.",
        f"Forecast: the higher of the last 3 and last {s.window} months' average use. Safety margin: {s.safety:.2f} standard deviations of the last {s.sd_window} months.",
        "Orders cover the lead time plus this month of forecast use plus the safety margin, after counting stock and orders already on the way.",
        "The plan never buys more in total than the project really bought (the data has no bill of quantities).",
        "Use is recorded for the whole project only; it is split across godowns by what each godown handed out that month (an estimate).",
        "Stock may move between godowns the same day (the records show same-day transfer vouchers).",
        f"A saving counts only if the plan left under {MAX_SHORTAGE_SHARE:.0%} of use unsupplied.",
        "Source data: Lumino Industries Limited, shared by Calcutta AI Club for Vibe Coders Hackathon 3. Planning support, not an instruction to buy.",
    ]


def workbook(r: Replay, month: str, name: str, everything: pd.DataFrame) -> bytes:
    """One .xlsx a store-keeper or purchase officer can open: this month's list, the full replay, all items, assumptions."""
    plan_now = explain.month_plan(r, month)
    replay = pd.DataFrame(
        {
            "Month": r.monthly["month"],
            "Actually used": r.monthly["used"],
            "Really arrived": r.monthly["real_arrived"],
            "Really idle": r.monthly["real_idle"],
            "Planner ordered": r.monthly["plan_order"],
            "Plan: arrived": r.monthly["plan_arrived"],
            "Plan: idle": r.monthly["plan_idle"],
            "Plan: could not supply": r.monthly["plan_shortage"],
        }
    )
    board = everything.rename(
        columns={"item": "Item", "unit": "Unit", "lead_days": "Lead time (days)", "avg_real": "Idle really (avg)", "avg_plan": "Idle with planner (avg)",
                 "cut": "Cut", "peak_real": "Peak really", "peak_plan": "Peak with planner", "short": "Shortage share", "orders": "Orders", "counts": "Counts?"}
    ).drop(columns=["code"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xl:
        book = xl.book
        wrap = book.add_format({"text_wrap": True, "valign": "top"})
        head = book.add_format({"bold": True, "bg_color": "#EDE9FE", "border": 1, "text_wrap": True, "valign": "top"})
        sheets = [(f"Plan for {month}", plan_now), ("Replay", replay), ("All items", board)]
        for title, df in sheets:
            df.to_excel(xl, sheet_name=title[:31], index=False, startrow=1, header=False)
            ws = xl.sheets[title[:31]]
            for c, col in enumerate(df.columns):
                ws.write(0, c, col, head)
                width = 60 if col == "Why" else (26 if col in ("Action", "Item") else 16)
                ws.set_column(c, c, width, wrap if col in ("Why", "Action", "Item") else None)
            ws.freeze_panes(1, 0)
        pd.DataFrame({"Assumptions and limits": assumptions(r, name)}).to_excel(xl, sheet_name="Assumptions", index=False)
        xl.sheets["Assumptions"].set_column(0, 0, 130, wrap)
    return buf.getvalue()
