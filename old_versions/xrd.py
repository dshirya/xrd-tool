import os
import glob
import numpy as np
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter1d
import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.io as pio

# ----- User Variables -----
directory = "/Users/danila/Downloads/XRD_pr8/Y"

# Get sorted list of .xy files
pattern_files = sorted(glob.glob(os.path.join(directory, "*.xy")))
if not pattern_files:
    raise FileNotFoundError(f"No .xy files found in directory: {directory}")

file_names = [os.path.basename(f) for f in pattern_files]

app = dash.Dash(__name__)

def generate_figure(angle_min, angle_max, global_sep, bg_values, int_values):
    sigma = 0.1  # smoothing parameter
    fig = go.Figure()
    
    for idx, filepath in enumerate(pattern_files):
        name = os.path.basename(filepath)
        data = np.loadtxt(filepath)
        x = data[:, 0]
        y = data[:, 1]
        
        # Filter data by the current angle range
        mask = (x >= angle_min) & (x <= angle_max)
        x_filtered = x[mask]
        y_filtered = y[mask]
        
        # Apply Gaussian smoothing
        y_smoothed = gaussian_filter1d(y_filtered, sigma=sigma)
        
        # Get per-file background and intensity slider values
        bg = bg_values[idx]
        intensity = int_values[idx]
        
        # Normalize and scale the data
        y_min = np.min(y_smoothed)
        y_max = np.max(y_smoothed)
        if y_max - y_min == 0:
            y_normalized = y_smoothed - y_min
        else:
            y_normalized = (y_smoothed - y_min) / (y_max - y_min)
        y_scaled = y_normalized * intensity
        
        # Apply background shift and global separation offset
        final_y = y_scaled + bg + (idx * global_sep)
        
        fig.add_trace(go.Scatter(
            x=x_filtered,
            y=final_y,
            mode='lines',
            name=name,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        xaxis_title="2θ",
        template="simple_white",
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

# Global controls for angle and separation sliders (wrapped in Divs for styling)
global_controls = html.Div([
    html.Div([
        html.Label("Angle min:"),
        dcc.Slider(
            id='angle-min-slider',
            min=0,
            max=100,
            step=1,
            value=10,  # default set to 10
            updatemode="drag",
            marks={i: str(i) for i in range(0, 101, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px'}),
    
    html.Div([
        html.Label("Angle max:"),
        dcc.Slider(
            id='angle-max-slider',
            min=0,
            max=100,
            step=1,
            value=90,  # default set to 90
            updatemode="drag",
            marks={i: str(i) for i in range(0, 101, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px'}),
    
    html.Div([
        html.Label("Global Separation:"),
        dcc.Slider(
            id='global-sep-slider',
            min=0,
            max=100,
            step=1,
            value=0,
            updatemode="drag",
            marks={i: str(i) for i in range(0, 101, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px'})
])

# Per-file controls: each file gets a background (BG) and intensity slider.
per_file_controls = []
for i, name in enumerate(file_names):
    per_file_controls.append(
        html.Div([
            html.Span(name, style={'display': 'inline-block', 'width': '200px', 'fontWeight': 'bold'}),
            html.Label("BG:", style={'margin-left': '20px'}),
            html.Div(
                dcc.Slider(
                    id={'type': 'bg-slider', 'index': i},
                    min=-10,
                    max=50,
                    step=0.5,
                    value=0,  # default BG 0
                    updatemode="drag",
                    marks={-10: "-10", 0: "0", 50: "50"},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                style={'width': '300px', 'display': 'inline-block', 'margin-left': '10px'}
            ),
            html.Label("Int:", style={'margin-left': '20px'}),
            html.Div(
                dcc.Slider(
                    id={'type': 'int-slider', 'index': i},
                    min=1,
                    max=200,
                    step=1,
                    value=100,  # default Int 100
                    updatemode="drag",
                    marks={1: "1", 100: "100", 200: "200"},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                style={'width': '300px', 'display': 'inline-block', 'margin-left': '10px'}
            )
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'})
    )

per_file_controls_section = html.Div(per_file_controls, style={'padding': '10px'})

# Reset and Save buttons added to the controls
reset_button = html.Button("Reset", id="reset-button", n_clicks=0, style={'margin': '20px'})
save_button = html.Button("Save Plot", id="save-button", n_clicks=0, style={'margin': '20px'})

# The download component is hidden and will be triggered by the save button callback.
download_component = dcc.Download(id="download")

# App layout: two-column layout with the graph on the left (wrapped in a 4:3 ratio container) and controls on the right.
app.layout = html.Div([
    html.Div(
        html.Div(
            dcc.Graph(
                id='graph',
                config={'displayModeBar': True, 'doubleClick': 'reset'},
                style={'position': 'absolute', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0}
            ),
            style={
                'position': 'relative',
                'width': '100%',
                'paddingBottom': '75%'  # 75% for a 4:3 aspect ratio
            }
        ),
        style={'flex': '2'}
    ),
    html.Div(
        [
            reset_button,
            save_button,
            download_component,
            global_controls,
            html.Hr(),
            html.H3("Per-file Controls:"),
            per_file_controls_section
        ],
        style={'flex': '1', 'padding': '10px'}
    )
], style={'display': 'flex', 'flexDirection': 'row'})

# Callback to update the graph based on all slider inputs
@app.callback(
    Output('graph', 'figure'),
    Input('angle-min-slider', 'value'),
    Input('angle-max-slider', 'value'),
    Input('global-sep-slider', 'value'),
    Input({'type': 'bg-slider', 'index': ALL}, 'value'),
    Input({'type': 'int-slider', 'index': ALL}, 'value')
)
def update_graph(angle_min, angle_max, global_sep, bg_values, int_values):
    return generate_figure(angle_min, angle_max, global_sep, bg_values, int_values)

# Combined callback to update angle sliders either when zooming/panning on the graph or when the reset button is pressed.
@app.callback(
    Output('angle-min-slider', 'value'),
    Output('angle-max-slider', 'value'),
    Input('graph', 'relayoutData'),
    Input('reset-button', 'n_clicks'),
    State('angle-min-slider', 'value'),
    State('angle-max-slider', 'value')
)
def update_angle_sliders_and_reset(relayoutData, n_clicks, current_min, current_max):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger = None
    else:
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    # If the reset button was clicked, return default angle values (10 and 90)
    if trigger == "reset-button":
        return 10, 90
    if relayoutData is not None:
        if 'xaxis.autorange' in relayoutData:
            return 10, 90
        if 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
            try:
                new_min = int(float(relayoutData['xaxis.range[0]']))
                new_max = int(float(relayoutData['xaxis.range[1]']))
                return new_min, new_max
            except Exception:
                pass
    return current_min, current_max

# Callback to reset global separation and per-file controls when reset button is pressed.
@app.callback(
    Output('global-sep-slider', 'value'),
    Output({'type': 'bg-slider', 'index': ALL}, 'value'),
    Output({'type': 'int-slider', 'index': ALL}, 'value'),
    Input('reset-button', 'n_clicks')
)
def reset_controls(n_clicks):
    if n_clicks is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    bg_defaults = [0] * len(file_names)
    int_defaults = [100] * len(file_names)
    return 0, bg_defaults, int_defaults

# Callback to save the current plot in high resolution when the save button is clicked.
@app.callback(
    Output("download", "data"),
    Input("save-button", "n_clicks"),
    State('angle-min-slider', 'value'),
    State('angle-max-slider', 'value'),
    State('global-sep-slider', 'value'),
    State({'type': 'bg-slider', 'index': ALL}, 'value'),
    State({'type': 'int-slider', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def save_plot(n_clicks, angle_min, angle_max, global_sep, bg_values, int_values):
    fig = generate_figure(angle_min, angle_max, global_sep, bg_values, int_values)
    # Generate a high resolution PNG image (1600x1200 pixels, scale factor 2)
    img_bytes = pio.to_image(fig, format='png', width=1600, height=1200, scale=2)
    
    # Define a function that writes the bytes to a file-like object
    def write_bytes(bytes_io):
        bytes_io.write(img_bytes)
    
    return dcc.send_bytes(write_bytes, "plot.png")

if __name__ == '__main__':
    app.run_server(debug=True)