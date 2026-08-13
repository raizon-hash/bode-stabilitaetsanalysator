"""Integrationstests der Streamlit-Oberfläche."""

import os
from pathlib import Path
import tempfile

from streamlit.testing.v1 import AppTest


os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib-bode-app"))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "streamlit_app.py"


def _start_app() -> AppTest:
    return AppTest.from_file(str(APP_PATH), default_timeout=30).run()


def test_app_starts_with_known_reference_system() -> None:
    app = _start_app()

    assert not app.exception
    assert [title.value for title in app.title] == ["Bode- und Stabilitätsanalysator"]
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Durchtrittsfrequenz ωD"] == "0.786 rad/s"
    assert metrics["Phasenreserve φR"] == "51.8 °"


def test_unstable_preset_is_reported_without_app_crash() -> None:
    app = _start_app()
    app.selectbox[0].select("Instabiler geschlossener Kreis").run()

    assert not app.exception
    assert any("geschlossene Kreis ist instabil" in error.value for error in app.error)


def test_example_csv_is_processed_in_the_interface() -> None:
    app = _start_app()
    csv_content = (PROJECT_ROOT / "examples" / "messdaten_beispiel.csv").read_bytes()
    app.get("file_uploader")[0].upload(
        "messdaten_beispiel.csv", csv_content, "text/csv"
    ).run()

    assert not app.exception
    assert not app.error
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Mittlere |Δ Betrag|"] == "0.125 dB"
    assert metrics["Maximale |Δ Phase|"] == "0.900°"
