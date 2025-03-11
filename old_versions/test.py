import base64
import io
import numpy as np
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter1d
import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.io as pio

# Start with an empty file list; files will be added via drag & drop.
initial_files = []

app = dash.Dash(__name__)

def generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files):
    sigma = 0.1  # smoothing parameter
    fig = go.Figure()
    
    for idx, file in enumerate(files):
        name = file["filename"]
        try:
            data = np.genfromtxt(io.StringIO(file["content"]))
        except Exception:
            continue
        
        if data.ndim < 2 or data.shape[1] < 2:
            continue
        
        x = data[:, 0]
        y = data[:, 1]
        
        # Filter data by the current angle range
        mask = (x >= angle_min) & (x <= angle_max)
        x_filtered = x[mask]
        y_filtered = y[mask]
        
        # Apply Gaussian smoothing
        y_smoothed = gaussian_filter1d(y_filtered, sigma=sigma)
        
        # Get slider values (defaulting if not available)
        bg = bg_values[idx] if idx < len(bg_values) else 0
        intensity = int_values[idx] if idx < len(int_values) else 100
        
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

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return decoded.decode('utf-8')

# Upload component for drag & drop of .xy files.
upload_component = dcc.Upload(
    id="upload-data",
    children=html.Div(["Drag and drop or click to upload .xy file(s)"]),
    style={
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px'
    },
    multiple=True
)

# Global slider controls with percentage widths for scalability.
global_controls = html.Div([
    html.Div([
        html.Label("Angle min:"),
        dcc.Slider(
            id='angle-min-slider',
            min=0,
            max=100,
            step=1,
            value=10,
            updatemode="drag",
            marks={i: str(i) for i in range(0, 101, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px', 'width': '90%'}),
    html.Div([
        html.Label("Angle max:"),
        dcc.Slider(
            id='angle-max-slider',
            min=0,
            max=100,
            step=1,
            value=90,
            updatemode="drag",
            marks={i: str(i) for i in range(0, 101, 10)},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '20px', 'width': '90%'}),
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
    ], style={'margin': '20px', 'width': '90%'}),
])

# This Div will hold dynamically created per-file controls.
per_file_controls_section = html.Div(id="per-file-controls-section", style={'padding': '10px'})

reset_button = html.Button("Reset", id="reset-button", n_clicks=0, style={'margin': '20px'})
save_button = html.Button("Save Plot", id="save-button", n_clicks=0, style={'margin': '20px'})
download_component = dcc.Download(id="download")

# Store to hold the current file list.
file_store = dcc.Store(id="file-store", data=initial_files)

# Main layout: two columns, each set to 50% of the window width.
app.layout = html.Div([
    upload_component,
    file_store,
    html.Div([
        # Graph container: always 50% of window width with a 4:3 aspect ratio.
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
                    'paddingBottom': '75%'  # 75% padding ensures a 4:3 ratio
                }
            ),
            style={'width': '50%', 'position': 'relative'}
        ),
        # Controls container: also 50% of window width.
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
            style={'width': '50%', 'padding': '10px'}
        )
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
])

# Callback: Update the file store when files are uploaded.
@app.callback(
    Output("file-store", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("file-store", "data")
)
def update_file_store(upload_contents, upload_filenames, current_files):
    if upload_contents is not None:
        new_files = []
        if isinstance(upload_contents, list):
            for contents, filename in zip(upload_contents, upload_filenames):
                content = parse_contents(contents)
                new_files.append({"filename": filename, "content": content})
        else:
            content = parse_contents(upload_contents)
            new_files.append({"filename": upload_filenames, "content": content})
        return new_files
    return current_files

# Callback: Dynamically update per-file controls based on current files.
@app.callback(
    Output("per-file-controls-section", "children"),
    Input("file-store", "data")
)
def update_per_file_controls(files):
    controls = []
    if files is None:
        return controls
    for i, file in enumerate(files):
        controls.append(
            html.Div([
                html.Span(file["filename"], style={'display': 'inline-block', 'width': '200px', 'fontWeight': 'bold'}),
                html.Label("BG:", style={'margin-left': '20px'}),
                html.Div(
                    dcc.Slider(
                        id={'type': 'bg-slider', 'index': i},
                        min=-10,
                        max=50,
                        step=0.5,
                        value=0,
                        updatemode="drag",
                        marks={-10: "-10", 0: "0", 50: "50"},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    style={'display': 'inline-block', 'margin-left': '10px', 'width': '80%'}
                ),
                html.Label("Int:", style={'margin-left': '20px'}),
                html.Div(
                    dcc.Slider(
                        id={'type': 'int-slider', 'index': i},
                        min=1,
                        max=200,
                        step=1,
                        value=100,
                        updatemode="drag",
                        marks={1: "1", 100: "100", 200: "200"},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    style={'display': 'inline-block', 'margin-left': '10px', 'width': '80%'}
                )
            ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'})
        )
    return controls

# Callback: Update the graph based on slider inputs and current files.
@app.callback(
    Output('graph', 'figure'),
    Input('angle-min-slider', 'value'),
    Input('angle-max-slider', 'value'),
    Input('global-sep-slider', 'value'),
    Input({'type': 'bg-slider', 'index': ALL}, 'value'),
    Input({'type': 'int-slider', 'index': ALL}, 'value'),
    Input('file-store', 'data')
)
def update_graph(angle_min, angle_max, global_sep, bg_values, int_values, files):
    if files is None or len(files) == 0:
        return go.Figure()
    if bg_values is None or len(bg_values) != len(files):
        bg_values = [0] * len(files)
    if int_values is None or len(int_values) != len(files):
        int_values = [100] * len(files)
    return generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files)

# Callback: Update angle sliders based on graph interactions or reset button.
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

# Callback: Reset global separation and per-file controls.
@app.callback(
    Output('global-sep-slider', 'value'),
    Output({'type': 'bg-slider', 'index': ALL}, 'value'),
    Output({'type': 'int-slider', 'index': ALL}, 'value'),
    Input('reset-button', 'n_clicks'),
    State('file-store', 'data')
)
def reset_controls(n_clicks, files):
    if n_clicks is None or n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    num_files = len(files) if files else 0
    bg_defaults = [0] * num_files
    int_defaults = [100] * num_files
    return 0, bg_defaults, int_defaults

# Callback: Save the current plot in high resolution when the save button is clicked.
@app.callback(
    Output("download", "data"),
    Input("save-button", "n_clicks"),
    State('angle-min-slider', 'value'),
    State('angle-max-slider', 'value'),
    State('global-sep-slider', 'value'),
    State({'type': 'bg-slider', 'index': ALL}, 'value'),
    State({'type': 'int-slider', 'index': ALL}, 'value'),
    State('file-store', 'data'),
    prevent_initial_call=True
)
def save_plot(n_clicks, angle_min, angle_max, global_sep, bg_values, int_values, files):
    if files is None or len(files) == 0:
        return dash.no_update
    fig = generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files)
    img_bytes = pio.to_image(fig, format='png', width=1600, height=1200, scale=2)
    def write_bytes(bytes_io):
        bytes_io.write(img_bytes)
    return dcc.send_bytes(write_bytes, "plot.png")

if __name__ == '__main__':
    app.run_server(debug=True)