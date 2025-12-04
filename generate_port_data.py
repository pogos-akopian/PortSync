import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_data():
    """
    Generates a synthetic dataset for PortSync representing 100 tanker voyages.
    """
    np.random.seed(42) # Ensure reproducibility
    n_vessels = 100
    
    # 1. Vessel_ID
    vessel_ids = [f"TANKER-{i:03d}" for i in range(1, n_vessels + 1)]
    
    # 2. Arrival_Date (Last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    arrival_dates = [start_date + timedelta(days=np.random.randint(0, 90)) for _ in range(n_vessels)]
    arrival_dates.sort() # Sort by date for realism
    
    # 3. Queue_Size (0-5) with specific weights
    # Weights: 0=30%, 1-2=50%, 3-5=20%
    # 0: 30%, 1: 25%, 2: 25%, 3: 6.6%, 4: 6.7%, 5: 6.7% (approx to sum to 20%)
    queue_probs = [0.30, 0.25, 0.25, 0.07, 0.07, 0.06] 
    queue_sizes = np.random.choice([0, 1, 2, 3, 4, 5], size=n_vessels, p=queue_probs)
    
    # 4. Waiting_Days
    # If Queue=0, then 0. If Queue>0, random float 1.0-4.0
    waiting_days = []
    for q in queue_sizes:
        if q == 0:
            waiting_days.append(0.0)
        else:
            waiting_days.append(np.round(np.random.uniform(1.0, 4.0), 2))
    
    # 5. Actual_Speed_Knots (Normal dist around 14.0)
    actual_speeds = np.round(np.random.normal(14.0, 1.0, n_vessels), 1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Vessel_ID': vessel_ids,
        'Arrival_Date': arrival_dates,
        'Queue_Size': queue_sizes,
        'Waiting_Days': waiting_days,
        'Actual_Speed_Knots': actual_speeds
    })
    
    # --- Business Logic (Calculated Columns) ---
    
    # Demurrage_Cost: Waiting_Days * $30,000
    df['Demurrage_Cost'] = df['Waiting_Days'] * 30000
    
    # Fuel_Consumed_Tons: Random between 500-800
    df['Fuel_Consumed_Tons'] = np.random.randint(500, 801, size=n_vessels)
    
    # Optimal_Speed_Knots
    # Simplification: Just multiply Actual_Speed by 0.75 for rows with waiting time (Queue > 0).
    # Otherwise keep Actual_Speed.
    df['Optimal_Speed_Knots'] = np.where(
        df['Queue_Size'] > 0,
        np.round(df['Actual_Speed_Knots'] * 0.75, 1),
        df['Actual_Speed_Knots']
    )
    
    # Potential_Fuel_Savings_USD
    # Assume sailing slower saves 15% fuel cost per day of delay avoided.
    # Logic interpretation: If we slowed down to avoid waiting, we save fuel.
    # The prompt says: "Assume sailing slower saves 15% fuel cost per day of delay avoided."
    # This implies the savings is proportional to the waiting time we are avoiding by slowing down.
    # Let's calculate Fuel Cost first. Price per ton = $600.
    fuel_price_per_ton = 600
    df['Total_Fuel_Cost'] = df['Fuel_Consumed_Tons'] * fuel_price_per_ton
    
    # Savings: 15% of Total Fuel Cost * Waiting Days? 
    # Or is it 15% savings on the voyage fuel for every day of delay?
    # "saves 15% fuel cost per day of delay avoided" -> 
    # If I wait 2 days, and I slow down to arrive 2 days later, I avoid 2 days of delay.
    # So I save 15% * 2 = 30% of fuel cost? That seems high but let's follow the logic.
    # Let's cap it reasonably or just use the formula: Savings = Fuel_Cost * 0.15 * Waiting_Days
    # Only applicable if Queue > 0.
    
    df['Potential_Fuel_Savings_USD'] = np.where(
        df['Queue_Size'] > 0,
        np.round(df['Total_Fuel_Cost'] * 0.15 * df['Waiting_Days'], 2),
        0.0
    )
    
    # Clean up temp columns if needed, but Total_Fuel_Cost is useful context.
    
    # Save to CSV
    output_file = 'port_traffic.csv'
    try:
        df.to_csv(output_file, index=False)
        print(f"Successfully generated {output_file} with {len(df)} records.")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    generate_data()
