"""Plotly figures. One palette, used everywhere, so a colour always means the same thing."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .fmt import short_godown

COLOR = {
    "arrived": "#3b82f6",
    "issued": "#f59e0b",
    "used": "#10b981",
    "godown": "#7c3aed",
    "contractor": "#fb923c",
    "plan": "#0ea5e9",
    "real": "#a855f7",
    "short": "#ef4444",
}
_GRID = "rgba(128,128,128,0.22)"


def _dates(months: pd.Series) -> pd.DatetimeIndex:
    return pd.to_datetime(months.astype(str) + "-01")


def _base(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=72, b=8),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.07, x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(gridcolor=_GRID, showline=False)
    fig.update_yaxes(gridcolor=_GRID, zeroline=False)
    return fig


def stock_story(site: pd.DataFrame, unit: str) -> go.Figure:
    """Top: where the stock sat. Bottom: what moved each month. Same months, so the gap is obvious."""
    x = _dates(site["month"])
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
        subplot_titles=(f"Stock on hand at month end ({unit})", f"What moved each month ({unit})"),
    )
    fig.add_trace(
        go.Scatter(x=x, y=site["godown_stock"], name="Idle in godowns", mode="lines", stackgroup="stock",
                   line=dict(width=0.8, color=COLOR["godown"]), fillcolor="rgba(124,58,237,0.55)"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=site["with_contractors"], name="Held by contractors", mode="lines", stackgroup="stock",
                   line=dict(width=0.8, color=COLOR["contractor"]), fillcolor="rgba(251,146,60,0.55)"),
        row=1, col=1,
    )
    for col, label, color in (("received", "Arrived from vendors", "arrived"), ("issue", "Issued to contractors", "issued"), ("used", "Actually used", "used")):
        fig.add_trace(go.Bar(x=x, y=site[col], name=label, marker_color=COLOR[color]), row=2, col=1)
    fig.update_layout(barmode="group", bargap=0.2)
    fig.update_annotations(font_size=13, xanchor="left", x=0)
    return _base(fig, 600)


def godown_heatmap(grid_item: pd.DataFrame, unit: str) -> go.Figure:
    """Godown by month: where it piled up."""
    piv = grid_item.pivot(index="godown", columns="month", values="stock")
    places = list(piv.index)
    fig = go.Figure(
        go.Heatmap(
            z=piv.loc[places].values,
            x=_dates(pd.Series(piv.columns)),
            y=[short_godown(g) for g in places],
            colorscale="Purples",
            colorbar=dict(title=unit, thickness=12),
            hovertemplate="%{y} · %{x|%b %Y}<br>%{z:,.0f} " + unit + " idle<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(hovermode="closest")
    return _base(fig, 300).update_layout(margin=dict(l=8, r=8, t=8, b=8))
