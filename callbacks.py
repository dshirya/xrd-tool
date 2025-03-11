import dash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, ALL, callback_context
import plotly.io as pio
from utils import generate_figure, parse_contents

def register_callbacks(app):
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

    # Callback: Update per-file controls based on current files.
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
        ctx = callback_context  # Use the global callback_context
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