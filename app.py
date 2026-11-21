"""Yardstick: a stock and ordering planner that runs on what the site actually uses.

UI only. The numbers come from `core/`.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core import charts
from core.bundle import load_tables
from core.fmt import indian, month_label, short_godown, short_item
from core.ledger import build_ledger, data_notes, item_grid, item_site, ledger_table, overview, peak_idle

st.set_page_config(page_title="Yardstick · stock planner for Lumino", page_icon="📏", layout="wide")


@st.cache_resource(show_spinner="Reading the project's records…")
def get_ledger():
    tables = load_tables()
    if tables is None:
        return None
    return build_ledger(tables["flows"], tables["used"], tables["items"]), tables["sets"]


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

tab_see, tab_about = st.tabs(["See it", "About the data"])

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
