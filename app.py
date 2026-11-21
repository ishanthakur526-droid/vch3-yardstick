"""Yardstick: a stock and ordering planner that runs on what the site actually uses.

UI only. The numbers come from `core/`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core import charts, explain, sets as setcheck
from core.bundle import load_tables
from core.fmt import indian, month_label, short_godown, short_item
from core.ledger import build_ledger, data_notes, item_grid, item_site, ledger_table, overview, peak_idle
from core.planner import MAX_SHORTAGE_SHARE, Settings, counts, replay

st.set_page_config(page_title="Yardstick · stock planner for Lumino", page_icon="📏", layout="wide")


@st.cache_resource(show_spinner="Reading the project's records…")
def get_ledger():
    tables = load_tables()
    if tables is None:
        return None
    return build_ledger(tables["flows"], tables["used"], tables["items"]), tables["sets"]


@st.cache_data(show_spinner=False)
def run_replay(_ledger, code: str, takeover: int, window: int, safety: float):
    return replay(_ledger, code, Settings(takeover=takeover, window=window, safety=safety))


@st.cache_data(show_spinner="Replaying all 16 items month by month…")
def run_all(_ledger, takeover: int, window: int, safety: float) -> pd.DataFrame:
    rows = []
    for code in _ledger.items["item_code"]:
        r = run_replay(_ledger, code, takeover, window, safety)
        s = r.summary
        rows.append(
            {
                "code": code, "item": short_item(_ledger.item_name(code)), "unit": r.unit, "lead_days": int(_ledger.items.set_index("item_code").loc[code, "lead_time_days"]),
                "avg_real": s["avg_real"], "avg_plan": s["avg_plan"], "cut": s["reduction"],
                "peak_real": s["peak_real"], "peak_plan": s["peak_plan"], "short": s["shortage_pct"],
                "orders": s["orders_n"], "counts": counts(s),
            }
        )
    return pd.DataFrame(rows)


def decimals_for(unit: str) -> int:
    return 2 if unit in {"MT", "KM"} else 0


def number_columns(df: pd.DataFrame, unit: str) -> dict:
    dec = decimals_for(unit)
    cfg = {}
    for col in df.columns:
        if col == "Month":
            continue
        cfg[col] = st.column_config.NumberColumn(format="%.1f" if col == "Months of cover" else f"%.{dec}f")
    return cfg


bundle = get_ledger()

st.markdown(
    "<h1 style='margin-bottom:0'>Yardstick</h1>"
    "<p style='font-size:1.15rem;opacity:.85;margin:.1rem 0 .2rem'>"
    "A stock and ordering planner that runs on what the site actually uses.</p>",
    unsafe_allow_html=True,
)

if bundle is None:
    st.error(
        "This copy of the app has no project data loaded, so there is nothing to show. "
        "The data is not stored in the public code; the host provides it as a secret."
    )
    st.stop()

ledger, sets_table = bundle
st.caption(
    f"Lumino Industries · one real project around Kanpur · {month_label(ledger.months[0])} to "
    f"{month_label(ledger.months[-1])} · {len(ledger.items)} items · {len(ledger.godowns) - 1} godowns · "
    "built at Vibe Coders Hackathon 3"
)

tab_see, tab_plan, tab_sets, tab_about = st.tabs(["See it", "Plan it", "Match the sets", "About the data"])

# --------------------------------------------------------------------------------------------
with tab_see:
    names = dict(zip(ledger.items["item_code"], ledger.items["item_name"]))
    codes = list(ledger.items["item_code"])
    ov = overview(ledger)

    pick_a, pick_b = st.columns([3, 2])
    default_code = "MPO010014" if "MPO010014" in codes else codes[0]
    code = pick_a.selectbox(
        "Item",
        codes,
        index=codes.index(default_code),
        format_func=lambda c: f"{short_item(names[c])}  ·  {ledger.unit(c)}",
    )
    places = ["All godowns"] + [g for g in ledger.godowns]
    place = pick_b.selectbox("Godown", places, format_func=lambda g: g if g == "All godowns" else short_godown(g))

    unit = ledger.unit(code)
    site = item_site(ledger, code)
    row = ov[ov["item_code"] == code].iloc[0]
    peak_month, peak = peak_idle(ledger, code)
    at_peak = site[site["month"] == peak_month].iloc[0]
    cover = at_peak["cover_months"]

    cover_text = f", about {cover:.0f} months of cover" if pd.notna(cover) and cover >= 1 else ""
    st.info(
        f"**{short_item(names[code], 80)}.** At the peak ({month_label(peak_month)}), **{indian(peak)} {unit}** "
        f"were sitting idle ({indian(at_peak['godown_stock'])} in godowns, {indian(at_peak['with_contractors'])} with "
        f"contractors) while the site used **{indian(at_peak['used'])}** that month{cover_text}."
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Arrived from vendors", f"{indian(row['received'])} {unit}", border=True)
    k2.metric("Actually used", f"{indian(row['used'])} {unit}", border=True)
    last = site.iloc[-1]
    k3.metric("Idle at project end", f"{indian(last['idle_total'])} {unit}", border=True,
              help=f"{indian(last['godown_stock'])} in godowns + {indian(last['with_contractors'])} with contractors")
    k4.metric("Peak idle", f"{indian(peak)} {unit}", border=True, help=month_label(peak_month))
    k5.metric("Lead time", f"{int(row['lead_time_days'])} days", border=True)

    st.plotly_chart(charts.stock_story(site, unit))
    st.caption(
        "Contractor-held stock can only be tracked for the whole project: Lumino records usage per project, not per district."
    )

    st.subheader("Where it piled up")
    st.plotly_chart(charts.godown_heatmap(item_grid(ledger, code), unit))

    st.subheader("Month by month")
    godown = None if place == "All godowns" else place
    table = ledger_table(ledger, code, godown)
    st.dataframe(table, hide_index=True, column_config=number_columns(table, unit), height=420)
    st.download_button(
        "Download this ledger (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        file_name=f"yardstick_{code}_{'all' if godown is None else short_godown(godown).lower()}.csv",
        mime="text/csv",
    )

    st.subheader("All 16 items at a glance")
    show = ov.sort_values("peak_idle", ascending=False)
    glance = pd.DataFrame(
        {
            "Item": show["item"].map(short_item),
            "Unit": show["unit"],
            "Lead time (days)": show["lead_time_days"],
            "Arrived": [indian(v) for v in show["received"]],
            "Used": [indian(v) for v in show["used"]],
            "Idle at project end": [indian(v) for v in show["idle_now"]],
            "Peak idle": [indian(v) for v in show["peak_idle"]],
            "Peak month": show["peak_month"].map(month_label),
            "Used in that month": [indian(v) for v in show["used_that_month"]],
        }
    )
    st.dataframe(glance, hide_index=True)

# --------------------------------------------------------------------------------------------
with tab_plan:
    names = dict(zip(ledger.items["item_code"], ledger.items["item_name"]))
    codes = list(ledger.items["item_code"])
    st.markdown(
        "**Replay the project, month by month.** Each month the planner sees only what was known by then, and says what to "
        "order, hold or move. Then its plan is put next to what really happened: how much less stock would have sat idle, "
        "and any shortage it would have caused. A saving that starves the site does not count."
    )
    code = st.selectbox(
        "Item",
        codes,
        index=codes.index("MPO010014") if "MPO010014" in codes else 0,
        format_func=lambda c: f"{short_item(names[c])}  ·  {ledger.unit(c)}",
        key="plan_item",
    )
    with st.expander("Planner settings"):
        s1, s2, s3 = st.columns(3)
        takeover = s1.slider("Months on the original plan first", 3, 18, 9, help="A forecast needs history. Until then the project runs on what really arrived.")
        window = s2.slider("Months of use the forecast averages", 3, 12, 6)
        safety = s3.slider("Safety margin (standard deviations)", 0.0, 4.0, 2.33, 0.1, help="Higher means fewer shortages and more idle stock.")

    r = run_replay(ledger, code, takeover, window, safety)
    s = r.summary
    unit = r.unit
    ok = counts(s)
    kind, message = explain.verdict(r, ok)
    getattr(st, kind)(message)

    st.caption(f"Scored from {month_label(s['eval_from'])}, the first month the planner's own orders could land (lead time {r.lead_months} months).")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Average idle stock", f"{indian(s['avg_plan'])} {unit}", delta=f"{-s['reduction']:+.0%} vs {indian(s['avg_real'])} really", delta_color="inverse", border=True)
    peak_change = (s["peak_plan"] / s["peak_real"] - 1) if s["peak_real"] > 0 else 0.0
    m2.metric("Peak idle stock", f"{indian(s['peak_plan'])} {unit}", delta=f"{peak_change:+.0%} vs {indian(s['peak_real'])} really", delta_color="inverse", border=True)
    m3.metric("Use it could not supply", f"{s['shortage_pct']:.2%}", delta=f"{s['months_short']} months short", delta_color="off", border=True,
              help=f"Limit for the saving to count: {MAX_SHORTAGE_SHARE:.0%} of use.")
    m4.metric("Orders placed", f"{s['orders_n']}", delta=f"{indian(s['orders_qty'])} {unit}", delta_color="off", border=True)
    m5.metric("Moves between godowns", f"{s['moves_n']}", delta=f"{indian(s['moves_qty'])} {unit}", delta_color="off", border=True,
              help=f"Stock moved instead of newly ordered. {s['moves_planned_n']} planned at the start of a month "
                   f"({indian(s['moves_planned_qty'])} {unit}), {s['moves_n'] - s['moves_planned_n']} during the month to cover a godown that ran out.")

    st.plotly_chart(charts.replay_chart(r.monthly, r.settings.takeover, r.eval_start, unit))

    st.subheader("What the planner says, one month at a time")
    planning_months = [m for i, m in enumerate(r.months) if i >= r.settings.takeover]
    peak_month = s["peak_real_month"] if s["peak_real_month"] in planning_months else planning_months[0]
    month = st.select_slider("Month", options=planning_months, value=peak_month, format_func=month_label, key="plan_month")
    row = r.monthly[r.monthly["month"] == month].iloc[0]
    st.caption(
        f"In {month_label(month)} the project really received {indian(row['real_arrived'])} {unit} and the site used {indian(row['used'])}; "
        f"{indian(row['real_idle'])} {unit} sat idle at month end. The planner, knowing only the months before, would have ordered "
        f"{indian(row['plan_order'])} and ended with {indian(row['plan_idle'])} idle."
    )
    plan_now = explain.month_plan(r, month)
    st.dataframe(
        plan_now,
        hide_index=True,
        column_config={
            "In stock": st.column_config.NumberColumn(format=f"%.{decimals_for(unit)}f"),
            "Forecast use / month": st.column_config.NumberColumn(format=f"%.{decimals_for(unit)}f"),
            "Action": st.column_config.TextColumn(width="medium"),
            "Why": st.column_config.TextColumn(width="large"),
        },
    )
    st.download_button(
        "Download this month's list (CSV)",
        plan_now.to_csv(index=False).encode("utf-8"),
        file_name=f"yardstick_{code}_{month}_plan.csv",
        mime="text/csv",
    )

    st.subheader("Month by month: the plan against what happened")
    table = pd.DataFrame(
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
    st.dataframe(table, hide_index=True, column_config=number_columns(table, unit), height=360)
    st.download_button("Download the replay (CSV)", table.to_csv(index=False).encode("utf-8"), file_name=f"yardstick_{code}_replay.csv", mime="text/csv")

    st.subheader("All 16 items, same settings")
    everything = run_all(ledger, takeover, window, safety)
    n_ok = int(everything["counts"].sum())
    median_cut = float(everything.loc[everything["counts"], "cut"].median()) if n_ok else 0.0
    st.markdown(
        f"**{n_ok} of {len(everything)} items** kept the site supplied (under {MAX_SHORTAGE_SHARE:.0%} of use short). On those, the median "
        f"cut in average idle stock is **{median_cut:.0%}**."
    )
    board = everything.sort_values("cut", ascending=False)
    st.dataframe(
        pd.DataFrame(
            {
                "Item": board["item"],
                "Unit": board["unit"],
                "Lead time (days)": board["lead_days"],
                "Idle really (avg)": [indian(v) for v in board["avg_real"]],
                "Idle with planner (avg)": [indian(v) for v in board["avg_plan"]],
                "Cut": [f"{v:.0%}" for v in board["cut"]],
                "Peak really": [indian(v) for v in board["peak_real"]],
                "Peak with planner": [indian(v) for v in board["peak_plan"]],
                "Short": [f"{v:.1%}" for v in board["short"]],
                "Counts?": ["Yes" if c else "No: ran short" for c in board["counts"]],
            }
        ),
        hide_index=True,
    )

    with st.expander("How this plan works, and what it assumes"):
        st.markdown(
            f"- **Orders.** Each month: forecast = the higher of the last 3 and last {window} months' average use. Cover = that forecast for the "
            f"lead time plus this month, plus {safety:.2f} standard deviations of recent use as a safety margin. The order is whatever is missing after "
            f"counting stock and orders already on the way. It never buys more in total than the project really bought "
            f"(the data has no bill of quantities).\n"
            f"- **Moves.** Stock above one godown's own need goes to a godown that would run short this month, before anything new is ordered. "
            f"Transfers are same-day in the records, so a move during the month is allowed too and is counted.\n"
            f"- **No peeking.** The planner reads only months before the one it is deciding; the tests change the future and check nothing earlier moves.\n"
            f"- **First {takeover} months** run on what really arrived, because a forecast needs history. Orders landing within the first lead time after that "
            f"are inherited too. Scoring starts after that.\n"
            f"- **Use by godown is an estimate.** Lumino records use for the whole project only, so each month's use is split by what each godown handed out.\n"
            f"- **Contractor-held stock** is part of the real idle figure. In the plan, contractors draw what the site uses, so none is held back."
        )

# --------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def run_calibration(_ledger, sets_table: pd.DataFrame) -> pd.DataFrame:
    return setcheck.calibrate(_ledger, sets_table)


@st.cache_data(show_spinner=False)
def run_balance(_ledger, sets_table: pd.DataFrame, parent: str, basis: str, loose: bool):
    return setcheck.balance(_ledger, sets_table, parent, basis, judge=("strong", "loose") if loose else ("strong",))


with tab_sets:
    cal = run_calibration(ledger, sets_table)
    n_pairs, n_agree = len(cal), int(cal["agrees"].sum())
    st.markdown(
        "**Some items only work as a set.** A pole clamp is no use without its eye hook and bolts; if one runs short, "
        "the whole set waits however much of the rest is lying in the store. This checks, godown by godown and month by month, "
        "whether the children went out in the ratio their parents needed."
    )
    st.warning(
        f"**Lumino's ratios agree with what the site really used for only {n_agree} of {n_pairs} pairs.** The data pack says to compare them "
        "with real use and ask. Below are both: the ratio as given, and the ratio the site's own use implies. Which one is right for each "
        "item is a question for Lumino's people."
    )
    ratio_table = pd.DataFrame(
        {
            "Set": cal["parent_name"].map(lambda n: short_item(n, 34)),
            "Child": cal["child_name"].map(lambda n: short_item(n, 40)),
            "Unit": cal["child_unit"],
            "Ratio as given": [f"{v:g}" for v in cal["stated"]],
            "Ratio from real use": [f"{v:.4g}" for v in cal["observed"]],
            "Off by": [f"{(f if f >= 1 else 1 / f):.1f}× " + ("too high" if f < 1 else "too low") if not a else "agrees" for f, a in zip(cal["factor"], cal["agrees"])],
            "Follows its parent month to month": [f"{p} ({c:.2f})" if pd.notna(c) else "–" for p, c in zip(cal["pairing"], cal["monthly_correlation"])],
        }
    )
    st.dataframe(ratio_table, hide_index=True)
    st.caption(
        "'Off by' says how far the stated ratio is from real use. 'Follows its parent' is how closely a child's monthly use tracks its parent's: "
        "only a child that tracks closely (0.8 or more) can be judged set by set."
    )

    parents = list(dict.fromkeys(cal["parent_code"]))
    pnames = dict(zip(cal["parent_code"], cal["parent_name"]))
    c1, c2, c3 = st.columns([3, 2, 2])
    parent = c1.selectbox("Set", parents, format_func=lambda p: short_item(pnames[p], 60), key="set_parent")
    basis_label = c2.radio("Ratio to use", ["From real use", "As Lumino gave it"], key="set_basis")
    loose = c3.checkbox("Also judge loosely paired items", value=False, help="Children whose use only loosely follows the parent's. Expect many flags.")
    view = run_balance(ledger, sets_table, parent, "observed" if basis_label == "From real use" else "stated", loose)

    judged_children = [c for c, j in (view.judged or {}).items() if j]
    if not judged_children:
        st.info(
            "None of this set's children is issued set by set (their use does not follow the parent's closely enough), so the records cannot say "
            "whether this set is in balance. Ask Lumino how contractors draw them, or tick the box above to see what a loose reading gives."
        )
    else:
        flags = setcheck.flagged(view)
        cal_m = setcheck.calendar(view)
        n_bad = int((cal_m["status"] != "balanced").sum())
        k1, k2, k3 = st.columns(3)
        k1.metric("Months out of balance", f"{n_bad} of {len(cal_m)}", border=True, help="At least one godown is off on at least one judged child.")
        k2.metric("Serious / watch", f"{int((flags['severity'] == 'serious').sum())} / {int((flags['severity'] == 'watch').sum())}", border=True,
                  help=f"Godown-month accounts off by {setcheck.SERIOUS:.0%} / {setcheck.WATCH:.0%} of all sets issued so far.")
        k3.metric("Judged children", ", ".join(short_item(view.names[c], 22) for c in judged_children), border=True)

        st.plotly_chart(charts.set_calendar(cal_m))
        st.caption("Every month at least one godown's account is off on a judged child. Serious: off by 30% or more of all sets issued so far. Watch: 15% or more.")

        child = st.selectbox("Child", judged_children, format_func=lambda c: short_item(view.names[c], 60), key="set_child")
        st.plotly_chart(charts.set_account(view.account[view.account["child"] == child], short_item(view.names[child], 28), setcheck.WATCH, setcheck.SERIOUS))

        st.subheader("Every flag, worst first")
        if len(flags):
            shown = pd.DataFrame(
                {
                    "Month": flags["month"],
                    "Godown": flags["godown"].map(short_godown),
                    "Child": flags["child_name"].map(lambda n: short_item(n, 34)),
                    "Severity": flags["severity"],
                    "Off by": [f"{v:+.0%}" for v in flags["off"]],
                    "Why": flags["reason"],
                }
            )
            st.dataframe(shown, hide_index=True, height=320, column_config={"Why": st.column_config.TextColumn(width="large")})
            st.download_button("Download the flags (CSV)", shown.to_csv(index=False).encode("utf-8"), file_name=f"yardstick_sets_{parent}.csv", mime="text/csv")
        else:
            st.success("No godown is out of balance on the judged children.")

        st.subheader("What is stuck, in one month")
        pick = st.select_slider("Month", options=ledger.months, value=ledger.months[len(ledger.months) // 2], format_func=month_label, key="set_month")
        snap = setcheck.stuck(view, pick)
        checked = [m for m in view.members if m == view.parent or (view.judged or {}).get(m)]
        st.dataframe(
            pd.DataFrame(
                {
                    "Godown": snap["godown"].map(short_godown),
                    "Sets that can be finished": [indian(v) for v in snap["sets_possible"]],
                    "Limited by": snap["limiting"].map(lambda m: short_item(view.names[m], 30)),
                    **{f"{short_item(view.names[m], 22)}: on hand ({view.units[m]})": [indian(v) for v in snap[f"have_{m}"]] for m in checked},
                    **{f"{short_item(view.names[m], 22)}: waiting": [indian(v) for v in snap[f"waiting_{m}"]] for m in checked},
                }
            ),
            hide_index=True,
        )
        st.caption("'Waiting' is the stock of each member that cannot be used until the limiting one arrives.")

    with st.expander("How this works, and what it does not know"):
        st.markdown(
            "- **The account.** For each child at each godown: the sets' worth issued so far (child issued ÷ ratio) against the parents issued so far. "
            "Negative means the child is behind and sets wait for it; positive means the child is ahead and piling up.\n"
            "- **Ratios.** 'From real use' keeps the shape of Lumino's numbers and scales each child by one factor so the project's totals match what the "
            "site used. 'As Lumino gave it' uses the file's numbers untouched.\n"
            "- **Not every child is issued set by set.** Bolts, nuts and some lugs are handed out in bulk. Judging them month by month would flag almost everything, "
            "so by default only children that follow their parent closely are judged, and the rest are listed above for Lumino to explain.\n"
            "- **Contractor-held stock** is not split by godown in the records, so the account measures what left each godown, not what was installed."
        )

# --------------------------------------------------------------------------------------------
with tab_about:
    notes = data_notes(ledger)
    st.subheader("Where the numbers come from")
    st.markdown(
        "One real Lumino project around Kanpur, March 2023 to October 2026, shared by Calcutta AI Club for this hackathon. "
        "The data belongs to Lumino Industries Limited. It is not stored in this app's public code; the host supplies it as a secret."
    )
    st.markdown(
        "**How each number is built** (from the data pack's own rules)\n"
        "- *Idle in a godown* = receipts + transfers in − transfers out − issued to contractors + returned, added up from the start.\n"
        "- *Held by contractors* = issued − returned − used, added up from the start. Usage has no godown, so this is project-wide.\n"
        "- Rows that look identical are separate entries and are all counted. Rows with zero quantity add nothing.\n"
        "- Where a running total dips below zero (a late entry), it is shown as zero.\n"
        "- `KANPUR CLOSER` is the closing store that took leftover stock when the project wound up in 2026."
    )
    st.markdown(
        f"**Checks on this data**\n"
        f"- {notes['items']} items, {notes['locations']} locations (6 godowns and the closing store), {notes['months']}.\n"
        f"- {notes['godown_months_below_zero']} godown-months dip below zero from late entries (worst dip "
        f"{indian(notes['worst_dip'])}); they are shown as zero."
    )
