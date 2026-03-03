"""Audio Feature Extractor tab — Upload audio, show waveform + MFCC spectrogram."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import base64
import tempfile
import os


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Audio Feature Extractor"),
        html.P("Upload an audio file to visualize waveform, MFCC, and statistics.", className="text-muted"),
        dcc.Upload(
            id="afeat-upload",
            children=dbc.Button("Upload Audio", color="success", className="mb-3"),
            multiple=False,
        ),
        dcc.Loading(html.Div(id="afeat-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("afeat-output", "children"),
        Input("afeat-upload", "contents"),
        prevent_initial_call=True,
    )
    def run_features(contents):
        if not contents:
            return ""

        from pet_soul.audio.feature_extractor import load_audio, extract_mfcc, extract_audio_stats

        # Decode audio
        _, b64 = contents.split(",", 1)
        audio_bytes = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(audio_bytes)
        tmp.close()

        try:
            waveform, sr = load_audio(tmp.name)
            mfcc = extract_mfcc(waveform, sr)
            stats = extract_audio_stats(waveform, sr)
        finally:
            os.unlink(tmp.name)

        # Waveform plot
        t = np.arange(len(waveform)) / sr
        wave_fig = go.Figure(go.Scatter(
            x=t, y=waveform, mode="lines", line=dict(color="#55FFFF", width=0.5),
        ))
        wave_fig.update_layout(
            title="Waveform", xaxis_title="Time (s)", yaxis_title="Amplitude",
            height=250, template="plotly_dark",
        )

        # MFCC spectrogram
        mfcc_fig = go.Figure(go.Heatmap(
            z=mfcc, colorscale="Viridis",
            colorbar_title="Coefficient",
        ))
        mfcc_fig.update_layout(
            title="MFCC Spectrogram",
            xaxis_title="Time Frame", yaxis_title="MFCC Bin",
            height=300, template="plotly_dark",
        )

        # Stats table
        rows = [html.Tr([html.Td(k), html.Td(f"{v:.4f}")]) for k, v in stats.items()]
        table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Statistic"), html.Th("Value")])),
             html.Tbody(rows)],
            bordered=True, dark=True, striped=True, size="sm",
        )

        return html.Div([
            dcc.Graph(figure=wave_fig),
            dcc.Graph(figure=mfcc_fig),
            html.H5("Audio Statistics", className="mt-3"),
            table,
        ])
