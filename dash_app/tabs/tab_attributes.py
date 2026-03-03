"""Attribute Extractor tab — Upload image, show breed/color/marking probabilities."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import base64
import io
from PIL import Image


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Attribute Extractor — CLIP"),
        html.P("Upload a cropped pet image to extract breed, coat colors, and markings.", className="text-muted"),
        dcc.Upload(
            id="attr-upload",
            children=dbc.Button("Upload Image", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="attr-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("attr-output", "children"),
        Input("attr-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_extractor(contents):
        if not contents:
            return ""

        from pet_soul.appearance.attribute_extractor import AttributeExtractor

        _, b64 = contents.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

        extractor = AttributeExtractor(use_clip=True)

        # Breed
        breed, breed_conf = extractor.extract_breed(img)

        # Physical attributes
        attrs = extractor.extract_physical_attributes(img)
        coat_colors = extractor.extract_coat_colors(img)
        markings = extractor.extract_markings(img)

        # Breed result
        breed_text = f"**Breed:** {breed} ({breed_conf:.1%})"

        # Coat colors bar chart
        color_fig = go.Figure(go.Bar(
            y=[c for c, _ in coat_colors],
            x=[s for _, s in coat_colors],
            orientation="h",
            marker_color="#7EC850",
        ))
        color_fig.update_layout(
            title="Coat Colors", xaxis_title="Confidence",
            height=300, margin=dict(l=120, r=20, t=40, b=40),
            template="plotly_dark",
        )

        # Markings bar chart
        marking_fig = go.Figure(go.Bar(
            y=[m for m, _ in markings],
            x=[s for _, s in markings],
            orientation="h",
            marker_color="#FFAA00",
        ))
        marking_fig.update_layout(
            title="Markings", xaxis_title="Confidence",
            height=250, margin=dict(l=120, r=20, t=40, b=40),
            template="plotly_dark",
        )

        # Physical attributes table
        attr_rows = [html.Tr([html.Td(k), html.Td(str(v))]) for k, v in attrs.items()]
        attr_table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Attribute"), html.Th("Value")])),
             html.Tbody(attr_rows)],
            bordered=True, dark=True, striped=True, size="sm",
        )

        return html.Div([
            dcc.Markdown(breed_text),
            dcc.Graph(figure=color_fig),
            dcc.Graph(figure=marking_fig),
            html.H5("Physical Attributes", className="mt-3"),
            attr_table,
        ])
