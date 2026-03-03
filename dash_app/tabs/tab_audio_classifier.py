"""Audio Classifier tab — Upload audio, show vocal type + emotion bar charts."""

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
        html.H4("Audio Classifier — 1D CNN"),
        html.P("Upload a pet audio clip to classify vocal type and emotion.", className="text-muted"),
        dcc.Upload(
            id="aclass-upload",
            children=dbc.Button("Upload Audio", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="aclass-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("aclass-output", "children"),
        Input("aclass-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_classifier(contents):
        if not contents:
            return ""

        from pet_soul.audio.audio_classifier import (
            PetAudioClassifier, VOCAL_CLASSES, EMOTION_CLASSES,
        )
        from pet_soul.audio.feature_extractor import load_audio, extract_mfcc

        # Decode audio
        _, b64 = contents.split(",", 1)
        audio_bytes = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(audio_bytes)
        tmp.close()

        try:
            waveform, sr = load_audio(tmp.name)
            mfcc = extract_mfcc(waveform, sr)
        finally:
            os.unlink(tmp.name)

        classifier = PetAudioClassifier()
        result = classifier.classify(mfcc)

        # Vocal type bar chart
        vocal_probs = result.get("vocal_probs", [1.0 / len(VOCAL_CLASSES)] * len(VOCAL_CLASSES))
        emotion_probs = result.get("emotion_probs", [1.0 / len(EMOTION_CLASSES)] * len(EMOTION_CLASSES))

        fig = make_subplots(rows=1, cols=2, subplot_titles=["Vocal Type", "Emotion"])

        fig.add_trace(
            go.Bar(
                y=VOCAL_CLASSES, x=vocal_probs, orientation="h",
                marker_color="#7EC850", name="Vocal",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Bar(
                y=EMOTION_CLASSES, x=emotion_probs, orientation="h",
                marker_color="#FFAA00", name="Emotion",
            ),
            row=1, col=2,
        )

        fig.update_layout(height=350, template="plotly_dark", showlegend=False)

        vocal_type = result.get("vocal_type", "unknown")
        vocal_conf = result.get("vocal_confidence", 0)
        emotion = result.get("emotion", "unknown")
        emotion_conf = result.get("emotion_confidence", 0)

        return html.Div([
            dbc.Alert([
                html.Strong(f"Vocal: {vocal_type} ({vocal_conf:.1%})"),
                html.Span(" | "),
                html.Strong(f"Emotion: {emotion} ({emotion_conf:.1%})"),
            ], color="info"),
            dcc.Graph(figure=fig),
        ])
