import io
import numpy as np
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter1d
import base64

def generate_figure(angle_min, angle_max, global_sep, bg_values, int_values, files):
    sigma = 0.1  # smoothing parameter
    fig = go.Figure()
    
    for idx, file in enumerate(files):
        name = file["filename"]
        # Remove .xy extension (case insensitive) from the legend label.
        if name.lower().endswith('.xy'):
            name = name[:-3]
            
        try:
            data = np.genfromtxt(io.StringIO(file["content"]))
        except Exception:
            continue
        
        if data.ndim < 2 or data.shape[1] < 2:
            continue
        
        x = data[:, 0]
        y = data[:, 1]
        
        # Filter data by the current angle range.
        mask = (x >= angle_min) & (x <= angle_max)
        x_filtered = x[mask]
        y_filtered = y[mask]
        
        # Apply Gaussian smoothing.
        y_smoothed = gaussian_filter1d(y_filtered, sigma=sigma)
        
        bg = bg_values[idx] if idx < len(bg_values) else 0
        intensity = int_values[idx] if idx < len(int_values) else 100
        
        # Normalize and scale the data.
        y_min = np.min(y_smoothed)
        y_max = np.max(y_smoothed)
        if y_max - y_min == 0:
            y_normalized = y_smoothed - y_min
        else: 
            y_normalized = (y_smoothed - y_min) / (y_max - y_min)
        y_scaled = y_normalized * intensity
        
        final_y = y_scaled + bg + (idx * global_sep)
        
        fig.add_trace(go.Scatter(
            x=x_filtered,
            y=final_y,
            mode='lines',
            name=name,
            line=dict(width=2)
        ))
    
    # Update layout with increased font sizes for titles and legend.
    fig.update_layout(
        xaxis_title="diffraction angle, 2<i>θ</i>",
        xaxis_title_font=dict(family="Dejavu Sans", size=22),
        yaxis_title="intensity, a.u.",
        yaxis_title_font=dict(family="Dejavu Sans", size=22),
        template="simple_white",
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            font=dict(family="Dejavu Sans", size=20),
            yanchor='top',
            xanchor='right',
            x=0.99,
            y=0.99,
        )
    )
    
    # Determine the x-axis range.
    x_range = angle_max - angle_min
    
    # Configure x-axis tick settings based on the range.
    if x_range < 15:
        # Create a list of integer tick marks within the angle range.
        tick_values = list(range(int(np.ceil(angle_min)), int(np.floor(angle_max)) + 1))
        fig.update_xaxes(
            tickmode="array",
            tickvals=tick_values,
            tickfont=dict(family="Dejavu Sans", size=22),
            ticks="outside",
            ticklen=10,
            showline=True,
            mirror=True,
            automargin=True
        )
    else:
        # For larger ranges, use major ticks every 10° with labels
        # and minor ticks every 1° (as small marks).
        major_start = int(np.floor(angle_min / 10.0)) * 10
        fig.update_xaxes(
            tickmode="linear",
            tick0=major_start,    # first major tick is multiple of 10 at or below angle_min
            dtick=10,             # major ticks every 10
            tickfont=dict(family="Dejavu Sans", size=22),
            ticks="outside",
            ticklen=10,
            showline=True,
            mirror=True,
            automargin=True,
            minor=dict(
                tickmode="linear",
                tick0=int(np.floor(angle_min)),  # first minor tick is integer at or below angle_min
                dtick=1,                         # minor ticks every 1 degree
                ticks="inside",
                ticklen=4
            )
        )
    
    # Configure y-axis with a complete box and proper tick fonts.
    fig.update_yaxes(
        tickfont=dict(family="Dejavu Sans", size=22),
        showline=True,
        mirror=True,
        automargin=True
    )
    
    # Force x-axis to display the full angle range, even if data doesn't cover it.
    fig.update_xaxes(range=[angle_min, angle_max])
    
    return fig

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return decoded.decode('utf-8')