from dash import dcc, html

def create_layout(app):
    # Upload component for drag & drop .xy files.
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

    # Store to hold the current file list.
    file_store = dcc.Store(id="file-store", data=[])

    # Global slider controls.
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

    # Container for per-file controls (populated dynamically).
    per_file_controls_section = html.Div(id="per-file-controls-section", style={'padding': '10px'})

    # Buttons and download component.
    reset_button = html.Button("Reset", id="reset-button", n_clicks=0, style={'margin': '20px'})
    save_button = html.Button("Save Plot", id="save-button", n_clicks=0, style={'margin': '20px'})
    download_component = dcc.Download(id="download")

    # Graph container wrapped in a div with the CSS padding-bottom trick to enforce a 4:3 aspect ratio.
    graph_container = html.Div(
        html.Div(
            dcc.Graph(
                id='graph',
                config={'displayModeBar': True, 'doubleClick': 'reset'},
                style={'position': 'absolute', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0}
            ),
            style={
                'position': 'relative',
                'width': '100%',
                'paddingBottom': '75%'  # 75% padding gives a 4:3 ratio
            }
        ),
        style={'width': '50%', 'position': 'relative'}
    )

    # Controls container (takes up the other 50% of the window width).
    controls_container = html.Div(
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

    # Main layout: upload on top, then a two-column layout for graph and controls.
    layout = html.Div([
        upload_component,
        file_store,
        html.Div([graph_container, controls_container], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
    ])
    return layout