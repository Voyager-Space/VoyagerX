import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import splprep, splev
import os


CSV_FILE = 'voyager_log.csv'
THEME_COLOR = '#00f3ff'  
BG_COLOR = '#050814'     
GRID_COLOR = '#1c2b45'   

def generate_simulation_data():
    print("⚠️ No Log Found. Initiating Physics Simulation...")
    t = np.linspace(0, 30, 1000)
    
    
    z = 150 * np.log(t + 1) 
    r = 2 + 0.5 * t * np.sin(t/3) 
    theta = t * 0.5
    
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    
    noise = np.random.normal(0, 0.2, len(t))
    x += noise
    y += noise
    
    return pd.DataFrame({'X': x, 'Y': y, 'Altitude': z})

def smooth_trajectory(x, y, z, smoothing_factor=5):
    try:
       
        df = pd.DataFrame({'x':x, 'y':y, 'z':z}).drop_duplicates()
        
        if len(df) < 5: 
            return df.x.values, df.y.values, df.z.values 
        
        tck, u = splprep([df.x, df.y, df.z], s=smoothing_factor)
        new_points = splev(np.linspace(0, 1, len(df)*3), tck)
        return new_points[0], new_points[1], new_points[2]
    except Exception as e:
        print(f"Smoothing skipped: {e}")
        return x, y, z 

def load_data():
    try:
        if os.path.exists(CSV_FILE):
            print(f"📂 Loading Flight Log: {CSV_FILE}")
            df = pd.read_csv(CSV_FILE)
            
            
            if 'Height' in df.columns:
                df.rename(columns={'Height': 'Altitude'}, inplace=True)
            
            
            if 'Altitude' not in df.columns:
                raise ValueError("CSV missing 'Height' or 'Altitude' column")

            
            if 'Lat' in df.columns and 'Long' in df.columns:
                lat0 = df['Lat'].iloc[0]
                lon0 = df['Long'].iloc[0]
                
                
                df['X'] = (df['Long'] - lon0) * 111320 * np.cos(np.deg2rad(lat0))
                df['Y'] = (df['Lat'] - lat0) * 110574
            else:
                
                if 'X' not in df.columns:
                    df['X'] = 0
                    df['Y'] = 0
            
            return df
        else:
            return generate_simulation_data()
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return generate_simulation_data()

def create_dashboard():
    
    df = load_data()
    
    
    if df.empty:
        print("Data is empty. Exiting.")
        return

    raw_x, raw_y, raw_z = df['X'], df['Y'], df['Altitude']
    
    
    smooth_x, smooth_y, smooth_z = smooth_trajectory(raw_x, raw_y, raw_z, smoothing_factor=20)
    
    
    apogee_idx = np.argmax(smooth_z)
    apogee_pt = (smooth_x[apogee_idx], smooth_y[apogee_idx], smooth_z[apogee_idx])

    fig = go.Figure()

    fig.add_trace(go.Scatter3d(
        x=smooth_x, y=smooth_y, z=np.zeros_like(smooth_z),
        mode='lines',
        line=dict(color='gray', width=2, dash='dot'),
        name='Ground Shadow',
        hoverinfo='skip'
    ))

    fig.add_trace(go.Scatter3d(
        x=smooth_x, y=smooth_y, z=smooth_z,
        mode='lines',
        line=dict(
            color=smooth_z,
            colorscale='Turbo', 
            width=6,
            showscale=True,
            colorbar=dict(title="Alt (m)", x=0.9, tickfont=dict(color='white'))
        ),
        name='Flight Trajectory',
        hoverinfo='x+y+z'
    ))

    fig.add_trace(go.Scatter3d(
        x=[smooth_x[0], apogee_pt[0]],
        y=[smooth_y[0], apogee_pt[1]],
        z=[smooth_z[0], apogee_pt[2]],
        mode='markers+text',
        marker=dict(size=6, color=['green', 'white'], symbol='diamond'),
        text=['LAUNCH', f'APOGEE<br>{apogee_pt[2]:.1f}m'],
        textposition="top center",
        textfont=dict(color='white', size=12, family="Courier New"),
        name='Events'
    ))

    fig.update_layout(
        title={
            'text': "VOYAGER X /// POST-FLIGHT ANALYSIS",
            'y':0.9, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
            'font': dict(family="Arial Black", size=24, color=THEME_COLOR)
        },
        template="plotly_dark",
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        scene=dict(
            xaxis=dict(
                backgroundcolor=BG_COLOR, gridcolor=GRID_COLOR, showbackground=True,
                zerolinecolor=THEME_COLOR, title="EAST <-> WEST (m)"
            ),
            yaxis=dict(
                backgroundcolor=BG_COLOR, gridcolor=GRID_COLOR, showbackground=True,
                zerolinecolor=THEME_COLOR, title="NORTH <-> SOUTH (m)"
            ),
            zaxis=dict(
                backgroundcolor=BG_COLOR, gridcolor=GRID_COLOR, showbackground=True,
                zerolinecolor=THEME_COLOR, title="ALTITUDE (m)"
            ),
            aspectmode='data' 
        ),
        margin=dict(r=0, l=0, b=0, t=50)
    )

    print("🚀 Rendering High-Performance 3D Environment...")
    fig.show()

if __name__ == "__main__":
    create_dashboard()