"""Mathematischer Kern des Bode- und Stabilitätsanalysators.

Alle fachlichen Berechnungen sind von der Streamlit-Oberfläche getrennt. Das
macht die Funktionen automatisiert testbar und erleichtert die spätere
Fehlersuche.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
import re
import unicodedata
from typing import BinaryIO, Iterable

import control as ct
import numpy as np
import pandas as pd


class InputValidationError(ValueError):
    """Fehler bei der Eingabe einer Übertragungsfunktion."""


class CsvValidationError(ValueError):
    """Fehler beim Einlesen oder Validieren einer Messdaten-CSV."""


@dataclass(frozen=True)
class FrequencyResponse:
    """Frequenzantwort eines SISO-Systems."""

    omega_rad_s: np.ndarray
    magnitude: np.ndarray
    magnitude_db: np.ndarray
    phase_deg: np.ndarray


@dataclass(frozen=True)
class StabilityMargins:
    """Klassische Stabilitätsreserven der offenen Kreisübertragungsfunktion."""

    gain_margin_factor: float
    gain_margin_db: float
    phase_margin_deg: float
    stability_margin: float
    phase_crossover_rad_s: float
    gain_crossover_rad_s: float
    stability_margin_rad_s: float


@dataclass(frozen=True)
class SystemAnalysis:
    """Gesamtergebnis der regelungstechnischen Systemanalyse."""

    numerator: np.ndarray
    denominator: np.ndarray
    open_loop: ct.TransferFunction
    closed_loop: ct.TransferFunction
    open_loop_poles: np.ndarray
    open_loop_zeros: np.ndarray
    closed_loop_poles: np.ndarray
    closed_loop_zeros: np.ndarray
    open_loop_stability: str
    closed_loop_stability: str
    margins: StabilityMargins
    response: FrequencyResponse


@dataclass(frozen=True)
class MeasurementComparison:
    """Punktweiser Vergleich zwischen Messung und theoretischem Modell."""

    data: pd.DataFrame
    magnitude_mae_db: float
    magnitude_max_error_db: float
    phase_mae_deg: float
    phase_max_error_deg: float


def _trim_leading_zeros(coefficients: np.ndarray) -> np.ndarray:
    nonzero = np.flatnonzero(np.abs(coefficients) > 1e-15)
    if nonzero.size == 0:
        return np.array([], dtype=float)
    return coefficients[nonzero[0] :]


def parse_coefficients(
    raw: str | Iterable[float],
    name: str,
    *,
    max_order: int = 10,
) -> np.ndarray:
    """Liest reelle Polynomkoeffizienten in absteigender Potenzfolge ein.

    Kommas, Semikolons und Leerzeichen werden als Trennzeichen akzeptiert.
    Enthält die Eingabe Semikolons, werden Kommas innerhalb eines Werts als
    deutsche Dezimaltrennzeichen interpretiert.
    """

    if isinstance(raw, str):
        cleaned = raw.strip().strip("[]()")
        if not cleaned:
            raise InputValidationError(f"{name}: Es wurden keine Koeffizienten eingegeben.")

        if ";" in cleaned:
            tokens = [token.strip().replace(",", ".") for token in cleaned.split(";")]
        else:
            tokens = re.split(r"[,\s]+", cleaned)
        tokens = [token for token in tokens if token]
    else:
        try:
            tokens = list(raw)
        except TypeError as exc:
            raise InputValidationError(
                f"{name}: Die Koeffizienten konnten nicht gelesen werden."
            ) from exc

    try:
        coefficients = np.asarray([float(value) for value in tokens], dtype=float)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(
            f"{name}: Nur reelle Zahlen und gültige Trennzeichen sind erlaubt."
        ) from exc

    if coefficients.ndim != 1 or coefficients.size == 0:
        raise InputValidationError(f"{name}: Es wurden keine Koeffizienten erkannt.")
    if not np.all(np.isfinite(coefficients)):
        raise InputValidationError(f"{name}: NaN und unendliche Werte sind nicht erlaubt.")

    coefficients = _trim_leading_zeros(coefficients)
    if coefficients.size == 0:
        raise InputValidationError(f"{name}: Das Polynom darf nicht vollständig null sein.")
    if coefficients.size - 1 > max_order:
        raise InputValidationError(
            f"{name}: Maximal wird die Ordnung {max_order} unterstützt."
        )

    return coefficients


def validate_transfer_function(
    numerator: str | Iterable[float],
    denominator: str | Iterable[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Validiert und normalisiert Zähler und Nenner einer Übertragungsfunktion."""

    num = parse_coefficients(numerator, "Zähler")
    den = parse_coefficients(denominator, "Nenner")

    if num.size > den.size:
        raise InputValidationError(
            "Die Übertragungsfunktion ist unecht: Der Zählergrad darf nicht "
            "größer als der Nennergrad sein."
        )

    return num, den


def _validate_frequency_vector(omega_rad_s: Iterable[float]) -> np.ndarray:
    omega = np.asarray(omega_rad_s, dtype=float).reshape(-1)
    if omega.size == 0:
        raise InputValidationError("Der Frequenzvektor ist leer.")
    if not np.all(np.isfinite(omega)):
        raise InputValidationError("Der Frequenzvektor enthält ungültige Werte.")
    if np.any(omega <= 0):
        raise InputValidationError("Alle Frequenzen müssen größer als null sein.")
    if np.any(np.diff(omega) < 0):
        omega = np.sort(omega)
    return omega


def calculate_frequency_response(
    system: ct.TransferFunction,
    omega_rad_s: Iterable[float],
) -> FrequencyResponse:
    """Berechnet Betrag und entfaltete Phase eines SISO-Systems."""

    omega = _validate_frequency_vector(omega_rad_s)
    response = ct.frequency_response(system, omega)

    magnitude = np.atleast_1d(np.asarray(response.magnitude, dtype=float).squeeze())
    phase_rad = np.atleast_1d(np.asarray(response.phase, dtype=float).squeeze())

    if magnitude.size != omega.size or phase_rad.size != omega.size:
        raise RuntimeError("Die Frequenzantwort besitzt eine unerwartete Dimension.")

    safe_magnitude = np.maximum(magnitude, np.finfo(float).tiny)
    magnitude_db = 20.0 * np.log10(safe_magnitude)
    phase_deg = np.rad2deg(np.unwrap(phase_rad))

    return FrequencyResponse(
        omega_rad_s=omega,
        magnitude=magnitude,
        magnitude_db=magnitude_db,
        phase_deg=phase_deg,
    )


def _to_scalar(value: object) -> float:
    array = np.asarray(value, dtype=float).reshape(-1)
    if array.size == 0:
        return float("nan")
    return float(array[0])


def calculate_stability_margins(system: ct.TransferFunction) -> StabilityMargins:
    """Berechnet die Stabilitätsreserven für negative Einheitsrückführung."""

    gm, pm, sm, wpc, wgc, wms = ct.stability_margins(system, method="best")
    gm = _to_scalar(gm)

    if np.isinf(gm):
        gm_db = float("inf")
    elif np.isfinite(gm) and gm > 0:
        gm_db = float(20.0 * np.log10(gm))
    else:
        gm_db = float("nan")

    return StabilityMargins(
        gain_margin_factor=gm,
        gain_margin_db=gm_db,
        phase_margin_deg=_to_scalar(pm),
        stability_margin=_to_scalar(sm),
        phase_crossover_rad_s=_to_scalar(wpc),
        gain_crossover_rad_s=_to_scalar(wgc),
        stability_margin_rad_s=_to_scalar(wms),
    )


def classify_continuous_poles(poles: Iterable[complex], *, tolerance: float = 1e-8) -> str:
    """Klassifiziert die Stabilität anhand kontinuierlicher Systempole."""

    pole_array = np.asarray(list(poles), dtype=complex).reshape(-1)
    if pole_array.size == 0:
        return "asymptotisch stabil"

    real_parts = pole_array.real
    if np.any(real_parts > tolerance):
        return "instabil"
    if np.all(real_parts < -tolerance):
        return "asymptotisch stabil"

    axis_poles = pole_array[np.abs(real_parts) <= tolerance]
    for index, pole in enumerate(axis_poles):
        multiplicity = np.sum(np.abs(axis_poles - pole) <= 100 * tolerance)
        if multiplicity > 1:
            return "instabil (mehrfacher Pol auf der imaginären Achse)"

    return "grenzstabil (nicht asymptotisch stabil)"


def analyze_system(
    numerator: str | Iterable[float],
    denominator: str | Iterable[float],
    omega_rad_s: Iterable[float],
) -> SystemAnalysis:
    """Führt die vollständige Analyse einer offenen Kreisübertragungsfunktion aus."""

    num, den = validate_transfer_function(numerator, denominator)
    open_loop = ct.tf(num, den)
    closed_loop = ct.feedback(open_loop, 1, sign=-1)

    open_poles = np.asarray(ct.poles(open_loop), dtype=complex)
    open_zeros = np.asarray(ct.zeros(open_loop), dtype=complex)
    closed_poles = np.asarray(ct.poles(closed_loop), dtype=complex)
    closed_zeros = np.asarray(ct.zeros(closed_loop), dtype=complex)

    return SystemAnalysis(
        numerator=num,
        denominator=den,
        open_loop=open_loop,
        closed_loop=closed_loop,
        open_loop_poles=open_poles,
        open_loop_zeros=open_zeros,
        closed_loop_poles=closed_poles,
        closed_loop_zeros=closed_zeros,
        open_loop_stability=classify_continuous_poles(open_poles),
        closed_loop_stability=classify_continuous_poles(closed_poles),
        margins=calculate_stability_margins(open_loop),
        response=calculate_frequency_response(open_loop, omega_rad_s),
    )


def _normalise_column_name(column: object) -> str:
    text = unicodedata.normalize("NFKD", str(column).strip().lower())
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.replace("ω", "omega")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


_COLUMN_ALIASES = {
    "omega_rad_s": {
        "omega_rad_s",
        "omega_rads",
        "kreisfrequenz_rad_s",
        "kreisfrequenz_rads",
    },
    "frequency_hz": {"frequency_hz", "frequenz_hz", "f_hz"},
    "magnitude_db": {
        "magnitude_db",
        "amplitude_db",
        "betrag_db",
        "verstaerkung_db",
        "gain_db",
    },
    "phase_deg": {"phase_deg", "phase_degree", "phase_degrees", "phase_grad"},
}


def _decode_csv(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvValidationError("Die Datei muss UTF-8- oder Windows-1252-codiert sein.")


def _read_csv_bytes(source: bytes | bytearray | str | BinaryIO) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, bytearray):
        return bytes(source)
    if isinstance(source, str):
        return source.encode("utf-8")
    if hasattr(source, "read"):
        value = source.read()
        return value.encode("utf-8") if isinstance(value, str) else bytes(value)
    raise CsvValidationError("Die hochgeladene Datei konnte nicht gelesen werden.")


def _detect_csv_format(text: str) -> tuple[str, str]:
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if not first_line:
        raise CsvValidationError("Die CSV-Datei ist leer.")

    counts = {";": first_line.count(";"), "\t": first_line.count("\t"), ",": first_line.count(",")}
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] == 0:
        raise CsvValidationError(
            "Es wurde kein unterstütztes Trennzeichen (Komma, Semikolon oder Tabulator) erkannt."
        )
    decimal = "," if delimiter == ";" else "."
    return delimiter, decimal


def load_measurement_csv(source: bytes | bytearray | str | BinaryIO) -> pd.DataFrame:
    """Lädt und validiert Messdaten aus einer CSV-Datei.

    Das Ergebnis enthält immer die kanonischen Spalten ``omega_rad_s``,
    ``frequency_hz``, ``magnitude_db`` und ``phase_deg``.
    """

    raw_bytes = _read_csv_bytes(source)
    if not raw_bytes:
        raise CsvValidationError("Die CSV-Datei ist leer.")
    if len(raw_bytes) > 5_000_000:
        raise CsvValidationError("Die CSV-Datei ist größer als 5 MB.")

    text = _decode_csv(raw_bytes)
    delimiter, decimal = _detect_csv_format(text)

    try:
        dataframe = pd.read_csv(StringIO(text), sep=delimiter, decimal=decimal)
    except (pd.errors.ParserError, UnicodeError, ValueError) as exc:
        raise CsvValidationError(f"Die CSV-Datei konnte nicht eingelesen werden: {exc}") from exc

    if dataframe.empty:
        raise CsvValidationError("Die CSV-Datei enthält keine Messwerte.")
    if len(dataframe) > 10_000:
        raise CsvValidationError("Es werden höchstens 10.000 Messpunkte unterstützt.")

    recognised: dict[str, str] = {}
    for original in dataframe.columns:
        normalised = _normalise_column_name(original)
        for canonical, aliases in _COLUMN_ALIASES.items():
            if normalised in aliases:
                if canonical in recognised:
                    raise CsvValidationError(
                        f"Die Größe '{canonical}' ist durch mehrere CSV-Spalten definiert."
                    )
                recognised[canonical] = str(original)

    frequency_columns = [name for name in ("omega_rad_s", "frequency_hz") if name in recognised]
    if len(frequency_columns) != 1:
        raise CsvValidationError(
            "Die Datei muss genau eine Frequenzspalte enthalten: 'omega_rad_s' oder 'frequency_hz'."
        )
    for required in ("magnitude_db", "phase_deg"):
        if required not in recognised:
            raise CsvValidationError(f"Die erforderliche Spalte '{required}' fehlt.")

    selected = {
        canonical: dataframe[original].copy()
        for canonical, original in recognised.items()
        if canonical in {frequency_columns[0], "magnitude_db", "phase_deg"}
    }
    result = pd.DataFrame(selected)

    invalid_rows: set[int] = set()
    for column in result.columns:
        values = result[column]
        if pd.api.types.is_object_dtype(values.dtype) or pd.api.types.is_string_dtype(
            values.dtype
        ):
            values = values.astype(str).str.strip().str.replace(",", ".", regex=False)
        numeric = pd.to_numeric(values, errors="coerce")
        invalid = numeric.isna() | ~np.isfinite(numeric.to_numpy(dtype=float))
        invalid_rows.update((numeric.index[invalid] + 2).tolist())
        result[column] = numeric

    if invalid_rows:
        rows = ", ".join(str(row) for row in sorted(invalid_rows)[:8])
        suffix = " …" if len(invalid_rows) > 8 else ""
        raise CsvValidationError(f"Ungültige oder fehlende Zahlenwerte in CSV-Zeile {rows}{suffix}.")

    frequency_column = frequency_columns[0]
    if frequency_column == "frequency_hz":
        result.insert(0, "omega_rad_s", result["frequency_hz"] * 2.0 * np.pi)
    else:
        result.insert(1, "frequency_hz", result["omega_rad_s"] / (2.0 * np.pi))

    if np.any(result["omega_rad_s"] <= 0):
        raise CsvValidationError("Alle Messfrequenzen müssen größer als null sein.")
    if len(result) < 2:
        raise CsvValidationError("Die Datei muss mindestens zwei Messpunkte enthalten.")

    return result[
        ["omega_rad_s", "frequency_hz", "magnitude_db", "phase_deg"]
    ].sort_values("omega_rad_s", ignore_index=True)


def _wrapped_phase_difference(measured_deg: np.ndarray, theoretical_deg: np.ndarray) -> np.ndarray:
    return (measured_deg - theoretical_deg + 180.0) % 360.0 - 180.0


def compare_measurements(
    system: ct.TransferFunction,
    measurements: pd.DataFrame,
) -> MeasurementComparison:
    """Vergleicht validierte Messpunkte mit der Theorie bei identischen Frequenzen."""

    required = {"omega_rad_s", "frequency_hz", "magnitude_db", "phase_deg"}
    if not required.issubset(measurements.columns):
        raise CsvValidationError("Die Messdatentabelle wurde nicht vollständig validiert.")

    data = measurements.copy().sort_values("omega_rad_s", ignore_index=True)
    theory = calculate_frequency_response(system, data["omega_rad_s"].to_numpy())

    magnitude_error = data["magnitude_db"].to_numpy() - theory.magnitude_db
    phase_error = _wrapped_phase_difference(
        data["phase_deg"].to_numpy(), theory.phase_deg
    )

    data["theoretical_magnitude_db"] = theory.magnitude_db
    data["magnitude_error_db"] = magnitude_error
    data["theoretical_phase_deg"] = theory.phase_deg
    data["phase_error_deg"] = phase_error
    # Für die gemeinsame Darstellung wird die äquivalente Phasenlage gewählt,
    # die dem theoretischen Verlauf am nächsten liegt.
    data["phase_deg_aligned"] = theory.phase_deg + phase_error

    return MeasurementComparison(
        data=data,
        magnitude_mae_db=float(np.mean(np.abs(magnitude_error))),
        magnitude_max_error_db=float(np.max(np.abs(magnitude_error))),
        phase_mae_deg=float(np.mean(np.abs(phase_error))),
        phase_max_error_deg=float(np.max(np.abs(phase_error))),
    )
