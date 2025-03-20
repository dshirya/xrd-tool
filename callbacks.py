import dash
import plotly.graph_objects as go
from dash import dcc, Input, Output, State, ALL, callback_context
import plotly.io as pio
import numpy as np
import io

from utils import generate_figure, parse_contents
from layout import create_file_control

def compute_default_angles(files):
    """
    Computes the default min and max angles from the uploaded files.
    Reads the first column from each file (parsed as a string) using np.genfromtxt.
    """
    all_angles = []
    for file in files:
        try:
            data = np.genfromtxt(io.StringIO(file["content"]))
            if data.ndim < 2 or data.shape[1] < 2:
                continue
            angles = data[:, 0]
            all_angles.extend(angles)
        except Exception:
            continue
    if all_angles:
        return float(min(all_angles)), float(max(all_angles))
    return 10, 90  # Fallback defaults if no valid data is found.

def register_callbacks(app):
    # Callback: Update the file store when files are uploaded.
    @app.callback(
        Output("file-store", "data"),
        Input("upload-data", "contents"),
        State("upload-data", "filename"),
        State("file-store", "data")
    )
    def update_file_store(upload_contents, upload_filenames, current_files):
        current_files = current_files or []
        if upload_contents is not None:
            # Normalize to list.
            if not isinstance(upload_contents, list):
                upload_contents = [upload_contents]
                upload_filenames = [upload_filenames]
            new_files = [
                {"filename": fname, "content": parse_contents(contents)}
                for contents, fname in zip(upload_contents, upload_filenames)
            ]
            current_files.extend(new_files)
        return current_files

    # Callback: Update per-file controls based on current files.
    @app.callback(
        Output("per-file-controls-section", "children"),
        Input("file-store", "data")
    )
    def update_per_file_controls(files):
        if not files:
            return []
        return [create_file_control(i, file["filename"]) for i, file in enumerate(files)]

    # Callback: Toggle the legend store (flip True/False) when legend button is clicked.
    @app.callback(
        Output("legend-store", "data"),
        Input("legend-button", "n_clicks"),
        State("legend-store", "data"),
        prevent_initial_call=True
    )
    def toggle_legend(n_clicks, show_legend):
        return not show_legend

    # Callback: Update the graph based on slider inputs, files, and legend visibility.
    @app.callback(
        Output('graph', 'figure'),
        Input('angle-min-slider', 'value'),
        Input('angle-max-slider', 'value'),
        Input('global-sep-slider', 'value'),
        Input({'type': 'bg-slider', 'index': ALL}, 'value'),
        Input({'type': 'int-slider', 'index': ALL}, 'value'),
        Input('file-store', 'data'),
        Input('legend-store', 'data')  # <--- Legend visibility
    )
    def update_graph(angle_min, angle_max, global_sep, bg_values, int_values, files, show_legend):
        if not files:
            return go.Figure()
        # Ensure slider values lists match the number of files.
        if not bg_values or len(bg_values) != len(files):
            bg_values = [0] * len(files)
        if not int_values or len(int_values) != len(files):
            int_values = [100] * len(files)

        fig = generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files)
        # Here we apply the legend visibility:
        fig.update_layout(
            legend=dict(
                font=dict(family="Dejavu Sans", size=20),
                yanchor='top',
                xanchor='right',
                x=0.99,
                y=0.99,
            ),
            showlegend=show_legend
        )
        return fig

    # Combined Callback: Update angle sliders from file-store changes, reset-button, or graph relayout.
    @app.callback(
        Output('angle-min-slider', 'value'),
        Output('angle-max-slider', 'value'),
        Input('file-store', 'data'),
        Input('graph', 'relayoutData'),
        Input('reset-button', 'n_clicks'),
        State('angle-min-slider', 'value'),
        State('angle-max-slider', 'value')
    )
    def update_angle_sliders_combined(files, relayoutData, n_clicks, current_min, current_max):
        ctx = callback_context
        if not ctx.triggered:
            return current_min, current_max

        trigger = ctx.triggered[0]['prop_id']
        # If file-store was updated or reset is clicked, update to computed defaults.
        if trigger.startswith("file-store") or trigger.startswith("reset-button"):
            if files:
                new_min, new_max = compute_default_angles(files)
                return new_min, new_max
            return 10, 90

        # If the graph relayout triggered this callback.
        if trigger.startswith("graph"):
            if relayoutData:
                if 'xaxis.autorange' in relayoutData:
                    if files:
                        new_min, new_max = compute_default_angles(files)
                        return new_min, new_max
                    return 10, 90
                if 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
                    try:
                        new_min = float(relayoutData['xaxis.range[0]'])
                        new_max = float(relayoutData['xaxis.range[1]'])
                        return new_min, new_max
                    except Exception:
                        pass
            return current_min, current_max

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
        if not n_clicks or n_clicks == 0:
            raise dash.exceptions.PreventUpdate
        num_files = len(files) if files else 0
        bg_defaults = [0] * num_files
        int_defaults = [100] * num_files
        return 0, bg_defaults, int_defaults

    # Callback: Update the aspect ratio of the graph container.
    @app.callback(
        Output('graph-wrapper', 'style'),
        Input('width-ratio-input', 'value'),
        Input('height-ratio-input', 'value'),
        prevent_initial_call=True
    )
    def update_aspect_ratio(width_ratio, height_ratio):
        try:
            w = float(width_ratio)
            h = float(height_ratio)
            padding_bottom = f"{(h / w) * 100}%"
            return {'position': 'relative', 'width': '100%', 'paddingBottom': padding_bottom}
        except Exception:
            return {'position': 'relative', 'width': '100%', 'paddingBottom': '75%'}

    # Callback: Save the current plot in high resolution using the selected ratio.
        # Callback: Save the current plot in high resolution using the selected ratio.
    @app.callback(
        Output("download", "data"),
        Input("save-white-button", "n_clicks"),
        Input("save-transparent-button", "n_clicks"),
        State('angle-min-slider', 'value'),
        State('angle-max-slider', 'value'),
        State('global-sep-slider', 'value'),
        State({'type': 'bg-slider', 'index': ALL}, 'value'),
        State({'type': 'int-slider', 'index': ALL}, 'value'),
        State('file-store', 'data'),
        State('width-ratio-input', 'value'),
        State('height-ratio-input', 'value'),
        State('legend-store', 'data'),  # New state to capture legend toggle
        prevent_initial_call=True
    )
    def save_plot(n_white, n_transparent, angle_min, angle_max, global_sep,
                  bg_values, int_values, files, width_ratio, height_ratio, show_legend):
        if not files:
            return dash.no_update
        
        # Generate the figure as usual.
        fig = generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files)
        
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
        trigger = ctx.triggered[0]['prop_id']
        
        # If the transparent button was clicked, set a transparent background.
        if trigger.startswith("save-transparent-button"):
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
        # Otherwise (save-white-button), keep white background.
        
        # Apply the legend configuration and visibility.
        fig.update_layout(
            legend=dict(
                font=dict(family="Dejavu Sans", size=20),
                yanchor='top',
                xanchor='right',
                x=0.99,
                y=0.99,
            ),
            showlegend=show_legend
        )
        
        try:
            w_ratio = float(width_ratio)
            h_ratio = float(height_ratio)
            height = int(800 * (h_ratio / w_ratio))
        except Exception:
            height = 600

        img_bytes = pio.to_image(fig, format='png', width=800, height=height, scale=4)
        def write_bytes(bytes_io):
            bytes_io.write(img_bytes)
        
        # Set filename based on button type.
        if trigger.startswith("save-white-button"):
            filename = "plot_white.png"
        else:
            filename = "plot_transparent.png"
        
        return dcc.send_bytes(write_bytes, filename)