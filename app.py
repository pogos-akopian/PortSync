import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# 1. Header & Configuration
st.set_page_config(
    page_title="PortSync: Just-In-Time Logistics Optimizer",
    page_icon="⚓",
    layout="wide"
)

st.title("⚓ PortSync: Just-In-Time Logistics Optimizer")
st.markdown("Optimize your fleet's arrival to reduce demurrage costs and save fuel.")

# Load Data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('port_traffic.csv')
        return df
    except FileNotFoundError:
        st.error("Data file 'port_traffic.csv' not found. Please run the generation script.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 2. Top Row (Metrics)
    # Total Demurrage Wasted
    total_demurrage = df['Demurrage_Cost'].sum()
    
    # Potential Fuel Savings
    total_savings = df['Potential_Fuel_Savings_USD'].sum()
    
    # Fleet Efficiency Score (100 - % of ships that waited)
    # Waited means Waiting_Days > 0 (or Queue_Size > 0)
    ships_waited = df[df['Waiting_Days'] > 0].shape[0]
    total_ships = df.shape[0]
    efficiency_score = 100 - (ships_waited / total_ships * 100)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Demurrage Wasted",
            value=f"${total_demurrage:,.0f}",
            delta="- Lost Money",
            delta_color="inverse" # Red if positive (bad)
        )
        
    with col2:
        st.metric(
            label="Potential Fuel Savings",
            value=f"${total_savings:,.0f}",
            delta="+ Savings",
            delta_color="normal" # Green if positive (good)
        )
        
    with col3:
        st.metric(
            label="Fleet Efficiency Score",
            value=f"{efficiency_score:.1f}%",
            delta=f"{'High' if efficiency_score > 80 else 'Low'} Efficiency"
        )

    st.divider()

    # 3. Main Visual: Actual Cost vs Optimized Cost
    # Top 10 most expensive trips (by Demurrage + Fuel Cost)
    # We need to calculate Actual Total Cost and Optimized Total Cost
    # Actual Total Cost = Demurrage_Cost + Total_Fuel_Cost
    # Optimized Total Cost = Total_Fuel_Cost - Potential_Fuel_Savings_USD (Assuming 0 demurrage if optimized)
    
    # Re-calculate Total_Fuel_Cost if not in CSV (it was calculated in generation but maybe not saved or we want to be sure)
    # The generation script saved 'Total_Fuel_Cost' so we can use it.
    
    df['Actual_Total_Cost'] = df['Demurrage_Cost'] + df['Total_Fuel_Cost']
    df['Optimized_Total_Cost'] = df['Total_Fuel_Cost'] - df['Potential_Fuel_Savings_USD']
    
    top_10_expensive = df.nlargest(10, 'Actual_Total_Cost')
    
    # Prepare data for Altair (melt/long format)
    chart_data = top_10_expensive[['Vessel_ID', 'Actual_Total_Cost', 'Optimized_Total_Cost']].melt(
        id_vars='Vessel_ID', 
        var_name='Cost_Type', 
        value_name='Cost'
    )
    
    st.subheader("Top 10 Most Expensive Voyages: Actual vs. Optimized")
    
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Vessel_ID', sort='-y', title='Vessel'),
        y=alt.Y('Cost', title='Cost (USD)'),
        color=alt.Color('Cost_Type', legend=alt.Legend(title="Cost Scenario"), scale=alt.Scale(scheme='tableau10')),
        tooltip=['Vessel_ID', 'Cost_Type', alt.Tooltip('Cost', format='$,.0f')]
    ).properties(
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

    # 4. Sidebar (The Recommendation Engine)
    st.sidebar.header("🚀 JIT Recommendation Engine")
    st.sidebar.markdown("Calculate optimal speed to avoid queuing.")
    
    distance_nm = st.sidebar.number_input("Distance to Port (nm)", min_value=100, value=1000, step=50)
    current_queue = st.sidebar.number_input("Current Queue (ships)", min_value=0, value=2, step=1)
    
    # Logic: If Queue > 1, suggest slowing down by 20% to save fuel.
    if current_queue > 1:
        recommendation = "SLOW STEAMING RECOMMENDED"
        speed_factor = 0.8
        alert_type = "success"
    else:
        recommendation = "MAINTAIN SPEED"
        speed_factor = 1.0
        alert_type = "info"
        
    st.sidebar.subheader(f"Status: {recommendation}")
    
    if current_queue > 1:
        st.sidebar.info(f"Reduce speed by 20% to arrive after queue clears.")
        
        # Money Saved Estimate
        # Rough calc: 15% savings on fuel for the trip? Or just a fixed estimate?
        # Prompt: "Display a 'Money Saved' estimate box in the sidebar."
        # Let's use a simple formula based on distance and assumed fuel consumption.
        # Assume 30 tons/day at normal speed.
        # Normal days = Distance / (14 knots * 24)
        # Fuel cost = Normal days * 30 * $600
        # Savings = Fuel cost * 0.15
        
        avg_speed = 14.0
        days_at_sea = distance_nm / (avg_speed * 24)
        est_fuel_cost = days_at_sea * 30 * 600
        est_savings = est_fuel_cost * 0.15
        
        st.sidebar.metric("Estimated Fuel Savings", f"${est_savings:,.0f}")
    else:
        st.sidebar.write("Port is clear. Proceed at normal service speed.")

    # 5. Data Table
    st.subheader("Voyage Data Log")
    
    # Highlight high Demurrage
    # We'll use pandas styling
    def highlight_demurrage(val):
        color = 'red' if val > 50000 else 'black'
        return f'color: {color}'

    st.dataframe(
        df.style.format({
            'Demurrage_Cost': '${:,.0f}',
            'Total_Fuel_Cost': '${:,.0f}',
            'Potential_Fuel_Savings_USD': '${:,.0f}',
            'Waiting_Days': '{:.1f} days',
            'Actual_Speed_Knots': '{:.1f} kn'
        }).applymap(lambda x: 'background-color: #ffcccc' if x > 50000 else '', subset=['Demurrage_Cost']),
        use_container_width=True
    )

else:
    st.warning("No data available. Please generate the dataset.")
