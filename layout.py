from dash import dcc, html

def create_file_control(index, filename):
    """
    Creates the layout for per-file controls.
    Removes the '.xy' extension from the filename if it exists.
    The filename is rendered in a fixed-width container with text truncation.
    """
    corrected_filename = filename.replace(".xy", "")
    return html.Div([
        html.Div(
            corrected_filename,
            style={
                'display': 'inline-block',
                'width': '200px',
                'fontWeight': 'bold',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'whiteSpace': 'nowrap'
            },
            title=corrected_filename  # Displays the full filename on hover.
        ),
        html.Label("BG:", style={'margin-left': '20px'}),
        html.Div(
            dcc.Slider(
                id={'type': 'bg-slider', 'index': index},
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
                id={'type': 'int-slider', 'index': index},
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

def create_layout(app):
    # Upload component for drag & drop .xy files with light grey background.
    upload_component = dcc.Upload(
        id="upload-data",
        children=html.Div(
            "Drop .xy file(s) here or Click to upload",
            style={'width': '100%', 'textAlign': 'center'}
        ),
        style={
            'width': '90%',               # Container takes 90% of its parent width.
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'margin': '10px auto',        # Auto left/right margins to center it.
            'backgroundColor': 'lightgrey',
            'display': 'flex',            # Enable flexbox.
            'justifyContent': 'center',   # Center children horizontally.
            'alignItems': 'center'        # Center children vertically.
        },
        multiple=True 
    )

    # Store to hold the current file list.
    file_store = dcc.Store(id="file-store", data=[])

    # Ratio controls placed above the Angle min slider.
    ratio_controls = html.Div([
        html.Div([
            html.Label("Width:", style={'marginRight': '10px'}),
            dcc.Input(
                id='width-ratio-input',
                type='number',
                placeholder='e.g., 4',
                value=4,
                debounce=True,
                style={'width': '50px'}
            )
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("Height:", style={'marginRight': '10px'}),
            dcc.Input(
                id='height-ratio-input',
                type='number',
                placeholder='e.g., 3',
                value=3,
                debounce=True,
                style={'width': '50px'}
            )
        ], style={'display': 'inline-block'})
    ], style={'margin': '20px 10px', 'textAlign': 'center'})

    # Global slider controls.
    global_controls = html.Div([
        html.Div([
            html.Label("angle min:"),
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
        ], style={'margin': '10px', 'width': '45%', "display": "inline-block"}),
        html.Div([
            html.Label("angle max:"),
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
        ], style={'margin': '10px', 'width': '45%', "display": "inline-block"}),
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
        ], style={'margin': '20px', 'width': '90%'})
    ])

    # Container for per-file controls.
    per_file_controls_container = html.Div([
        html.Div(id="per-file-controls-section", style={'padding': '10px'})
    ])

    # Buttons and download component.
    reset_button = html.Button(
        "Reset", 
        id="reset-button", 
        n_clicks=0, 
        style={
            'margin': '10px',
            'padding': '15px 20px',
            'fontSize': '16px',
            'backgroundColor': 'orange',
            'border': 'none',
            'color': 'white',
            'borderRadius': '5px'
        }
    )
    save_button = html.Button(
        "Save Plot", 
        id="save-button", 
        n_clicks=0, 
        style={
            'margin': '10px',
            'padding': '15px 20px',
            'fontSize': '16px',
            'backgroundColor': 'green',
            'border': 'none',
            'color': 'white',
            'borderRadius': '5px'
        }
    )
    download_component = dcc.Download(id="download")

    # Graph container now only holds the graph.
    graph_container = html.Div(
        [
            html.Div(
                dcc.Graph(
                    id='graph',
                    config={'displayModeBar': True, 'doubleClick': 'reset'},
                    style={'position': 'absolute', 'top': 0, 'left': 0, 'right': 0, 'bottom': 0}
                ),
                style={
                    'position': 'relative',
                    'width': '100%',
                    'paddingBottom': '75%'  # Default 4:3 ratio
                },
                id='graph-wrapper'
            )
        ],
        style={
            'width': '50%',
            'position': 'relative',
            'borderRight': '2px solid black',  # Only a right border for the plot.
            'padding': '5px'
        }
    )

    # Controls container (takes up the other 50% of the window width).
    controls_container = html.Div(
        [
            # The horizontal divider is styled to connect with the plot's right border.
            reset_button,
            save_button,
            download_component,
            ratio_controls,
            global_controls,
            html.Hr(style={'border': 'none', 'borderTop': '2px solid black'}),  # You may leave this default hr or remove if unnecessary.
            per_file_controls_container,
            upload_component  # Only this component has a light grey background.
        ],
        style={'width': '50%'}
    )

    # Main layout: file store and a two-column layout for graph and controls.
    layout = html.Div([
        file_store,
        html.Div([graph_container, controls_container],
                 style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
    ], style={'font-family': 'Dejavu Sans'})
    
    return layout