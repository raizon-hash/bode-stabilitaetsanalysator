"""Streamlit-Oberfläche für den Bode- und Stabilitätsanalysator."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from calculations import (
    CsvValidationError,
    InputValidationError,
    MeasurementComparison,
    SystemAnalysis,
    analyze_system,
    compare_measurements,
    load_measurement_csv,
)


st.set_page_config(
    page_title="Bode- und Stabilitätsanalysator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1320px; padding-top: 1.8rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.25); border-radius: .65rem; padding: .8rem 1rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.2);}
    </style>
    """,
    unsafe_allow_html=True,
)


PRESETS = {
    "Stabiles Beispiel: 1 / (s(s + 1))": ("1", "1, 1, 0"),
    "PT2-Strecke: 4 / (s² + 2s + 4)": ("4", "1, 2, 4"),
    "Instabiler geschlossener Kreis": ("10", "1, 3, 2, 0"),
    "Eigene Koeffizienten": None,
}


def _initialise_state() -> None:
    st.session_state.setdefault("preset", "Stabiles Beispiel: 1 / (s(s + 1))")
    st.session_state.setdefault("numerator", "1")
    st.session_state.setdefault("denominator", "1, 1, 0")


def _apply_preset() -> None:
    values = PRESETS[st.session_state.preset]
    if values is not None:
        st.session_state.numerator, st.session_state.denominator = values


def _format_value(value: float, unit: str = "", digits: int = 3) -> str:
    if np.isnan(value):
        return "nicht vorhanden"
    if np.isposinf(value):
        return "∞"
    if np.isneginf(value):
        return "−∞"
    suffix = f" {unit}" if unit else ""
    return f"{value:.{digits}g}{suffix}"


def _format_coefficient(value: float) -> str:
    if np.isclose(value, round(value), atol=1e-12):
        return str(int(round(value)))
    return f"{value:.5g}"


def _polynomial_latex(coefficients: np.ndarray) -> str:
    degree = len(coefficients) - 1
    terms: list[str] = []
    for index, coefficient in enumerate(coefficients):
        if np.isclose(coefficient, 0.0, atol=1e-14):
            continue
        power = degree - index
        absolute = abs(float(coefficient))
        if power == 0:
            body = _format_coefficient(absolute)
        else:
            coefficient_text = "" if np.isclose(absolute, 1.0) else _format_coefficient(absolute)
            variable = "s" if power == 1 else f"s^{{{power}}}"
            body = f"{coefficient_text}{variable}"

        if not terms:
            terms.append(f"-{body}" if coefficient < 0 else body)
        else:
            terms.append((" - " if coefficient < 0 else " + ") + body)
    return "".join(terms) if terms else "0"


def _system_latex(system: object) -> str:
    numerator = np.asarray(system.num[0][0], dtype=float)
    denominator = np.asarray(system.den[0][0], dtype=float)
    return rf"\frac{{{_polynomial_latex(numerator)}}}{{{_polynomial_latex(denominator)}}}"


def _frequency_display(omega_rad_s: float, unit: str) -> float:
    return omega_rad_s if unit == "rad/s" else omega_rad_s / (2.0 * np.pi)


def _frequency_label(unit: str) -> str:
    return "Kreisfrequenz ω [rad/s]" if unit == "rad/s" else "Frequenz f [Hz]"


def _frequency_unit_symbol(unit: str) -> str:
    return "rad/s" if unit == "rad/s" else "Hz"


def _create_bode_figure(
    analysis: SystemAnalysis,
    comparison: MeasurementComparison | None,
    unit: str,
    show_margins: bool,
) -> go.Figure:
    x_theory = np.array(
        [_frequency_display(value, unit) for value in analysis.response.omega_rad_s]
    )
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.52, 0.48],
    )
    figure.add_trace(
        go.Scatter(
            x=x_theory,
            y=analysis.response.magnitude_db,
            mode="lines",
            name="Theorie",
            line={"color": "#2f80ed", "width": 2.6},
            hovertemplate="%{x:.4g}<br>%{y:.3f} dB<extra>Theorie</extra>",
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=x_theory,
            y=analysis.response.phase_deg,
            mode="lines",
            name="Theorie Phase",
            showlegend=False,
            line={"color": "#2f80ed", "width": 2.6},
            hovertemplate="%{x:.4g}<br>%{y:.2f}°<extra>Theorie</extra>",
        ),
        row=2,
        col=1,
    )

    if comparison is not None:
        data = comparison.data
        frequency_column = "omega_rad_s" if unit == "rad/s" else "frequency_hz"
        figure.add_trace(
            go.Scatter(
                x=data[frequency_column],
                y=data["magnitude_db"],
                mode="markers",
                name="Messung",
                marker={"color": "#f2994a", "size": 9, "symbol": "diamond"},
                hovertemplate="%{x:.4g}<br>%{y:.3f} dB<extra>Messung</extra>",
            ),
            row=1,
            col=1,
        )
        figure.add_trace(
            go.Scatter(
                x=data[frequency_column],
                y=data["phase_deg_aligned"],
                mode="markers",
                name="Messung Phase",
                showlegend=False,
                marker={"color": "#f2994a", "size": 9, "symbol": "diamond"},
                hovertemplate="%{x:.4g}<br>%{y:.2f}°<extra>Messung</extra>",
            ),
            row=2,
            col=1,
        )

    figure.add_hline(y=0.0, line_dash="dash", line_color="#7f8c8d", row=1, col=1)
    figure.add_hline(y=-180.0, line_dash="dash", line_color="#7f8c8d", row=2, col=1)

    if show_margins:
        margins = analysis.margins
        for omega, colour, label in (
            (margins.gain_crossover_rad_s, "#27ae60", "ωD"),
            (margins.phase_crossover_rad_s, "#eb5757", "ωπ"),
        ):
            if np.isfinite(omega) and omega > 0:
                x_value = _frequency_display(omega, unit)
                if x_theory.min() <= x_value <= x_theory.max():
                    figure.add_vline(
                        x=x_value,
                        line_dash="dot",
                        line_width=1.7,
                        line_color=colour,
                        annotation_text=label,
                        annotation_position="top",
                    )

    figure.update_xaxes(type="log", showgrid=True, minor={"showgrid": True}, row=1, col=1)
    figure.update_xaxes(
        type="log",
        title_text=_frequency_label(unit),
        showgrid=True,
        minor={"showgrid": True},
        row=2,
        col=1,
    )
    figure.update_yaxes(title_text="Betrag [dB]", row=1, col=1)
    figure.update_yaxes(title_text="Phase [°]", row=2, col=1)
    figure.update_layout(
        height=720,
        margin={"l": 40, "r": 25, "t": 25, "b": 30},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    return figure


def _pole_zero_table(analysis: SystemAnalysis) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    groups = (
        ("Offener Kreis", "Pol", analysis.open_loop_poles),
        ("Offener Kreis", "Nullstelle", analysis.open_loop_zeros),
        ("Geschlossener Kreis", "Pol", analysis.closed_loop_poles),
        ("Geschlossener Kreis", "Nullstelle", analysis.closed_loop_zeros),
    )
    for system_name, point_type, values in groups:
        for value in values:
            rows.append(
                {
                    "System": system_name,
                    "Typ": point_type,
                    "Realteil": value.real,
                    "Imaginärteil": value.imag,
                    "Betrag": abs(value),
                }
            )
    return pd.DataFrame(rows)


def _create_pole_zero_figure(analysis: SystemAnalysis) -> go.Figure:
    figure = go.Figure()
    traces = (
        (analysis.open_loop_poles, "Offene Pole", "x", "#2f80ed", 12),
        (analysis.open_loop_zeros, "Offene Nullstellen", "circle-open", "#2f80ed", 12),
        (analysis.closed_loop_poles, "Geschlossene Pole", "diamond", "#eb5757", 10),
    )
    for values, name, symbol, colour, size in traces:
        if len(values):
            figure.add_trace(
                go.Scatter(
                    x=np.real(values),
                    y=np.imag(values),
                    mode="markers",
                    name=name,
                    marker={"symbol": symbol, "color": colour, "size": size, "line_width": 2},
                    hovertemplate="Re = %{x:.4g}<br>Im = %{y:.4g}<extra>%{fullData.name}</extra>",
                )
            )
    figure.add_vline(x=0.0, line_color="#7f8c8d", line_width=1.4)
    figure.add_hline(y=0.0, line_color="#7f8c8d", line_width=1.0)
    figure.update_layout(
        height=520,
        xaxis_title="Realteil",
        yaxis_title="Imaginärteil",
        yaxis={"scaleanchor": "x", "scaleratio": 1},
        margin={"l": 35, "r": 25, "t": 25, "b": 35},
        legend={"orientation": "h", "y": 1.08},
    )
    return figure


def _create_error_figure(comparison: MeasurementComparison, unit: str) -> go.Figure:
    data = comparison.data
    frequency_column = "omega_rad_s" if unit == "rad/s" else "frequency_hz"
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    figure.add_trace(
        go.Scatter(
            x=data[frequency_column],
            y=data["magnitude_error_db"],
            mode="lines+markers",
            name="Betragsabweichung",
            line={"color": "#9b51e0"},
        ),
        row=1,
        col=1,
    )
    figure.add_trace(
        go.Scatter(
            x=data[frequency_column],
            y=data["phase_error_deg"],
            mode="lines+markers",
            name="Phasenabweichung",
            line={"color": "#f2994a"},
        ),
        row=2,
        col=1,
    )
    figure.add_hline(y=0, line_dash="dash", line_color="#7f8c8d", row=1, col=1)
    figure.add_hline(y=0, line_dash="dash", line_color="#7f8c8d", row=2, col=1)
    figure.update_xaxes(type="log", row=1, col=1)
    figure.update_xaxes(type="log", title_text=_frequency_label(unit), row=2, col=1)
    figure.update_yaxes(title_text="Δ Betrag [dB]", row=1, col=1)
    figure.update_yaxes(title_text="Δ Phase [°]", row=2, col=1)
    figure.update_layout(
        height=520,
        margin={"l": 35, "r": 25, "t": 25, "b": 35},
        showlegend=False,
    )
    return figure


_initialise_state()

with st.sidebar:
    st.header("Systemdefinition")
    st.selectbox(
        "Beispielsystem",
        PRESETS,
        key="preset",
        on_change=_apply_preset,
    )
    st.text_input(
        "Zählerkoeffizienten",
        key="numerator",
        help="Absteigende Potenzfolge, z. B. 1, 3 für s + 3.",
    )
    st.text_input(
        "Nennerkoeffizienten",
        key="denominator",
        help="Absteigende Potenzfolge, z. B. 1, 1, 0 für s² + s.",
    )
    st.caption(
        "Komma, Semikolon oder Leerzeichen trennen Koeffizienten. "
        "Bei Dezimalkommas bitte Semikolon verwenden: `0,5; 1; 0`."
    )

    st.divider()
    st.header("Frequenzbereich")
    frequency_unit = st.selectbox("Anzeigeeinheit", ("rad/s", "Hz"))
    col_min, col_max = st.columns(2)
    with col_min:
        minimum_frequency = st.number_input(
            f"Minimum [{frequency_unit}]",
            min_value=1e-6,
            max_value=1e9,
            value=0.01,
            format="%.6g",
        )
    with col_max:
        maximum_frequency = st.number_input(
            f"Maximum [{frequency_unit}]",
            min_value=1e-6,
            max_value=1e9,
            value=100.0,
            format="%.6g",
        )
    sample_count = st.slider("Berechnungspunkte", 200, 2000, 800, 100)
    show_margins = st.checkbox("Grenzfrequenzen markieren", value=True)

    st.divider()
    st.header("Messdaten")
    uploaded_file = st.file_uploader(
        "CSV-Datei hochladen",
        type=("csv", "txt"),
        help="Benötigt Frequenz, Betrag in dB und Phase in Grad.",
    )

st.title("Bode- und Stabilitätsanalysator")
st.caption(
    "Analyse einer offenen Kreisübertragungsfunktion und des geschlossenen Kreises "
    "bei negativer Einheitsrückführung"
)

if maximum_frequency <= minimum_frequency:
    st.error("Das Frequenzmaximum muss größer als das Frequenzminimum sein.")
    st.stop()

omega_min = minimum_frequency if frequency_unit == "rad/s" else 2.0 * np.pi * minimum_frequency
omega_max = maximum_frequency if frequency_unit == "rad/s" else 2.0 * np.pi * maximum_frequency
omega = np.logspace(math.log10(omega_min), math.log10(omega_max), sample_count)

try:
    analysis = analyze_system(st.session_state.numerator, st.session_state.denominator, omega)
except InputValidationError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:  # Oberfläche darf bei numerischen Sonderfällen nicht abstürzen.
    st.error(f"Das System konnte numerisch nicht analysiert werden: {exc}")
    st.stop()

measurements = None
comparison = None
csv_error = None
if uploaded_file is not None:
    try:
        measurements = load_measurement_csv(uploaded_file.getvalue())
        comparison = compare_measurements(analysis.open_loop, measurements)
    except CsvValidationError as exc:
        csv_error = str(exc)
    except Exception as exc:
        csv_error = f"Die Messdaten konnten nicht verarbeitet werden: {exc}"

formula_column, explanation_column = st.columns([1.4, 1])
with formula_column:
    st.subheader("Übertragungsfunktionen")
    st.latex(rf"G_0(s) = {_system_latex(analysis.open_loop)}")
    st.latex(rf"G_w(s) = \frac{{G_0(s)}}{{1 + G_0(s)}} = {_system_latex(analysis.closed_loop)}")
with explanation_column:
    if analysis.closed_loop_stability == "asymptotisch stabil":
        st.success("Der geschlossene Kreis ist asymptotisch stabil.", icon="✅")
    elif analysis.closed_loop_stability.startswith("grenzstabil"):
        st.warning(f"Der geschlossene Kreis ist {analysis.closed_loop_stability}.", icon="⚠️")
    else:
        st.error(f"Der geschlossene Kreis ist {analysis.closed_loop_stability}.", icon="⛔")
    if np.any(analysis.open_loop_poles.real > 1e-8):
        st.warning(
            "Der offene Kreis besitzt Pole in der rechten Halbebene. Klassische "
            "Bode-Reserven allein sind dann kein hinreichender Stabilitätsnachweis."
        )

margin_columns = st.columns(4)
margin_columns[0].metric(
    "Durchtrittsfrequenz ωD",
    _format_value(
        _frequency_display(analysis.margins.gain_crossover_rad_s, frequency_unit),
        _frequency_unit_symbol(frequency_unit),
    ),
)
margin_columns[1].metric(
    "Phasenreserve φR",
    _format_value(analysis.margins.phase_margin_deg, "°"),
)
margin_columns[2].metric(
    "Amplitudenreserve AR",
    _format_value(analysis.margins.gain_margin_db, "dB"),
)
margin_columns[3].metric(
    "Stabilitätsreserve sm",
    _format_value(analysis.margins.stability_margin),
)

tab_bode, tab_poles, tab_measurements, tab_help = st.tabs(
    ("Bode-Diagramm", "Pole und Stabilität", "Messdatenvergleich", "Hinweise")
)

with tab_bode:
    st.plotly_chart(
        _create_bode_figure(analysis, comparison, frequency_unit, show_margins),
        width="stretch",
        config={"displaylogo": False, "scrollZoom": True},
    )
    if comparison is not None:
        st.info(
            "Die Messpunkte wurden bei ihren Originalfrequenzen mit dem Modell verglichen. "
            "Phasenwerte werden für die Darstellung um ganzzahlige Vielfache von 360° ausgerichtet."
        )

with tab_poles:
    plot_column, table_column = st.columns([1.35, 1])
    with plot_column:
        st.plotly_chart(
            _create_pole_zero_figure(analysis),
            width="stretch",
            config={"displaylogo": False},
        )
    with table_column:
        st.subheader("Stabilitätsbewertung")
        st.write(f"**Offener Kreis:** {analysis.open_loop_stability}")
        st.write(f"**Geschlossener Kreis:** {analysis.closed_loop_stability}")
        st.caption(
            "Asymptotische Stabilität liegt nur vor, wenn sämtliche Pole einen "
            "streng negativen Realteil besitzen."
        )
        st.subheader("Pol- und Nullstellenwerte")
        pole_table = _pole_zero_table(analysis)
        if pole_table.empty:
            st.info("Das System besitzt keine endlichen Pole oder Nullstellen.")
        else:
            st.dataframe(
                pole_table.style.format(
                    {"Realteil": "{:.5g}", "Imaginärteil": "{:.5g}", "Betrag": "{:.5g}"}
                ),
                width="stretch",
                hide_index=True,
            )

with tab_measurements:
    template_csv = (
        "omega_rad_s;magnitude_db;phase_deg\n"
        "0,1;20,137;-95,111\n"
        "0,2;13,689;-102,110\n"
        "0,5;5,141;-116,165\n"
        "0,8;-0,360;-129,360\n"
        "1;-2,900;-134,500\n"
        "2;-13,090;-153,835\n"
        "5;-27,959;-167,790\n"
        "10;-40,143;-174,889\n"
    )
    st.download_button(
        "Beispiel-CSV herunterladen",
        data=template_csv.encode("utf-8"),
        file_name="messdaten_beispiel.csv",
        mime="text/csv",
    )

    if csv_error:
        st.error(csv_error)
    elif comparison is None:
        st.info(
            "Lade links eine CSV-Datei hoch. Benötigt werden `omega_rad_s` oder "
            "`frequency_hz` sowie `magnitude_db` und `phase_deg`."
        )
    else:
        error_columns = st.columns(4)
        error_columns[0].metric("Mittlere |Δ Betrag|", f"{comparison.magnitude_mae_db:.3f} dB")
        error_columns[1].metric(
            "Maximale |Δ Betrag|", f"{comparison.magnitude_max_error_db:.3f} dB"
        )
        error_columns[2].metric("Mittlere |Δ Phase|", f"{comparison.phase_mae_deg:.3f}°")
        error_columns[3].metric(
            "Maximale |Δ Phase|", f"{comparison.phase_max_error_deg:.3f}°"
        )
        st.plotly_chart(
            _create_error_figure(comparison, frequency_unit),
            width="stretch",
            config={"displaylogo": False},
        )

        display_data = comparison.data.drop(columns=["phase_deg_aligned"]).rename(
            columns={
                "omega_rad_s": "ω [rad/s]",
                "frequency_hz": "f [Hz]",
                "magnitude_db": "Messung Betrag [dB]",
                "phase_deg": "Messung Phase [°]",
                "theoretical_magnitude_db": "Theorie Betrag [dB]",
                "magnitude_error_db": "Δ Betrag [dB]",
                "theoretical_phase_deg": "Theorie Phase [°]",
                "phase_error_deg": "Δ Phase [°]",
            }
        )
        st.dataframe(
            display_data.style.format("{:.5g}"),
            width="stretch",
            hide_index=True,
        )

with tab_help:
    st.subheader("Interpretation der Kennwerte")
    st.markdown(
        """
        - **Durchtrittsfrequenz ωD:** Frequenz, bei der der Betrag des offenen Kreises 0 dB beträgt.
        - **Phasenreserve φR:** Abstand der Phase bei ωD zur kritischen Phase −180°.
        - **Amplitudenreserve AR:** Zulässige Verstärkungsänderung bis zum Stabilitätsrand, in dB.
        - **Stabilitätsreserve sm:** Minimaler Abstand des Nyquist-Orts zur kritischen Stelle −1.
        - **Geschlossene Pole:** Entscheidend für die tatsächliche Stabilität des rückgekoppelten Systems.
        """
    )
    st.warning(
        "Ein nicht vorhandener Kreuzungspunkt wird als ‚nicht vorhanden‘ oder mit einer "
        "unendlichen Reserve angezeigt. Das ist kein Rechenfehler."
    )
    with st.expander("Unterstütztes CSV-Format"):
        st.code(
            "omega_rad_s;magnitude_db;phase_deg\n"
            "0,1;20,137;-95,111\n"
            "0,2;13,689;-102,110",
            language="text",
        )
        st.caption(
            "Alternativ darf die Frequenzspalte `frequency_hz` heißen. "
            "Komma-, Semikolon- und Tabulator-Trennung werden erkannt."
        )

st.divider()
st.caption(
    "LF 10.2 · Technische Web-Applikation mit Python · Berechnungen mit NumPy, "
    "Pandas und Python Control Systems Library"
)
