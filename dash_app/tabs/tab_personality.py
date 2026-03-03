"""Personality tab — From motion stats, compute and display personality radar chart."""

from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


TRAIT_NAMES = [
    "energy_level", "playfulness", "reactivity",
    "tail_expressiveness", "gait_regularity",
    "vocal_energy", "vocal_frequency",
    "sociability", "calmness",
]


def layout():
    sliders = []
    stats = [
        ("avg_speed", 0, 2, 0.5),
        ("max_speed", 0, 5, 1.5),
        ("movement_entropy", 0, 3, 1.0),
        ("tail_wag_freq", 0, 10, 2.0),
        ("head_motion_range", 0, 2, 0.5),
        ("gait_regularity", 0, 1, 0.5),
    ]

    for name, mn, mx, default in stats:
        sliders.append(dbc.Row([
            dbc.Col(dbc.Label(name), width=4),
            dbc.Col(dcc.Slider(
                id=f"pers-{name}", min=mn, max=mx,
                step=(mx - mn) / 20, value=default,
                marks={mn: str(mn), mx: str(mx)},
            ), width=8),
        ], className="mb-2"))

    return dbc.Card(dbc.CardBody([
        html.H4("Personality Profile"),
        html.P("Adjust motion statistics to derive personality traits.", className="text-muted"),
        *sliders,
        dbc.Button("Compute Personality", id="pers-run", color="success", className="mt-2 mb-3"),
        html.Div(id="pers-output"),
    ]))


def register_callbacks(app):
    @app.callback(
        Output("pers-output", "children"),
        Input("pers-run", "n_clicks"),
        [
            Input(f"pers-{name}", "value")
            for name in ["avg_speed", "max_speed", "movement_entropy",
                         "tail_wag_freq", "head_motion_range", "gait_regularity"]
        ],
        prevent_initial_call=True,
    )
    def compute_personality(n_clicks, avg_speed, max_speed, entropy, tail, head, gait):
        if not n_clicks:
            return ""

        from pet_soul.behavior.personality import profile_from_motion_stats

        stats = {
            "avg_speed": float(avg_speed or 0),
            "max_speed": float(max_speed or 0),
            "movement_entropy": float(entropy or 0),
            "tail_wag_freq": float(tail or 0),
            "head_motion_range": float(head or 0),
            "gait_regularity": float(gait or 0),
        }

        profile = profile_from_motion_stats(stats)
        d = profile.to_dict()

        # Radar chart
        values = [d.get(t, 0.5) for t in TRAIT_NAMES]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=TRAIT_NAMES + [TRAIT_NAMES[0]],
            fill="toself",
            fillcolor="rgba(170, 85, 255, 0.3)",
            line_color="#AA55FF",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Personality Profile (9 traits)",
            height=450, template="plotly_dark",
        )

        # Traits table
        rows = [html.Tr([html.Td(k), html.Td(f"{v:.3f}")]) for k, v in d.items()]
        table = dbc.Table(
            [html.Thead(html.Tr([html.Th("Trait"), html.Th("Value")])),
             html.Tbody(rows)],
            bordered=True, dark=True, striped=True, size="sm",
        )

        return html.Div([dcc.Graph(figure=fig), table])
