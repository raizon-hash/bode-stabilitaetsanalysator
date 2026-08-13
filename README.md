# Bode- und Stabilitätsanalysator

Interaktive Streamlit-Web-App zur regelungstechnischen Analyse linearer,
zeitinvarianter SISO-Systeme. Das Projekt entsteht im Lernfeld LF 10.2 und
verwendet Inhalte aus LF 8.

## Funktionsumfang

- Eingabe einer offenen Kreisübertragungsfunktion über Zähler- und
  Nennerkoeffizienten
- Berechnung des theoretischen Frequenzgangs
- interaktives Bode-Diagramm für Betrag und Phase
- Berechnung von Durchtrittsfrequenz, Phasenreserve, Amplitudenreserve und
  Stabilitätsreserve
- Bildung des geschlossenen Kreises bei negativer Einheitsrückführung
- Stabilitätsbewertung anhand der geschlossenen Pole
- Darstellung der Pole und Nullstellen in der komplexen Ebene
- CSV-Import gemessener Frequenzgänge
- Vergleich zwischen Messung und Theorie einschließlich Abweichungskennwerten
- verständliche Fehlermeldungen bei ungültigen Eingaben und Dateien

## Mathematisches Modell

Die eingegebene Übertragungsfunktion wird als offene Kreisübertragungsfunktion
interpretiert:

```text
          b_m s^m + ... + b_1 s + b_0
G_0(s) = -----------------------------
          a_n s^n + ... + a_1 s + a_0
```

Für eine negative Einheitsrückführung wird der geschlossene Kreis mit

```text
G_w(s) = G_0(s) / (1 + G_0(s))
```

gebildet. Ein kontinuierliches System wird genau dann als asymptotisch stabil
bewertet, wenn alle geschlossenen Pole strikt in der linken Halbebene liegen.
Die klassischen Stabilitätsreserven werden für `G_0(s)` berechnet.

## Koeffizienteneingabe

Die Koeffizienten werden in absteigender Potenzreihenfolge eingegeben.

Beispiel:

```text
Zähler: 1
Nenner: 1, 1, 0
```

entspricht

```text
G_0(s) = 1 / (s² + s) = 1 / (s(s + 1)).
```

Als Trennzeichen sind Kommas, Semikolons oder Leerzeichen erlaubt. Bei
Dezimalzahlen mit deutschem Dezimalkomma muss das Semikolon als Trennzeichen
verwendet werden, beispielsweise `0,5; 1; 0`.

## CSV-Format

Die App akzeptiert UTF-8- und Windows-1252-Dateien sowie Komma-, Semikolon-
und Tabulator-Trennung. Deutsche Excel-CSV-Dateien mit Semikolon und
Dezimalkomma werden unterstützt.

Erforderlich sind jeweils eine Frequenz-, Betrags- und Phasenspalte:

| Größe | Unterstützte Spaltennamen |
| --- | --- |
| Frequenz | `omega_rad_s` oder `frequency_hz` |
| Betrag | `magnitude_db` |
| Phase | `phase_deg` |

Ein vollständiges Beispiel befindet sich in
[`examples/messdaten_beispiel.csv`](examples/messdaten_beispiel.csv).

## Lokaler Start

Voraussetzung ist Python 3.12. Diese Version wird auch für die Bereitstellung
verwendet.

```bash
python -m venv .venv
```

Unter Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Unter Linux oder macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Die Tests prüfen unter anderem ein System mit analytisch bekannten
Stabilitätsreserven, einen instabilen geschlossenen Kreis sowie verschiedene
gültige und fehlerhafte CSV-Dateien.

## Deployment auf Streamlit Community Cloud

1. Auf [share.streamlit.io](https://share.streamlit.io/) mit GitHub anmelden.
2. Dieses Repository und den Branch `main` auswählen.
3. Als Startdatei `streamlit_app.py` angeben.
4. Unter **Advanced settings** Python 3.12 auswählen bzw. die Voreinstellung
   beibehalten.
5. Die App bereitstellen.

Nach jedem Push auf den Branch `main` wird die bereitgestellte App automatisch
aktualisiert.

## Projektstruktur

```text
.
├── .streamlit/config.toml
├── calculations.py
├── streamlit_app.py
├── requirements.txt
├── requirements-dev.txt
├── examples/messdaten_beispiel.csv
└── tests/
    ├── test_calculations.py
    └── test_app.py
```

## Fachliche Einschränkungen

- Untersucht werden kontinuierliche SISO-Systeme mit reellen Koeffizienten.
- Nichtkausale bzw. unechte Übertragungsfunktionen werden abgewiesen.
- Die Stabilitätsreserven beziehen sich auf negative Einheitsrückführung.
- Pole des geschlossenen Kreises sind das entscheidende Stabilitätskriterium;
  positive Bode-Reserven allein reichen bei offenen instabilen Systemen nicht
  als Stabilitätsnachweis aus.
