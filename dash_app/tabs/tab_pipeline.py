"""Full Pipeline tab — Upload image, run complete detection + extraction + prompt."""

from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import base64
import io
from PIL import Image


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Full Pipeline"),
        html.P("Run the complete appearance pipeline on an image.", className="text-muted"),
        dbc.Checklist(
            id="pipe-options",
            options=[{"label": " Skip 3D generation (saves Meshy credits)", "value": "skip_3d"}],
            value=["skip_3d"],
            className="mb-3",
        ),
        dcc.Upload(
            id="pipe-upload",
            children=dbc.Button("Upload Image", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="pipe-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("pipe-output", "children"),
        Input("pipe-upload", "contents"),
        State("pipe-options", "value"),
        prevent_initial_call=True,
    )
    def run_pipeline(contents, options):
        if not contents:
            return ""

        from pet_soul.appearance.pipeline import Pet3DModelPipeline

        _, b64 = contents.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

        skip_3d = "skip_3d" in (options or [])
        pipeline = Pet3DModelPipeline(use_clip=True)

        if skip_3d:
            # Run detection + extraction only
            if not pipeline.detector.is_ready():
                return dbc.Alert("Pipeline not ready", color="danger")

            det = pipeline.detector.detect(img)
            if not det:
                return dbc.Alert("No pet detected", color="warning")

            cropped = pipeline.detector.crop_pet(img, det["bbox"])
            profile = pipeline.extractor.extract_all(cropped) if hasattr(pipeline, 'extractor') else {}
            prompt = ""
            if hasattr(pipeline, 'prompt_builder'):
                prompt = pipeline.prompt_builder.build(profile) if profile else ""

            result = {"profile": profile, "prompt": prompt}
        else:
            result = pipeline.process(img)

        if "error" in result:
            return dbc.Alert(f"Error: {result['error']}", color="danger")

        profile = result.get("profile", {})
        prompt = result.get("prompt", "")

        # Profile table
        if hasattr(profile, '__dict__'):
            items = vars(profile).items()
        elif isinstance(profile, dict):
            items = profile.items()
        else:
            items = []

        rows = [html.Tr([html.Td(str(k)), html.Td(str(v))]) for k, v in items]
        profile_table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Field"), html.Th("Value")])),
             html.Tbody(rows)],
            bordered=True, dark=True, striped=True, size="sm",
        )

        parts = [
            html.H5("Pet Profile", className="mt-2"),
            profile_table,
        ]

        if prompt:
            parts += [
                html.H5("Texture Prompt", className="mt-3"),
                html.Pre(prompt, style={
                    "background": "#1a1a2e", "padding": "12px",
                    "borderRadius": "4px", "color": "#7EC850",
                }),
            ]

        model_path = result.get("model_path")
        if model_path:
            parts.append(dbc.Alert(f"3D model saved: {model_path}", color="success"))

        return html.Div(parts)
