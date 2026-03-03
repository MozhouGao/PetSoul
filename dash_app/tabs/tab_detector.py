"""Pet Detector tab — Upload image, run YOLOv8 detection, show bbox overlay."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import base64
import io
from PIL import Image


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Pet Detector — YOLOv8 Nano"),
        html.P("Upload a pet image to detect and crop the pet.", className="text-muted"),
        dcc.Upload(
            id="det-upload",
            children=dbc.Button("Upload Image", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="det-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("det-output", "children"),
        Input("det-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_detector(contents):
        if not contents:
            return ""

        from pet_soul.appearance.pet_detector import PetDetector

        _, b64 = contents.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

        detector = PetDetector()
        if not detector.is_ready():
            return dbc.Alert("YOLOv8 model not loaded", color="danger")

        result = detector.detect(img)

        fig = go.Figure(go.Image(z=img))
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=450)

        if result:
            x1, y1, x2, y2 = result["bbox"]
            species = result.get("species", "pet")
            conf = result.get("confidence", 0)
            fig.add_shape(
                type="rect", x0=x1, y0=y1, x1=x2, y1=y2,
                line=dict(color="lime", width=3),
            )
            fig.update_layout(title=f"Detected: {species} ({conf:.1%})")

            cropped = detector.crop_pet(img, result["bbox"])
            crop_fig = go.Figure(go.Image(z=cropped))
            crop_fig.update_layout(
                title="Cropped Region", margin=dict(l=0, r=0, t=40, b=0), height=300,
            )

            return html.Div([
                dcc.Graph(figure=fig),
                html.Hr(),
                dcc.Graph(figure=crop_fig),
            ])
        else:
            fig.update_layout(title="No pet detected")
            return dcc.Graph(figure=fig)
