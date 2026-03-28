"""OpenOA Streamlit Demo - FE + BE Deployment"""
import streamlit as st
import os
from pathlib import Path
import zipfile
import pandas as pd
from openoa import PlantData
from openoa.analysis import aep, wake_losses
from openoa.utils import plot
from examples.project_ENGIE import extract_data, clean_scada, prepare

st.set_page_config(
    page_title="OpenOA Dashboard",
    page_icon="🌀",
    layout="wide"
)

st.title("🌀 OpenOA - Wind Plant Analysis Dashboard")
st.markdown("**Frontend + Backend Deployment** using NREL OpenOA library.")
st.markdown("Loads ENGIE *La Haute Borne* example data (4 turbines, 2014-2015). Runs Monte Carlo AEP and Wake Losses analyses.")

@st.cache_data
def load_example_data():
    """Extract and prepare ENGIE La Haute Borne data."""
    data_path = Path("data/la_haute_borne")
    if not data_path.exists():
        st.info("📦 Extracting example data...")
        zip_path = data_path.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(data_path.parent)
        st.success("Data extracted!")
    # Run prepare to clean/load PlantData
    plant = prepare(path=data_path, use_cleansed=False, return_value="plantdata")
    return plant

@st.cache_data
def run_aep(plant):
    """Run Monte Carlo AEP analysis."""
    aep_analysis = aep.create_MonteCarloAEP(plant)
    aep_analysis.run(num_sim=100)
    return aep_analysis

@st.cache_data
def run_wake(plant):
    """Run Wake Losses analysis."""
    wake_analysis = wake_losses.create_WakeLosses(plant)
    wake_analysis.run(num_sim=50)
    return wake_analysis

# Sidebar for options
st.sidebar.header("Options")
analysis_type = st.sidebar.selectbox("Analysis", ["AEP", "Wake Losses", "Both"])
use_example = st.sidebar.checkbox("Use ENGIE Example Data", value=True)

if use_example:
    if "plant" not in st.session_state:
        with st.spinner("Loading data & running analyses..."):
            st.session_state.plant = load_example_data()
            st.session_state.aep = run_aep(st.session_state.plant)
            st.session_state.wake = run_wake(st.session_state.plant)
    plant = st.session_state.plant
    aep_res = st.session_state.aep
    wake_res = st.session_state.wake
else:
    st.warning("Upload data for custom analysis.")

# Main page
tab1, tab2, tab3 = st.tabs(["Data", "Results", "Plots"])

with tab1:
    st.subheader("Plant Info")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Capacity", f"{plant.metadata.capacity:.1f} MW")
        st.metric("Turbines", plant.n_turbines)
    with col2:
        st.metric("Data Period", f"{plant.scada.index.get_level_values('time').min().strftime('%Y-%m-%d')} to {plant.scada.index.get_level_values('time').max().strftime('%Y-%m-%d')}")
    st.dataframe(plant.asset)

with tab2:
    if analysis_type in ("AEP", "Both"):
        st.subheader("AEP Results")
        col1, col2 = st.columns(2)
        with col1:
            mean_aep = aep_res.results['aep_GWh'].mean()
            p10_aep = aep_res.results['aep_GWh'].quantile(0.1)
            st.metric("Mean AEP", f"{mean_aep:.1f} GWh/yr", delta=f"P10: {p10_aep:.1f}")
        with col2:
            mean_avail = aep_res.results['avail_pct'].mean()
            mean_curt = aep_res.results['curt_pct'].mean()
            st.metric("LT Availability Loss", f"{mean_avail*100:.1f}%")
            st.metric("LT Curtailment Loss", f"{mean_curt*100:.1f}%")
        st.dataframe(aep_res.results.describe())

    if analysis_type in ("Wake Losses", "Both"):
        st.subheader("Wake Losses Results")
        col1, col2 = st.columns(2)
        with col1:
            mean_wake_por = wake_res.wake_losses_por_mean
            mean_wake_lt = wake_res.wake_losses_lt_mean
            st.metric("POR Plant Wake Loss", f"{mean_wake_por*100:.1f}%")
            st.metric("LT Plant Wake Loss", f"{mean_wake_lt*100:.1f}%")
        st.bar_chart(pd.DataFrame({
            'POR': [mean_wake_por],
            'LT': [mean_wake_lt],
            'LT Std': [wake_res.wake_losses_lt_std]
        }))

with tab3:
    if analysis_type in ("AEP", "Both"):
        st.subheader("AEP Distributions")
        aep_res.plot_result_aep_distributions()
    if analysis_type in ("Wake Losses", "Both"):
        st.subheader("Wake Losses vs Wind Direction")
        wake_res.plot_wake_losses_by_wind_direction()
        st.subheader("Wake Losses vs Wind Speed")
        wake_res.plot_wake_losses_by_wind_speed()

st.markdown("---")
st.markdown("**Permanent Deployment:** Commit & push to GitHub `blackboxai/streamlit-deploy` branch → [Streamlit Cloud](https://share.streamlit.io) for live app link.")
st.caption("Demo using OpenOA v3.x. Data: ENGIE La Haute Borne (CC-BY-4.0).")

