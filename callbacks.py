import dash
import plotly.graph_objects as go
from dash import dcc, Input, Output, State, ALL, callback_context
import plotly.io as pio
from utils import generate_figure, parse_contents
from layout import create_file_control


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
            # Normalize to list and use list comprehension.
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
        if not files:
            return go.Figure()
        # Ensure slider values lists match the number of files.
        if not bg_values or len(bg_values) != len(files):
            bg_values = [0] * len(files)
        if not int_values or len(int_values) != len(files):
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
        ctx = callback_context
        if not ctx.triggered:
            return current_min, current_max

        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger == "reset-button":
            return 10, 90

        if relayoutData:
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
            # Default to 4:3 aspect ratio if parsing fails.
            return {'position': 'relative', 'width': '100%', 'paddingBottom': '75%'}

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
        if not files:
            return dash.no_update
        fig = generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files)
        img_bytes = pio.to_image(fig, format='png', width=1600, height=1200, scale=2)
        def write_bytes(bytes_io):
            bytes_io.write(img_bytes)
        return dcc.send_bytes(write_bytes, "plot.png")