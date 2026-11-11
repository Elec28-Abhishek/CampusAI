from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT_DIR = Path(__file__).resolve().parents[1] / "components" / "google_map"
_google_map = components.declare_component("campusai_vssut_google_map", path=str(_COMPONENT_DIR))


def google_map(**properties):
    return _google_map(default=None, **properties)
