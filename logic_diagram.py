from graphviz import Digraph

def create_logic_diagram():
    dot = Digraph('Project Logic Flow', comment='Logic Flow of the Rocket Telemetry System')
    dot.attr(rankdir='TB', size='15,20', ratio='fill', newrank='true')
    
    # Global Styles
    dot.attr('node', shape='box', style='filled', fontname='Arial', fontsize='12')
    dot.attr('edge', fontname='Arial', fontsize='10')

    # --- 1. USER INTERFACE (Frontend) ---
    with dot.subgraph(name='cluster_frontend') as c:
        c.attr(label='USER INTERFACE (Browser)', color='blue', bgcolor='#e6f2ff')
        
        # Landing Page
        c.node('LANDING', 'landing.html\n(Start Menu)', shape='oval', fillcolor='#ffcc00')
        
        # Visualizer Logic
        with dot.subgraph(name='cluster_vis') as vis:
            vis.attr(label='visualizer.html (3D View)', color='black', bgcolor='white')
            vis.node('VIS_INIT', 'Initialize Cesium Viewer\n(Load Terrain & Models)')
            vis.node('VIS_LOOP', 'Main Loop (50ms Interval)')
            vis.node('VIS_FETCH', 'Fetch /api/data')
            vis.node('VIS_UPDATE_UI', 'Update Text & Gauges')
            vis.node('VIS_UPDATE_3D', 'Update 3D Rocket\nPosition & Orientation')
            vis.node('VIS_CAM', 'Update Camera\n(Track/Free/Cockpit)')
            vis.node('VIS_SIM_INPUT', 'Read Sliders (Sim Mode)\nSend to /api/control')
            
            vis.edge('VIS_INIT', 'VIS_LOOP')
            vis.edge('VIS_LOOP', 'VIS_FETCH')
            vis.edge('VIS_FETCH', 'VIS_UPDATE_UI')
            vis.edge('VIS_UPDATE_UI', 'VIS_UPDATE_3D')
            vis.edge('VIS_UPDATE_3D', 'VIS_CAM')
            vis.edge('VIS_UPDATE_UI', 'VIS_SIM_INPUT', label='If Sim Mode')

        # Analytics Logic
        with dot.subgraph(name='cluster_ana') as ana:
            ana.attr(label='analytics.html (Data View)', color='black', bgcolor='white')
            ana.node('ANA_INIT', 'Initialize Charts (Chart.js)\nInitialize Plotly 3D')
            ana.node('ANA_LOOP', 'Main Loop (100ms Interval)')
            ana.node('ANA_FETCH', 'Fetch /api/data')
            ana.node('ANA_CALC', 'Physics Integration\n(Calc Velocity from Accel)')
            ana.node('ANA_UPDATE', 'Update 2D Charts & 3D Plot')
            
            ana.edge('ANA_INIT', 'ANA_LOOP')
            ana.edge('ANA_LOOP', 'ANA_FETCH')
            ana.edge('ANA_FETCH', 'ANA_CALC')
            ana.edge('ANA_CALC', 'ANA_UPDATE')

        c.edge('LANDING', 'VIS_INIT', label='Open Tab 1')
        c.edge('LANDING', 'ANA_INIT', label='Open Tab 2')

    # --- 2. BACKEND SERVER (Python Flask) ---
    with dot.subgraph(name='cluster_backend') as c:
        c.attr(label='BACKEND SERVER (app.py)', color='red', bgcolor='#ffe6e6')
        
        c.node('APP_START', 'Start Flask App\nInitialize Globals')
        c.node('API_DATA', 'Route: /api/data\n(Return JSON)')
        c.node('API_CONTROL', 'Route: /api/control\n(Update Sim Inputs)')
        c.node('API_START', 'Route: /api/start/<mode>\n(Launch Threads)')
        c.node('API_CSV', 'Route: /api/export_csv\n(Generate File)')
        
        # Threads
        c.node('THREAD_SERIAL', 'Thread: Serial Worker\n(Read USB Port)')
        c.node('THREAD_SIM', 'Thread: Sim Worker\n(Physics Engine)')
        
        c.node('GLOBAL_DATA', 'Global Telemetry Dict\n(Shared Memory)', shape='cylinder', fillcolor='lightgrey')
        
        c.edge('APP_START', 'API_START')
        c.edge('API_START', 'THREAD_SERIAL', label='Mode=LIVE')
        c.edge('API_START', 'THREAD_SIM', label='Mode=SIM')
        
        c.edge('THREAD_SERIAL', 'GLOBAL_DATA', label='Update Data')
        c.edge('THREAD_SIM', 'GLOBAL_DATA', label='Update Data')
        
        c.edge('GLOBAL_DATA', 'API_DATA', label='Read Data')
        c.edge('API_CONTROL', 'THREAD_SIM', label='Update Physics Inputs')
        c.edge('GLOBAL_DATA', 'API_CSV', label='Read Log')

    # --- 3. OFFLINE ANALYSIS ---
    with dot.subgraph(name='cluster_analysis') as c:
        c.attr(label='OFFLINE ANALYSIS (trajectory_analyzer.py)', color='green', bgcolor='#e6ffe6')
        c.node('ANA_LOAD', 'Load CSV File')
        c.node('ANA_SMOOTH', 'B-Spline Smoothing')
        c.node('ANA_PLOT', 'Generate 3D Plotly Graph')
        
        c.edge('ANA_LOAD', 'ANA_SMOOTH')
        c.edge('ANA_SMOOTH', 'ANA_PLOT')

    # --- INTER-SYSTEM CONNECTIONS ---
    
    # Frontend <-> Backend
    dot.edge('VIS_FETCH', 'API_DATA', label='HTTP GET', color='blue', penwidth='2.0')
    dot.edge('ANA_FETCH', 'API_DATA', label='HTTP GET', color='blue', penwidth='2.0')
    dot.edge('VIS_SIM_INPUT', 'API_CONTROL', label='HTTP POST', color='orange')
    
    # External Data
    dot.node('USB', 'USB Serial Port\n(Hardware)', shape='component', fillcolor='orange')
    dot.edge('USB', 'THREAD_SERIAL', label='Binary Stream')
    
    dot.node('CSV_FILE', 'voyager_log.csv', shape='note', fillcolor='yellow')
    dot.edge('API_CSV', 'CSV_FILE', label='Download')
    dot.edge('CSV_FILE', 'ANA_LOAD', label='Read')

    # Render
    dot.render('project_logic_flow', format='png', cleanup=True)
    print("Logic diagram generated: project_logic_flow.png")

if __name__ == '__main__':
    create_logic_diagram()