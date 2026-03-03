"""Latent Dynamics tab — Run rollout trajectories per action."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Latent Dynamics Model"),
        html.P("Simulate state trajectories for each action from a random initial state.", className="text-muted"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Rollout steps"),
                dbc.Input(id="dyn-steps", type="number", value=10, min=1, max=30),
            ], width=3),
            dbc.Col([
                dbc.Button("Run Rollout", id="dyn-run", color="success", className="mt-4"),
            ], width=3),
        ], className="mb-3"),
        dcc.Loading(html.Div(id="dyn-output")),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("dyn-output", "children"),
        Input("dyn-run", "n_clicks"),
        Input("dyn-steps", "value"),
        prevent_initial_call=True,
    )
    def run_rollout(n_clicks, steps):
        if not n_clicks:
            return ""

        from pet_soul.world_model.latent_dynamics import LatentDynamicsModel
        from pet_soul.world_model.policy_network import ACTION_NAMES, NUM_ACTIONS
        import torch

        steps = int(steps or 10)
        latent_dim = 32

        model = LatentDynamicsModel(latent_dim=latent_dim, action_dim=NUM_ACTIONS)
        model.eval()

        # Random initial state
        z0 = torch.randn(latent_dim)

        # Rollout for each action
        trajectories = {}
        for action_id, action_name in enumerate(ACTION_NAMES):
            action_seq = [action_id] * steps
            traj = model.rollout(z0.numpy(), action_seq, steps=steps)
            trajectories[action_name] = traj

        # Plot L2 norm of latent state over time for each action
        norm_fig = go.Figure()
        colors = ["#7EC850", "#55FFFF", "#FF5555", "#FFAA00", "#AA55FF"]
        for i, (name, traj) in enumerate(trajectories.items()):
            norms = np.linalg.norm(traj, axis=1)
            norm_fig.add_trace(go.Scatter(
                y=norms, mode="lines+markers", name=name,
                line=dict(color=colors[i % len(colors)]),
            ))
        norm_fig.update_layout(
            title="Latent State Norm per Action",
            xaxis_title="Step", yaxis_title="||z||",
            height=400, template="plotly_dark",
        )

        # Heatmap of latent state for "play" action
        play_traj = trajectories.get("play", list(trajectories.values())[0])
        heat_fig = go.Figure(go.Heatmap(
            z=play_traj.T,
            colorscale="Viridis",
            colorbar_title="Value",
        ))
        heat_fig.update_layout(
            title="Latent State Heatmap (play action)",
            xaxis_title="Step", yaxis_title="Latent Dim",
            height=350, template="plotly_dark",
        )

        # Divergence: how different are the endpoints?
        endpoints = np.array([traj[-1] for traj in trajectories.values()])
        diff_matrix = np.zeros((len(ACTION_NAMES), len(ACTION_NAMES)))
        for i in range(len(ACTION_NAMES)):
            for j in range(len(ACTION_NAMES)):
                diff_matrix[i, j] = np.linalg.norm(endpoints[i] - endpoints[j])

        diff_fig = go.Figure(go.Heatmap(
            z=diff_matrix,
            x=ACTION_NAMES, y=ACTION_NAMES,
            colorscale="Reds",
            colorbar_title="L2 Distance",
        ))
        diff_fig.update_layout(
            title="Endpoint Divergence Between Actions",
            height=350, template="plotly_dark",
        )

        return html.Div([
            dcc.Graph(figure=norm_fig),
            dcc.Graph(figure=heat_fig),
            dcc.Graph(figure=diff_fig),
        ])
