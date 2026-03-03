"""Motion Autoencoder tab — Encode/decode motion, show latent space."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Motion Autoencoder — LSTM VAE"),
        html.P("Generate random motion samples and visualize the latent space.", className="text-muted"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Number of samples"),
                dbc.Input(id="ae-n-samples", type="number", value=20, min=5, max=100),
            ], width=3),
            dbc.Col([
                dbc.Label("Sequence length"),
                dbc.Input(id="ae-seq-len", type="number", value=30, min=10, max=60),
            ], width=3),
            dbc.Col([
                dbc.Button("Generate & Encode", id="ae-run", color="success", className="mt-4"),
            ], width=3),
        ], className="mb-3"),
        dcc.Loading(html.Div(id="ae-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("ae-output", "children"),
        Input("ae-run", "n_clicks"),
        [
            Input("ae-n-samples", "value"),
            Input("ae-seq-len", "value"),
        ],
        prevent_initial_call=True,
    )
    def run_autoencoder(n_clicks, n_samples, seq_len):
        if not n_clicks:
            return ""

        from pet_soul.motion.motion_autoencoder import MotionAutoencoder
        import torch

        n_samples = int(n_samples or 20)
        seq_len = int(seq_len or 30)
        input_dim = 42  # 14 joints * 3 coords

        model = MotionAutoencoder(
            input_dim=input_dim, hidden_dim=128,
            latent_dim=64, seq_length=seq_len,
        )
        model.eval()

        # Generate random input sequences
        random_seqs = torch.randn(n_samples, seq_len, input_dim)

        # Encode all
        with torch.no_grad():
            recon, mu, logvar = model(random_seqs)
            latents = mu.numpy()

        # PCA to 2D for visualization
        centered = latents - latents.mean(axis=0)
        cov = np.cov(centered.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        top2 = eigvecs[:, -2:]
        projected = centered @ top2

        # Latent space scatter
        scatter_fig = go.Figure(go.Scatter(
            x=projected[:, 0], y=projected[:, 1],
            mode="markers",
            marker=dict(size=8, color=np.arange(n_samples), colorscale="Viridis"),
            text=[f"Sample {i}" for i in range(n_samples)],
        ))
        scatter_fig.update_layout(
            title="Latent Space (PCA 2D)", xaxis_title="PC1", yaxis_title="PC2",
            height=400, template="plotly_dark",
        )

        # Reconstruction error per sample
        errors = ((recon - random_seqs) ** 2).mean(dim=[1, 2]).numpy()
        error_fig = go.Figure(go.Bar(
            x=list(range(n_samples)), y=errors,
            marker_color="#FFAA00",
        ))
        error_fig.update_layout(
            title="Reconstruction Error (MSE)", xaxis_title="Sample", yaxis_title="MSE",
            height=300, template="plotly_dark",
        )

        # Sample a decoded motion
        sampled = model.sample(1)
        sample_fig = go.Figure()
        for j in range(min(5, input_dim // 3)):
            sample_fig.add_trace(go.Scatter(
                y=sampled[0, :, j * 3], mode="lines", name=f"Joint {j} x",
            ))
        sample_fig.update_layout(
            title="Sampled Motion (first 5 joints, x-coord)",
            xaxis_title="Frame", yaxis_title="Position",
            height=300, template="plotly_dark",
        )

        return html.Div([
            dcc.Graph(figure=scatter_fig),
            dcc.Graph(figure=error_fig),
            dcc.Graph(figure=sample_fig),
        ])
