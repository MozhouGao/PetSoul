"""FSM tab — Interactive behavior state machine with sensory sliders."""

import json
import time
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


STATE_COLORS = {
    "IDLE": "#888888",
    "CURIOUS": "#55FFFF",
    "PLAYFUL": "#7EC850",
    "ALERT": "#FF5555",
    "RESTING": "#AA55FF",
}


def layout():
    return dbc.Card(dbc.CardBody([
        html.H4("Behavior FSM — Probabilistic State Machine"),
        html.P("Adjust sensory inputs and step the FSM to see state transitions.", className="text-muted"),

        dbc.Row([
            dbc.Col([
                dbc.Label("User Distance (0=touching, 10=far)"),
                dcc.Slider(id="fsm-dist", min=0, max=10, step=0.5, value=5,
                           marks={0: "0", 5: "5", 10: "10"}),
            ], width=6),
            dbc.Col([
                dbc.Label("Sound Level (0-1)"),
                dcc.Slider(id="fsm-sound", min=0, max=1, step=0.05, value=0.2,
                           marks={0: "0", 0.5: "0.5", 1: "1"}),
            ], width=6),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                dbc.Label("Time Since Interaction (seconds)"),
                dcc.Slider(id="fsm-time", min=0, max=60, step=1, value=3,
                           marks={0: "0", 30: "30", 60: "60"}),
            ], width=6),
            dbc.Col([
                dbc.Checklist(
                    id="fsm-moving",
                    options=[{"label": " User is moving", "value": "moving"}],
                    value=["moving"],
                    className="mt-4",
                ),
            ], width=3),
            dbc.Col([
                dbc.Button("Step", id="fsm-step", color="success", className="mt-4 me-2"),
                dbc.Button("Step x10", id="fsm-step10", color="warning", className="mt-4"),
            ], width=3),
        ], className="mb-3"),

        dcc.Store(id="fsm-store", data=json.dumps({
            "state": "IDLE",
            "history": ["IDLE"],
            "entered_at": time.time(),
        })),

        html.Div(id="fsm-output"),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("fsm-store", "data"),
        Output("fsm-output", "children"),
        Input("fsm-step", "n_clicks"),
        Input("fsm-step10", "n_clicks"),
        State("fsm-dist", "value"),
        State("fsm-sound", "value"),
        State("fsm-time", "value"),
        State("fsm-moving", "value"),
        State("fsm-store", "data"),
        prevent_initial_call=True,
    )
    def step_fsm(n1, n10, dist, sound, time_since, moving_vals, store_json):
        from dash import ctx
        from pet_soul.behavior.state_machine import PetFSM, PetState, SensoryInput

        store = json.loads(store_json)
        history = store.get("history", ["IDLE"])

        # Determine how many steps
        triggered = ctx.triggered_id
        steps = 10 if triggered == "fsm-step10" else 1

        # Create FSM and restore state
        fsm = PetFSM(initial_state=PetState[store.get("state", "IDLE")])

        user_moving = "moving" in (moving_vals or [])

        for _ in range(steps):
            sensory = SensoryInput(
                user_distance=float(dist or 5),
                user_moving=user_moving,
                sound_level=float(sound or 0.2),
                time_since_interaction=float(time_since or 3),
            )
            new_state = fsm.update(sensory)
            history.append(new_state.name)

        current = fsm.state.name

        # Keep last 100 entries
        history = history[-100:]

        new_store = json.dumps({
            "state": current,
            "history": history,
            "entered_at": time.time(),
        })

        # Current state display
        color = STATE_COLORS.get(current, "#888")
        state_display = html.Div([
            html.H2(current, style={
                "color": color, "textAlign": "center",
                "fontFamily": "monospace", "fontSize": "2.5em",
            }),
            html.P(f"History length: {len(history)} steps", className="text-muted text-center"),
        ])

        # History timeline
        colors = [STATE_COLORS.get(s, "#888") for s in history[-50:]]
        hist_fig = go.Figure(go.Bar(
            x=list(range(len(history[-50:]))),
            y=[1] * len(history[-50:]),
            marker_color=colors,
            text=history[-50:],
            hoverinfo="text",
        ))
        hist_fig.update_layout(
            title="State History (last 50 steps)",
            height=200, template="plotly_dark",
            yaxis=dict(visible=False),
            xaxis_title="Step",
        )

        # State distribution
        from collections import Counter
        counts = Counter(history)
        states = list(STATE_COLORS.keys())
        dist_fig = go.Figure(go.Bar(
            x=states,
            y=[counts.get(s, 0) for s in states],
            marker_color=[STATE_COLORS[s] for s in states],
        ))
        dist_fig.update_layout(
            title="State Distribution", height=250, template="plotly_dark",
        )

        return new_store, html.Div([
            state_display,
            dcc.Graph(figure=hist_fig),
            dcc.Graph(figure=dist_fig),
        ])
