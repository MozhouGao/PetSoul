"""
PetSoul Developer Dashboard — test each ML model individually.

Run:   python -m dash_app.app     (from project root)
Port:  8050
"""

import sys
from pathlib import Path

# Ensure pet_soul is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from dash_app.tabs import tab_detector, tab_attributes, tab_pipeline, tab_pose  # noqa: E402
from dash_app.tabs import tab_motion_features, tab_autoencoder  # noqa: E402
from dash_app.tabs import tab_audio_classifier, tab_audio_features  # noqa: E402
from dash_app.tabs import tab_fsm, tab_personality, tab_dynamics, tab_policy  # noqa: E402

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)
app.title = "PetSoul Dev Dashboard"

TABS = [
    ("Detector", tab_detector),
    ("Attributes", tab_attributes),
    ("Pipeline", tab_pipeline),
    ("Pose", tab_pose),
    ("Motion Stats", tab_motion_features),
    ("Autoencoder", tab_autoencoder),
    ("Audio Class.", tab_audio_classifier),
    ("Audio Features", tab_audio_features),
    ("FSM", tab_fsm),
    ("Personality", tab_personality),
    ("Dynamics", tab_dynamics),
    ("Policy", tab_policy),
]

app.layout = dbc.Container([
    html.H2("PetSoul Dev Dashboard", className="mt-3 mb-2",
            style={"fontFamily": "monospace", "color": "#7EC850"}),
    html.Hr(style={"borderColor": "#5B8731"}),
    dbc.Tabs(
        [
            dbc.Tab(
                module.layout(),
                label=name,
                tab_id=name.lower().replace(" ", "-").replace(".", ""),
            )
            for name, module in TABS
        ],
        id="main-tabs",
        active_tab="detector",
    ),
], fluid=True, className="pb-5")

# Register all callbacks
for _, module in TABS:
    module.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
