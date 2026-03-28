"""OpenOA Streamlit Demo - Robust FE + BE."""
import streamlit as st
import os
from pathlib import Path
import shutil
from openoa import PlantData
from openoa.analysis import aep, wake_losses
from examples.project_ENGIE import prepare

st.set_page_config(page_title="OpenOA Dashboard", page_icon="🌀", layout="wide")

# Premium Aesthetic Injection
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dee2e6;
    }
    .stMetric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    h1 {
        color: #1a202c;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌀 OpenOA Dashboard")
st.markdown("_NREL OpenOA wind plant analysis (AEP, wakes)._")

with st.sidebar:
    st.header("⚙️ Simulation Settings")
    st.markdown("Adjust the number of Monte Carlo simulations to balance speed vs. accuracy.")
    num_sim_aep = st.slider("AEP Analysis Simulations", min_value=1, max_value=100, value=10, step=1)
    num_sim_wake = st.slider("Wake Analysis Simulations", min_value=1, max_value=100, value=5, step=1)

@st.cache_resource
def load_plant():
    """Load ENGIE data via project_ENGIE.prepare (handles zip/data)."""
    data_dir = Path(__file__).parent / "data"
    meta = data_dir / "plant_meta.yml"
    data_path = data_dir / "la_haute_borne"
    
    # Always re-prepare to avoid bad state
    if data_path.exists():
        shutil.rmtree(data_path)
    
    plant = prepare(path=data_path, return_value="plantdata")
    return plant

with st.spinner("Initializing Data Engine..."):
    plant = load_plant()

tab1, tab2, tab3 = st.tabs(["Data", "AEP", "Wakes"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Capacity", f"{plant.metadata.capacity:.1f} MW")
        st.metric("Turbines", plant.n_turbines)
    with col2:
        start, end = plant.scada.index.get_level_values("time").min(), plant.scada.index.get_level_values("time").max()
        st.metric("Period", f"{start.date()} to {end.date()}")
    st.dataframe(plant.asset.head())
    st.subheader("SCADA Sample")
    st.dataframe(plant.scada.head())

with tab2:
    @st.cache_resource
    def aep_analysis(num_sim):
        a = aep.create_MonteCarloAEP(plant)
        a.run(num_sim=num_sim)
        return a
    aep_res = aep_analysis(num_sim_aep)
    col1, col2 = st.columns(2)
    with col1:
        mean = aep_res.results.aep_GWh.mean()
        p10 = aep_res.results.aep_GWh.quantile(0.1)
        st.metric("Mean AEP", f"{mean:.1f} GWh/yr", f"P10 {p10:.1f}")
    with col2:
        st.metric("LT Avail Loss", f"{aep_res.results.avail_pct.mean()*100:.1f}%")
        st.metric("LT Curt Loss", f"{aep_res.results.curt_pct.mean()*100:.1f}%")
    aep_res.plot_result_aep_distributions()

with tab3:
    @st.cache_resource
    def wake_analysis(num_sim):
        w = wake_losses.create_WakeLosses(plant)
        w.run(num_sim=num_sim)
        return w
    wake_res = wake_analysis(num_sim_wake)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("POR Wake Loss", f"{wake_res.wake_losses_por_mean*100:.1f}%")
        st.metric("LT Wake Loss", f"{wake_res.wake_losses_lt_mean*100:.1f}%")
    wake_res.plot_wake_losses_by_wind_direction()
    wake_res.plot_wake_losses_by_wind_speed()

st.markdown("---")
col_footer, _ = st.columns([1, 1])
with col_footer:
    st.caption("🚀 **Live Deployment Instance**")
    st.caption("Engine: [OpenOA v3.2](https://github.com/Anurag313y/OpenOA-Dashboard) | Powered by Streamlit")

