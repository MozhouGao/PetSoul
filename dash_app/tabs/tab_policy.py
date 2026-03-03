"""Policy Network tab — Action selection with reward predictions."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Policy Network — Action Selection"),
        html.P("Given a latent state, see action probabilities and reward predictions.", className="text-muted"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Temperature"),
                dcc.Slider(id="pol-temp", min=0.1, max=5.0, step=0.1, value=1.0,
                           marks={0.1: "0.1", 1: "1.0", 3: "3.0", 5: "5.0"}),
            ], width=6),
            dbc.Col([
                dbc.Label("Lookahead depth"),
                dbc.Input(id="pol-lookahead", type="number", value=1, min=1, max=5),
            ], width=3),
            dbc.Col([
                dbc.Button("Select Action", id="pol-run", color="success", className="mt-4"),
            ], width=3),
        ], className="mb-3"),
        dcc.Loading(html.Div(id="pol-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("pol-output", "children"),
        Input("pol-run", "n_clicks"),
        Input("pol-temp", "value"),
        Input("pol-lookahead", "value"),
        prevent_initial_call=True,
    )
    def run_policy(n_clicks, temperature, lookahead):
        if not n_clicks:
            return ""

        from pet_soul.world_model.latent_dynamics import LatentDynamicsModel
        from pet_soul.world_model.policy_network import (
            PolicyNetwork, RewardPredictor, ACTION_NAMES, NUM_ACTIONS,
        )
        import torch

        latent_dim = 32
        temperature = float(temperature or 1.0)
        lookahead = int(lookahead or 1)

        dynamics = LatentDynamicsModel(latent_dim=latent_dim, action_dim=NUM_ACTIONS)
        reward = RewardPredictor(latent_dim=latent_dim)
        policy = PolicyNetwork(dynamics=dynamics, reward=reward, temperature=temperature)

        dynamics.eval()
        reward.eval()

        # Random initial state
        z = torch.randn(latent_dim)
        z_np = z.numpy()

        # Get rewards for each action
        rewards = []
        for action_id in range(NUM_ACTIONS):
            z_next = dynamics.predict(z_np, action_id)
            r = reward(torch.tensor(z_next, dtype=torch.float32)).item()
            rewards.append(r)

        # Softmax probabilities
        rewards_arr = np.array(rewards)
        logits = rewards_arr / temperature
        logits -= logits.max()
        probs = np.exp(logits) / np.exp(logits).sum()

        selected = policy.select_action_name(z_np, lookahead=lookahead)

        # Create plots
        colors = ["#7EC850", "#55FFFF", "#FF5555", "#FFAA00", "#AA55FF"]
        highlight = [c if name != selected else "#FFFFFF" for name, c in zip(ACTION_NAMES, colors)]

        fig = make_subplots(rows=1, cols=2, subplot_titles=["Action Probabilities", "Predicted Rewards"])

        fig.add_trace(
            go.Bar(
                x=ACTION_NAMES, y=probs,
                marker_color=highlight, name="Probability",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Bar(
                x=ACTION_NAMES, y=rewards,
                marker_color=colors, name="Reward",
            ),
            row=1, col=2,
        )

        fig.update_layout(height=400, template="plotly_dark", showlegend=False)

        return html.Div([
            dbc.Alert([
                html.Strong(f"Selected action: {selected}"),
                html.Span(f" (temperature={temperature}, lookahead={lookahead})"),
            ], color="success"),
            dcc.Graph(figure=fig),
        ])
