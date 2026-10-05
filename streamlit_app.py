"""Streamlit report viewer for iRacing telemetry.

Run with:  poetry run streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Make the src-layout package importable when running from a bare checkout
# (e.g. Streamlit Community Cloud), without needing an editable install.
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st  # noqa: E402

from iracing_telemetry import (  # noqa: E402
    SessionMetadata,
    build_figures,
    build_report,
    get_valid_laps,
    load_filtered_frame,
    read_session_metadata,
)

IBT_INPUT_DIR = Path(__file__).parent / "ibt_input"
SAMPLE_DIR = Path(__file__).parent / "examples" / "samples"

st.set_page_config(page_title="iRacing Telemetry", page_icon="🏁", layout="wide")


def _list_sample_files() -> list[Path]:
    files = list(IBT_INPUT_DIR.glob("*.ibt"))
    if SAMPLE_DIR.is_dir():
        files += list(SAMPLE_DIR.glob("*.ibt"))
    return sorted(files)


@st.cache_data(show_spinner="Reading telemetry…")
def _load(path_str: str):
    """Load the filtered frame and metadata for a file path (cached by path+mtime)."""
    path = Path(path_str)
    df = load_filtered_frame(path)
    metadata = read_session_metadata(path)
    return df, metadata


def _resolve_input() -> Path | None:
    """Sidebar controls to pick an uploaded file or one from ibt_input/."""
    st.sidebar.header("Session")
    source = st.sidebar.radio("Load from", ["Sample files", "Upload"], horizontal=True)

    if source == "Upload":
        uploaded = st.sidebar.file_uploader("Choose a .ibt file", type="ibt")
        if uploaded is None:
            return None
        tmp = tempfile.NamedTemporaryFile(suffix=".ibt", delete=False)
        tmp.write(uploaded.getvalue())
        tmp.close()
        return Path(tmp.name)

    samples = _list_sample_files()
    if not samples:
        st.sidebar.info("No .ibt files in ibt_input/. Switch to Upload.")
        return None
    choice = st.sidebar.selectbox("File", samples, format_func=lambda p: p.name)
    return choice


def _render_header(metadata: SessionMetadata) -> None:
    st.title(metadata.track_label)
    bits = [b for b in (metadata.location, metadata.car, metadata.driver) if b]
    if bits:
        st.caption(" · ".join(bits))
    if metadata.num_turns:
        st.caption(f"{metadata.num_turns} turns")


def main() -> None:
    input_path = _resolve_input()
    if input_path is None:
        st.title("iRacing Telemetry Analysis")
        st.write("Pick a sample session or upload a `.ibt` file from the sidebar to begin.")
        return

    units = st.sidebar.radio("Units", ["mph", "kph"], horizontal=True)

    df, metadata = _load(str(input_path))
    valid_laps = get_valid_laps(df)

    if not valid_laps:
        st.warning("No complete laps found in this session.")
        return

    selected = st.sidebar.multiselect(
        "Laps", valid_laps, default=valid_laps, format_func=lambda lap: f"Lap {lap}"
    )
    if not selected:
        st.info("Select at least one lap from the sidebar.")
        return

    _render_header(metadata)

    charts_tab, report_tab = st.tabs(["Charts", "Report"])

    with charts_tab:
        figures = build_figures(df, selected, units=units)
        for name, figure in figures.items():
            st.subheader(name)
            if isinstance(figure, list):
                for fig in figure:
                    st.plotly_chart(fig, width="stretch")
            else:
                st.plotly_chart(figure, width="stretch")

    with report_tab:
        st.markdown(build_report(df, input_path.stem, units=units, metadata=metadata))


if __name__ == "__main__":
    main()
