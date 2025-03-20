from dash import dcc, html
import dash

def create_file_control(index, filename):
    """
    Creates the layout for per-file controls.
    Removes the '.xy' extension (case insensitive) from the filename if it exists.
    The filename is rendered in a fixed-width container with text truncation.
    """
    corrected_filename = filename
    if corrected_filename.lower().endswith('.xy'):
        corrected_filename = corrected_filename[:-3]
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
            title=corrected_filename
        ),
        html.Label("BG", style={'margin-left': '20px'}),
        html.Div(
            dcc.Slider(
                id={'type': 'bg-slider', 'index': index},
                min=-10,
                max=50,
                step=0.5,
                value=0,
                updatemode="drag",
                # Larger font for marks:
                marks={
                    -10: {'label': "-10", 'style': {'fontSize': '18px'}},
                     0:  {'label': "0",   'style': {'fontSize': '18px'}},
                     50: {'label': "50",  'style': {'fontSize': '18px'}}
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            style={'display': 'inline-block', 'margin-left': '10px', 'width': '80%'}
        ),
        html.Label("Int", style={'margin-left': '20px'}),
        html.Div(
            dcc.Slider(
                id={'type': 'int-slider', 'index': index},
                min=1,
                max=200,
                step=1,
                value=100,
                updatemode="drag",
                marks={
                    1:   {'label': "1",   'style': {'fontSize': '18px'}},
                    100: {'label': "100", 'style': {'fontSize': '18px'}},
                    200: {'label': "200", 'style': {'fontSize': '18px'}}
                },
                tooltip={"placement": "bottom", "always_visible": True}
            ),
            style={'display': 'inline-block', 'margin-left': '10px', 'width': '80%'}
        )
    ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'})

def create_layout(app):
    # Upload component for drag & drop .xy files with a light grey background.
    upload_component = dcc.Upload(
        id="upload-data",
        children=html.Div(
            "Drop .xy file(s) here or Click to upload",
            style={'width': '100%', 'textAlign': 'center'}
        ),
        style={
            'width': '90%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'margin': '10px auto',
            'backgroundColor': 'lightgrey',
            'display': 'flex',
            'justifyContent': 'center',
            'alignItems': 'center'
        },
        multiple=True 
    )

    # Store to hold the current file list.
    file_store = dcc.Store(id="file-store", data=[])

    # Ratio controls placed above the angle sliders.
    ratio_controls = html.Div([
        html.Div([
            html.Label("Width", style={'marginRight': '10px', 'fontSize': '18px'}),
            dcc.Input(
                id='width-ratio-input',
                type='number',
                placeholder='e.g., 4',
                value=4,
                debounce=True,
                style={
                    'width': '80px',
                    'height': '30px',
                    'fontSize': '16px'
                }
            )
        ], style={'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("Height", style={'marginRight': '10px', 'fontSize': '18px'}),
            dcc.Input(
                id='height-ratio-input',
                type='number',
                placeholder='e.g., 3',
                value=3,
                debounce=True,
                style={
                    'width': '80px',
                    'height': '30px',
                    'fontSize': '16px'
                }
            )
        ], style={'display': 'inline-block'}),
    ], style={'margin': '20px 10px', 'textAlign': 'center'})

    # Global slider controls.
    # Let's build the marks with bigger font:
    angle_marks = {i: {'label': str(i), 'style': {'fontSize': '18px'}} for i in range(0, 101, 10)}
    global_sep_marks = {i: {'label': str(i), 'style': {'fontSize': '18px'}} for i in range(0, 101, 10)}

    global_controls = html.Div([
        html.Div([
            html.Label("angle min", style={'fontSize': '18px'}),
            dcc.Slider(
                id='angle-min-slider',
                min=0,
                max=100,
                step=1,
                value=10,
                updatemode="drag",
                marks=angle_marks,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'margin': '10px', 'width': '45%', "display": "inline-block"}),
        html.Div([
            html.Label("angle max", style={'fontSize': '18px'}),
            dcc.Slider(
                id='angle-max-slider',
                min=0,
                max=100,
                step=1,
                value=90,
                updatemode="drag",
                marks=angle_marks,
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'margin': '10px', 'width': '45%', "display": "inline-block"}),
        html.Div([
            html.Label("Global Separation", style={'fontSize': '18px'}),
            dcc.Slider(
                id='global-sep-slider',
                min=0,
                max=100,
                step=1,
                value=0,
                updatemode="drag",
                marks=global_sep_marks,
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
            'padding': '15px 20px',
            'fontSize': '16px',
            'backgroundColor': 'orange',
            'border': 'none',
            'color': 'white',
            'borderRadius': '5px'
        }
    )
    save_white_button = html.Button(
        "Save Plot (White BG)", 
        id="save-white-button", 
        n_clicks=0, 
        style={
            'padding': '15px 20px',
            'fontSize': '16px',
            'backgroundColor': 'blue',
            'border': 'none',
            'color': 'white',
            'borderRadius': '5px',
        }
    )
    save_transparent_button = html.Button(
        "Save Plot (Transparent)", 
        id="save-transparent-button", 
        n_clicks=0, 
        style={
            'padding': '15px 20px',
            'fontSize': '16px',
            'backgroundColor': 'green',
            'border': 'none',
            'color': 'white',
            'borderRadius': '5px'
        }
    )
    download_component = dcc.Download(id="download")

    # Arrange Reset and Save buttons on the same horizontal line.
    button_row = html.Div(
        [
            reset_button,
            html.Div(
                [
                    save_white_button,
                    save_transparent_button
                ],
                style={'display': 'flex', 'gap': '10px', 'marginLeft': '20px'}
            )
        ],
        style={'display': 'flex', 'alignItems': 'center', 'margin': '10px'}
    )

    # Graph container holds the graph.
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
            'borderRight': '2px solid black',
            'padding': '5px'
        }
    )

    # Controls container (takes up the other 50% of the window width).
    controls_container = html.Div(
        [
            button_row,
            download_component,
            ratio_controls,
            global_controls,
            html.Hr(style={'border': 'none', 'borderTop': '2px solid black'}),
            per_file_controls_container,
            upload_component
        ],
        style={'width': '50%'}
    )

    # Main layout: file store and a two-column layout for graph and controls.
    layout = html.Div([
        file_store,
        html.Div([graph_container, controls_container],
                 style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
    ], 
    # Enforce a bigger default font:
    style={'font-family': 'Dejavu Sans', 'fontSize': '18px'}
    )
    
    return layout