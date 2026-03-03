"""Pose Extractor tab — Upload video, show skeleton overlay + keypoint trajectories."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import base64
import tempfile
import os


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Pose Extractor — MediaPipe"),
        html.P("Upload a pet video to extract 2D keypoints.", className="text-muted"),
        dcc.Upload(
            id="pose-upload",
            children=dbc.Button("Upload Video", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="pose-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("pose-output", "children"),
        Input("pose-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_pose(contents):
        if not contents:
            return ""

        from pet_soul.motion.pose_extractor import PoseExtractor, PET_KEYPOINT_NAMES

        # Decode and save to temp file
        _, b64 = contents.split(",", 1)
        video_bytes = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(video_bytes)
        tmp.close()

        try:
            extractor = PoseExtractor()
            keypoints = extractor.extract_from_video(tmp.name, max_frames=300)
        finally:
            os.unlink(tmp.name)

        if keypoints is None or len(keypoints) == 0:
            return dbc.Alert("No keypoints extracted", color="warning")

        T, J, _ = keypoints.shape

        # Keypoint trajectory plot (x and y over time for each joint)
        fig = make_subplots(rows=2, cols=1, subplot_titles=["X Position", "Y Position"])
        for j in range(min(J, len(PET_KEYPOINT_NAMES))):
            name = PET_KEYPOINT_NAMES[j]
            fig.add_trace(
                go.Scatter(y=keypoints[:, j, 0], mode="lines", name=name, showlegend=True),
                row=1, col=1,
            )
            fig.add_trace(
                go.Scatter(y=keypoints[:, j, 1], mode="lines", name=name, showlegend=False),
                row=2, col=1,
            )

        fig.update_layout(
            height=600, template="plotly_dark",
            title=f"Keypoint Trajectories ({T} frames, {J} joints)",
        )
        fig.update_xaxes(title_text="Frame")

        # Visibility heatmap
        vis = keypoints[:, :, 2] if keypoints.shape[2] > 2 else np.ones((T, J))
        vis_fig = go.Figure(go.Heatmap(
            z=vis.T,
            y=PET_KEYPOINT_NAMES[:J],
            colorscale="Greens",
            colorbar_title="Visibility",
        ))
        vis_fig.update_layout(
            title="Keypoint Visibility", xaxis_title="Frame",
            height=350, template="plotly_dark",
        )

        return html.Div([
            dbc.Alert(f"Extracted {T} frames, {J} keypoints", color="info"),
            dcc.Graph(figure=fig),
            dcc.Graph(figure=vis_fig),
        ])
