import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from live_data import get_dashboard_data


st.set_page_config(
    page_title="SPECTRA Traffic Control Centre",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Refresh once per second so the dashboard follows SUMO live output.
st_autorefresh(interval=1000, key="spectra_live_refresh")


st.markdown(
    """
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}
.hero {
    padding: 1.1rem 1.4rem;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(30,30,40,.96), rgba(15,35,45,.96));
    margin-bottom: 1rem;
}
.hero h1 { margin: 0; font-size: 2.2rem; }
.hero p { margin: .25rem 0 0; opacity: .75; }
.online { color: #2ecc71; font-weight: 700; }
.waiting { color: #f39c12; font-weight: 700; }
.road-card {
    padding: 1rem;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 12px;
    min-height: 120px;
}
.road-title {
    font-size: 1.25rem;
    font-weight: 750;
    margin-bottom: .4rem;
}
.signal {
    font-size: 1.6rem;
    text-align: center;
    margin: .3rem 0 .4rem;
}
.signal-green { color: #2ecc71; }
.signal-red { color: #e74c3c; }
.signal-transition { color: #f1c40f; }
.junction {
    border: 1px solid rgba(128,128,128,.3);
    border-radius: 16px;
    padding: 1.3rem;
    text-align: center;
}
.j3 {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 125px;
    height: 125px;
    border-radius: 50%;
    border: 4px solid #888;
    font-size: 1.8rem;
    font-weight: 800;
    margin: .7rem;
}
.edge-label { font-weight: 800; font-size: 1.1rem; }
.small-note { opacity: .65; font-size: .85rem; }
</style>
""",
    unsafe_allow_html=True,
)


def safe_number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def signal_for_edge(edge, current_phase):
    if current_phase == "TRANSITION":
        return "🟡 TRANSITION", "signal-transition"

    edge_direction = "E1_E3" if edge in ["E1", "E3"] else "E2_E4"
    if current_phase == edge_direction:
        return "🟢 GREEN", "signal-green"

    return "🔴 RED", "signal-red"


# -----------------------------
# Live data source
# -----------------------------
data = get_dashboard_data()

if data is None:
    st.markdown(
        """
        <div class="hero">
            <h1>🚦 SPECTRA</h1>
            <p>Predictive Adaptive Traffic Signal Control Centre</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "Waiting for live SPECTRA data. Start `spectra_controller.py` and allow "
        "it to finish the training phase. The dashboard becomes live when "
        "`dashboard_live.json` is created."
    )

    st.stop()

traffic = data.get("traffic", {})

missing_edges = [edge for edge in ["E1", "E2", "E3", "E4"] if edge not in traffic]
if missing_edges:
    st.error(
        "Live JSON was found, but traffic data is incomplete. Missing: "
        + ", ".join(missing_edges)
    )
    st.stop()


# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🚦 SPECTRA</h1>
        <p>Predictive Adaptive Traffic Signal Control Centre</p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_col, sim_col, phase_col, time_col = st.columns(4)
with status_col:
    st.markdown("### <span class='online'>● SYSTEM LIVE</span>", unsafe_allow_html=True)
    st.caption(f"Updated {data.get('generated_at', '—')}")
with sim_col:
    st.metric("Simulation Time", f"{safe_number(data.get('simulation_time')):.0f} s")
with phase_col:
    st.metric("Current Phase", data.get("current_phase", "UNKNOWN"))
with time_col:
    st.metric("Time in Phase", f"{safe_number(data.get('time_in_phase')):.0f} s")

st.caption(f"Live source: `{data.get('_data_file', 'dashboard_live.json')}`")
st.divider()


# -----------------------------
# Live traffic cards
# -----------------------------
st.header("Live Traffic State")

cols = st.columns(4)
for i, edge in enumerate(["E1", "E2", "E3", "E4"]):
    d = traffic[edge]
    signal_text, signal_class = signal_for_edge(edge, data.get("current_phase"))

    with cols[i]:
        st.markdown(
            f"""
            <div class="road-card">
                <div class="road-title">Approach {edge}</div>
                <div class="signal {signal_class}">{signal_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.metric("Vehicles", int(safe_number(d.get("vehicle_count"))))
        st.metric("Halted / Queue", int(safe_number(d.get("halted_count"))))
        st.metric("Mean Speed", f"{safe_number(d.get('mean_speed')):.1f} m/s")
        st.metric("Waiting Time", f"{safe_number(d.get('waiting_time')):.1f} s")
        st.metric("Predicted +30 sec", f"{safe_number(d.get('predicted_halted')):.1f}")

st.divider()


# -----------------------------
# Junction + decision
# -----------------------------
left, right = st.columns([1.15, 1])

with left:
    st.header("Junction J3")
    st.markdown(
        """
        <div class="junction">
            <div class="edge-label">E1</div>
            <div>⬇</div>
            <div class="j3">J3</div>
            <div>↔</div>
            <div><span class="edge-label">E3</span> &nbsp;&nbsp;&nbsp; <span class="edge-label">E4</span></div>
            <div style="margin-top:.6rem">⬆</div>
            <div class="edge-label">E2</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Signal groups: E1/E3 and E2/E4")

with right:
    st.header("SPECTRA Decision")

    d1, d2 = st.columns(2)
    with d1:
        st.metric("E1 / E3 Action Cost", f"{safe_number(data.get('cost_13')):.2f}")
    with d2:
        st.metric("E2 / E4 Action Cost", f"{safe_number(data.get('cost_24')):.2f}")

    st.caption("Lower action cost = preferred Stage 7 action")

    st.write("Stage 7 Recommendation:", f"**{data.get('stage7_decision', '—')}**")
    st.write("Stage 8 Safe Action:", f"**{data.get('safe_action', '—')}**")
    st.success(f"Final Decision: **{data.get('final_decision', '—')}**")
    st.info(f"Reason: **{data.get('decision_reason', '—')}**")

st.divider()


# -----------------------------
# Current vs predicted
# -----------------------------
st.header("Current vs Predicted Congestion")

comparison = []
for edge in ["E1", "E2", "E3", "E4"]:
    d = traffic[edge]
    comparison.append(
        {
            "Edge": edge,
            "Current Halted": safe_number(d.get("halted_count")),
            "Predicted Halted (+30s)": safe_number(d.get("predicted_halted")),
        }
    )

comparison_df = pd.DataFrame(comparison)
melted = comparison_df.melt(id_vars="Edge", var_name="Measure", value_name="Vehicles")
fig = px.bar(
    melted,
    x="Edge",
    y="Vehicles",
    color="Measure",
    barmode="group",
    title="Current Queue vs 30-Second Prediction",
)
fig.update_layout(height=390, margin=dict(l=10, r=10, t=55, b=10))
st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Time-series graphs
# -----------------------------
history = data.get("traffic_history", [])
history_df = pd.DataFrame(history)

if not history_df.empty and {"time", "edge", "halted", "waiting_time"}.issubset(history_df.columns):
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Queue Length vs Time")
        fig_queue = px.line(
            history_df,
            x="time",
            y="halted",
            color="edge",
            labels={"time": "Simulation Time (s)", "halted": "Halted Vehicles"},
        )
        fig_queue.update_layout(height=400)
        st.plotly_chart(fig_queue, use_container_width=True)

    with c2:
        st.subheader("Average Waiting Time vs Time")
        fig_wait = px.line(
            history_df,
            x="time",
            y="waiting_time",
            color="edge",
            labels={"time": "Simulation Time (s)", "waiting_time": "Waiting Time (s)"},
        )
        fig_wait.update_layout(height=400)
        st.plotly_chart(fig_wait, use_container_width=True)
else:
    st.info("Live history will appear after SPECTRA has produced several control steps.")

st.divider()


# -----------------------------
# ML panel
# -----------------------------
st.header("🤖 Traffic Prediction Engine")
ml = data.get("ml", {})

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Prediction Horizon", f"{safe_number(ml.get('prediction_horizon')):.0f} sec")
with m2:
    st.metric("MAE", f"{safe_number(ml.get('mae')):.3f}")
with m3:
    st.metric("RMSE", f"{safe_number(ml.get('rmse')):.3f}")
with m4:
    st.metric("R²", f"{safe_number(ml.get('r2')):.3f}")

st.caption(f"Model: {ml.get('model', '—')}")

st.divider()


# -----------------------------
# Emergency + safety
# -----------------------------
e_col, s_col = st.columns(2)

with e_col:
    st.header("🚑 Emergency Priority")
    emergency = data.get("emergency", {})

    if emergency.get("detected"):
        st.error("EMERGENCY PRIORITY ACTIVE")
        st.write("Emergency vehicles:", emergency.get("count", 0))

        details = emergency.get("details", [])
        for vehicle in details:
            st.write(
                f'**{vehicle.get("vehicle_id", "unknown")}** on '
                f'**{vehicle.get("edge", "?")}** → '
                f'**{vehicle.get("direction", "?")}** '
                f'(waiting {safe_number(vehicle.get("waiting_time")):.1f} s)'
            )
    else:
        st.success("No emergency vehicle detected")

with s_col:
    st.header("🛡 Safety Monitor")
    safety = data.get("safety", {})

    st.write(f'Minimum Green: **{safety.get("minimum_green_time", "—")} s**')
    st.write(f'Maximum Green: **{safety.get("maximum_green_time", "—")} s**')
    st.write(f'Maximum Red: **{safety.get("maximum_red_time", "—")} s**')
    st.write(f'E1/E3 Red Time: **{safety.get("red_time_E1_E3", "—")} s**')
    st.write(f'E2/E4 Red Time: **{safety.get("red_time_E2_E4", "—")} s**')

    if safety.get("fairness_override"):
        st.warning("Fairness override active — starvation prevention")

    if safety.get("max_green_override"):
        st.warning("Maximum-green override active")

    if not safety.get("fairness_override") and not safety.get("max_green_override"):
        st.success("Safety constraints normal")

st.divider()
st.caption("SPECTRA Dashboard • Live data from spectra_controller.py")
