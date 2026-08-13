import numpy as np
import pandas as pd
import pytest

from calculations import (
    CsvValidationError,
    InputValidationError,
    analyze_system,
    compare_measurements,
    load_measurement_csv,
    parse_coefficients,
    validate_transfer_function,
)


def test_parse_coefficients_accepts_common_separators() -> None:
    np.testing.assert_allclose(parse_coefficients("1, 3, 2", "Test"), [1, 3, 2])
    np.testing.assert_allclose(parse_coefficients("0,5; 1; 0", "Test"), [0.5, 1, 0])
    np.testing.assert_allclose(parse_coefficients("1  0.25  4", "Test"), [1, 0.25, 4])


@pytest.mark.parametrize("value", ["", "0, 0", "1, x, 2", "nan, 1"])
def test_parse_coefficients_rejects_invalid_input(value: str) -> None:
    with pytest.raises(InputValidationError):
        parse_coefficients(value, "Test")


def test_improper_transfer_function_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="unecht"):
        validate_transfer_function("1, 0, 1", "1, 1")


def test_known_system_has_expected_margins_and_stable_closed_loop() -> None:
    # G0(s) = 1 / (s(s+1)); analytisch folgt ωD ≈ 0,7862 rad/s und φR ≈ 51,83°.
    omega = np.logspace(-3, 3, 1000)
    result = analyze_system([1], [1, 1, 0], omega)

    assert result.closed_loop_stability == "asymptotisch stabil"
    assert result.margins.gain_crossover_rad_s == pytest.approx(0.786151, rel=2e-4)
    assert result.margins.phase_margin_deg == pytest.approx(51.8273, rel=2e-4)
    assert np.isinf(result.margins.gain_margin_factor)
    np.testing.assert_allclose(
        np.sort_complex(result.closed_loop_poles),
        np.sort_complex(np.array([-0.5 - 0.8660254j, -0.5 + 0.8660254j])),
        rtol=1e-6,
    )


def test_unstable_closed_loop_is_detected() -> None:
    # G0(s) = 10 / (s(s+1)(s+2)); zwei geschlossene Pole liegen rechts.
    result = analyze_system([10], [1, 3, 2, 0], np.logspace(-3, 3, 800))
    assert result.closed_loop_stability == "instabil"
    assert np.any(result.closed_loop_poles.real > 0)


def test_german_excel_csv_is_loaded() -> None:
    content = (
        "omega_rad_s;magnitude_db;phase_deg\n"
        "0,1;20,137;-95,111\n"
        "1,0;-3,010;-135,0\n"
    ).encode("utf-8")
    data = load_measurement_csv(content)

    assert list(data.columns) == ["omega_rad_s", "frequency_hz", "magnitude_db", "phase_deg"]
    np.testing.assert_allclose(data["omega_rad_s"], [0.1, 1.0])
    np.testing.assert_allclose(data["magnitude_db"], [20.137, -3.010])


def test_frequency_in_hz_is_converted_to_angular_frequency() -> None:
    content = (
        "frequency_hz,magnitude_db,phase_deg\n"
        "1,0,-90\n"
        "10,-20,-135\n"
    ).encode("utf-8")
    data = load_measurement_csv(content)
    np.testing.assert_allclose(data["omega_rad_s"], 2 * np.pi * np.array([1.0, 10.0]))


@pytest.mark.parametrize(
    "content, message",
    [
        (b"omega_rad_s;magnitude_db\n1;0\n2;-3\n", "phase_deg"),
        (b"omega_rad_s;magnitude_db;phase_deg\n0;1;-90\n1;0;-100\n", "größer als null"),
        (b"omega_rad_s;magnitude_db;phase_deg\n1;x;-90\n2;0;-100\n", "Ungültige"),
    ],
)
def test_invalid_csv_is_rejected(content: bytes, message: str) -> None:
    with pytest.raises(CsvValidationError, match=message):
        load_measurement_csv(content)


def test_invalid_german_csv_reports_only_the_actual_row_with_pandas_string_dtype() -> None:
    content = (
        "omega_rad_s;magnitude_db;phase_deg\n"
        "0,1;kein_wert;-95,111\n"
        "1;-2,900;-134,500\n"
    ).encode("utf-8")

    with pytest.raises(CsvValidationError) as error:
        load_measurement_csv(content)

    assert str(error.value) == "Ungültige oder fehlende Zahlenwerte in CSV-Zeile 2."


def test_exact_measurements_have_zero_error_even_with_wrapped_phase() -> None:
    omega = np.array([0.2, 1.0, 5.0])
    analysis = analyze_system([1], [1, 1, 0], omega)
    # Der letzte Messwert ist um 360° äquivalent dargestellt.
    phase = analysis.response.phase_deg.copy()
    phase[-1] += 360.0
    measurements = pd.DataFrame(
        {
            "omega_rad_s": omega,
            "frequency_hz": omega / (2 * np.pi),
            "magnitude_db": analysis.response.magnitude_db,
            "phase_deg": phase,
        }
    )

    comparison = compare_measurements(analysis.open_loop, measurements)
    assert comparison.magnitude_mae_db == pytest.approx(0.0, abs=1e-12)
    assert comparison.phase_mae_deg == pytest.approx(0.0, abs=1e-12)
