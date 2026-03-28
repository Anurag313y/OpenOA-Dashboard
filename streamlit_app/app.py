"""OpenOA Streamlit Demo - Robust FE + BE."""
import streamlit as st
import os
from pathlib import Path
import shutil
from openoa import PlantData
from openoa.analysis import aep, wake_losses
from examples.project_ENGIE import prepare

st.set_page_config(page_title="OpenOA", page_icon="🌀", layout="wide")

st.title("🌀 OpenOA Dashboard")
st.markdown("NREL OpenOA wind plant analysis (AEP, wakes). ENGIE example auto-load.")

@st.cache_data
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
    @st.cache_data
    def aep_analysis():
        a = aep.create_MonteCarloAEP(plant)
        a.run(num_sim=50)
        return a
    aep_res = aep_analysis()
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
    @st.cache_data
    def wake_analysis():
        w = wake_losses.create_WakeLosses(plant)
        w.run(num_sim=50)
        return w
    wake_res = wake_analysis()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("POR Wake Loss", f"{wake_res.wake_losses_por_mean*100:.1f}%")
        st.metric("LT Wake Loss", f"{wake_res.wake_losses_lt_mean*100:.1f}%")
    wake_res.plot_wake_losses_by_wind_direction()
    wake_res.plot_wake_losses_by_wind_speed()

st.markdown("**Permanent Live App:** Streamlit Cloud: GitHub `NatLabRockies/OpenOA` branch `blackboxai/streamlit-deploy` path `streamlit_app/app.py`. Link: https://yourapp.streamlit.app")

