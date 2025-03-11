import io
import numpy as np
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter1d

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
    
    fig.update_layout(
        xaxis_title="2θ",
        template="simple_white",
        autosize=True,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    return fig

def parse_contents(contents):
    import base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    return decoded.decode('utf-8')