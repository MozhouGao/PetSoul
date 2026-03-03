"""Motion Features tab — Compute motion stats and show radar chart."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import base64
import tempfile
import os


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Motion Features"),
        html.P("Upload a pet video to compute motion statistics and display as radar chart.", className="text-muted"),
        dcc.Upload(
            id="mfeat-upload",
            children=dbc.Button("Upload Video", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="mfeat-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("mfeat-output", "children"),
        Input("mfeat-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_features(contents):
        if not contents:
            return ""

        from pet_soul.motion.pose_extractor import PoseExtractor
        from pet_soul.motion.lift_2d_to_3d import lift_sequence, smooth_trajectory
        from pet_soul.motion.motion_features import compute_motion_stats, FEATURE_NAMES

        # Decode video
        _, b64 = contents.split(",", 1)
        video_bytes = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(video_bytes)
        tmp.close()

        try:
            extractor = PoseExtractor()
            kp_2d = extractor.extract_from_video(tmp.name, max_frames=300)
        finally:
            os.unlink(tmp.name)

        if kp_2d is None or len(kp_2d) == 0:
            return dbc.Alert("No keypoints extracted", color="warning")

        # Lift to 3D and smooth
        kp_3d = lift_sequence(kp_2d[:, :, :2])
        kp_3d = smooth_trajectory(kp_3d)

        # Compute stats
        stats = compute_motion_stats(kp_3d)

        # Radar chart
        categories = list(FEATURE_NAMES)
        values = [stats.get(k, 0) for k in categories]
        # Normalize to 0-1 for radar
        max_vals = [max(abs(v), 1e-6) for v in values]
        norm_values = [v / m for v, m in zip(values, max_vals)]

        fig = go.Figure(go.Scatterpolar(
            r=norm_values + [norm_values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            fillcolor="rgba(126, 200, 80, 0.3)",
            line_color="#7EC850",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Motion Statistics (Normalized)",
            height=450, template="plotly_dark",
        )

        # Stats table
        rows = [html.Tr([html.Td(k), html.Td(f"{v:.4f}")]) for k, v in stats.items()]
        table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Metric"), html.Th("Value")])),
             html.Tbody(rows)],
            bordered=True, dark=True, striped=True, size="sm",
        )

        return html.Div([
            dcc.Graph(figure=fig),
            html.H5("Raw Values", className="mt-3"),
            table,
        ])
