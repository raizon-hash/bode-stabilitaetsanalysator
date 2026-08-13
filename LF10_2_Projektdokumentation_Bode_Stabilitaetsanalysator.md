---
lang: de-DE
title: "Projektdokumentation"
subtitle: "Regelungstechnischer Bode- und Stabilitätsanalysator mit Messdatenvergleich"
date: "Stand: 13. August 2026"
subject: "LF 10.2 - Technische Web-Applikation mit Python"
keywords:
  - Python
  - Streamlit
  - Bode-Diagramm
  - Stabilitätsanalyse
  - Messdaten
---

\newpage

# Kurzfassung

Im Lernfeld **LF 10.2 - Spezielle Anwendungsprojekte** wurde eine technische
Web-Applikation mit Python entwickelt. Das bestätigte Projektthema lautet
**„Regelungstechnischer Bode- und Stabilitätsanalysator mit
Messdatenvergleich“**. Die App analysiert kontinuierliche lineare
SISO-Systeme anhand ihrer Übertragungsfunktion. Sie berechnet den
Frequenzgang, stellt das Bode-Diagramm interaktiv dar, bestimmt klassische
Stabilitätsreserven, untersucht die Pole des geschlossenen Kreises und
vergleicht theoretische Werte mit importierten Messdaten.

Der Berechnungskern wurde von der Benutzeroberfläche getrennt aufgebaut. Zum
Einsatz kommen Python 3.12, NumPy, Pandas, SciPy, Plotly, die Python Control
Systems Library und Streamlit. Der Quellcode wird in einem öffentlichen
GitHub-Repository verwaltet. Die veröffentlichte Anwendung läuft auf
Streamlit Community Cloud.

Die im ursprünglichen Aufgabenleitfaden vorgesehene Veröffentlichung über
Hugging Face Spaces konnte nicht wie beschrieben umgesetzt werden. Der
eingebaute Streamlit-SDK von Hugging Face wurde 2025 eingestellt. Streamlit
muss dort inzwischen über einen Docker Space betrieben werden; für neu
angelegte Docker- oder reguläre Gradio-Spaces mit Rechenleistung ist ein
kostenpflichtiger Tarif erforderlich. Deshalb wurde als kostenlose und für
Streamlit besser geeignete Alternative Streamlit Community Cloud gewählt.

Die fertige Anwendung wurde mit **18 automatisierten Tests** und zusätzlichen
Live-Tests im Browser geprüft. Dabei wurde ein versionsabhängiger Fehler bei
deutschen CSV-Dateien unter Pandas 3 gefunden, behoben und durch einen
Regressionstest abgesichert. Nach dem abschließenden Deployment funktionierten
die Korrektur, der CSV-Vergleich und alle wesentlichen Bedienfunktionen auch in
der öffentlich erreichbaren App.

| Ergebnis | Adresse |
|---|---|
| Live-App | <https://bode-stabilitaetsanalysator-agpzycecrpkmmtvdsobuqb.streamlit.app/> |
| Quellcode | <https://github.com/raizon-hash/bode-stabilitaetsanalysator> |

# 1. Ausgangslage und Aufgabenstellung

## 1.1 Didaktischer Rahmen

Die schulische Aufgabenstellung verlangt die Entwicklung einer technischen
Web-Applikation mit Python. Die App soll ein technisches Fachthema praktisch
umsetzen und mindestens folgende Bestandteile besitzen:

- interaktive Parametereingaben,
- Import externer Daten, insbesondere CSV-Dateien,
- automatisierte mathematische Berechnungen,
- dynamische Diagramme,
- strukturierte Ergebnis- und Tabellenausgaben,
- verständliche Fehlerbehandlung sowie
- systematische Tests mit Grenzwerten und fehlerhaften Eingaben.

Der Leitfaden legt besonderen Wert auf eine funktionierende und stabile
Anwendung. Funktionalität und Stabilität bilden 50 Prozent der Bewertung. Die
anderen 50 Prozent entfallen auf eine 15-minütige Live-Präsentation, in der
neben der App auch technische Probleme und deren Lösungen erläutert werden.

## 1.2 Abgrenzung

Diese Dokumentation behandelt ausschließlich das LF-10.2-Projekt zum Bode-
und Stabilitätsanalysator. Unterlagen und Gespräche zur Klausurvorbereitung
über Gleichstrommaschinen gehören zu einem anderen Lernfeld und wurden weder
für die Implementierung noch für die Dokumentation verwendet.

## 1.3 Bestätigtes Thema und Pflichtumfang

Das Thema wurde am 1. Juli 2026 mit folgendem Umfang angenommen:

- Eingabe einer allgemeinen offenen Kreisübertragungsfunktion,
- Berechnung und Darstellung des Bode-Diagramms,
- Anzeige von Polen und Nullstellen,
- Berechnung von Durchtrittsfrequenz, Phasenreserve und Amplitudenreserve,
- Bewertung der Stabilität des geschlossenen Kreises,
- Import und Vergleich gemessener Frequenzgangdaten,
- Export beziehungsweise Bereitstellung einer Beispiel-CSV sowie
- robuste Behandlung fehlerhafter Eingaben und Dateien.

Die erste Planung sah vor, den Python-Berechnungskern zunächst unabhängig von
der Oberfläche, gegebenenfalls in Google Colab, zu prüfen und danach die
grafische Oberfläche mit Streamlit aufzubauen. Dieses Prinzip wurde in der
endgültigen Projektstruktur beibehalten: Fachlogik und Oberfläche liegen in
getrennten Python-Dateien.

# 2. Zielsetzung

Die Anwendung soll die regelungstechnische Analyse eines kontinuierlichen,
linearen SISO-Systems erleichtern. Anstelle einer festen Strecke kann der
Anwender die Koeffizienten einer Übertragungsfunktion selbst eingeben oder ein
vorbereitetes Beispielsystem auswählen.

Aus den Eingaben soll die App:

1. die offene Kreisübertragungsfunktion bilden,
2. den theoretischen Frequenzgang berechnen,
3. Betrag und Phase als Bode-Diagramm darstellen,
4. Stabilitätsreserven bestimmen,
5. den geschlossenen Kreis bei negativer Einheitsrückführung bilden,
6. seine Pole und Stabilität bewerten und
7. hochgeladene Messwerte mit der Theorie vergleichen.

Die App soll auch bei ungültigen Eingaben kontrolliert reagieren. Ein Fehler
darf nicht zu einem sichtbaren Absturz führen, sondern muss als verständlicher
Hinweis ausgegeben werden.

# 3. Fachliche Grundlagen

## 3.1 Offene Kreisübertragungsfunktion

Die eingegebenen Koeffizienten beschreiben die offene
Kreisübertragungsfunktion

$$
G_0(s)=\frac{b_m s^m + \dots + b_1s + b_0}
             {a_n s^n + \dots + a_1s + a_0}.
$$

Zähler- und Nennerkoeffizienten werden in absteigender Potenzreihenfolge
eingegeben. Das Beispiel

```text
Zähler: 1
Nenner: 1, 1, 0
```

entspricht

$$
G_0(s)=\frac{1}{s^2+s}=\frac{1}{s(s+1)}.
$$

## 3.2 Frequenzgang und Bode-Diagramm

Für den Frequenzgang wird $s=j\omega$ eingesetzt. Der Betrag wird in Dezibel
und die Phase in Grad ausgegeben:

$$
L(\omega)=20\log_{10}\left|G_0(j\omega)\right|,
\qquad
\varphi(\omega)=\arg\left(G_0(j\omega)\right).
$$

Die Frequenzachse ist logarithmisch. Der Anwender kann zwischen Kreisfrequenz
$\omega$ in rad/s und Frequenz $f$ in Hz umschalten. Die Umrechnung lautet

$$
f=\frac{\omega}{2\pi}.
$$

## 3.3 Geschlossener Kreis

Für eine negative Einheitsrückführung wird die Führungsübertragungsfunktion

$$
G_w(s)=\frac{G_0(s)}{1+G_0(s)}
$$

gebildet. Ein kontinuierliches System ist asymptotisch stabil, wenn sämtliche
Pole des geschlossenen Kreises einen strikt negativen Realteil besitzen. Pole
auf der imaginären Achse werden als grenzstabil beziehungsweise nicht
asymptotisch stabil bewertet. Pole in der rechten Halbebene bedeuten
Instabilität.

## 3.4 Stabilitätskennwerte

Die App berechnet folgende Größen für den offenen Kreis:

| Kennwert | Bedeutung |
|---|---|
| Durchtrittsfrequenz $\omega_D$ | Frequenz, bei der der Betrag 0 dB erreicht |
| Phasenreserve $\varphi_R$ | Abstand der Phase bei $\omega_D$ zu $-180^\circ$ |
| Amplitudenreserve $A_R$ | zulässige Verstärkungsänderung bis zum Stabilitätsrand |
| Stabilitätsreserve $s_m$ | minimaler Abstand des Nyquist-Orts zur kritischen Stelle $-1$ |

Die klassischen Bode-Reserven sind bei einem bereits instabilen offenen Kreis
allein kein hinreichender Stabilitätsnachweis. Deshalb prüft die Anwendung
zusätzlich ausdrücklich die Pole des geschlossenen Kreises und warnt bei Polen
des offenen Kreises in der rechten Halbebene.

# 4. Technische Konzeption

## 4.1 Verwendete Werkzeuge

| Baustein | Aufgabe | Festgelegte Version |
|---|---|---:|
| Python | Programmiersprache | 3.12 |
| Streamlit | Web-Oberfläche | 1.61.1 |
| NumPy | numerische Felder und Berechnungen | 2.5.2 |
| Pandas | CSV-Import und Tabellen | 3.0.5 |
| SciPy | numerische Hilfsfunktionen | 1.18.0 |
| Plotly | interaktive Diagramme | 6.9.0 |
| Python Control Systems Library | Übertragungsfunktionen und Regelungstechnik | 0.10.2 |
| PyArrow | Tabellenunterstützung in Streamlit | 19.0.1 |
| Pytest | automatisierte Tests | 8.3 bis unter 10 |

Die Versionen der Laufzeitabhängigkeiten sind in `requirements.txt` fest
eingetragen. Dies reduziert das Risiko, dass ein späteres automatisches Update
das Verhalten der veröffentlichten App verändert.

## 4.2 Aufbau der Anwendung

| Datei oder Ordner | Verantwortung |
|---|---|
| `calculations.py` | Validierung, Frequenzgang, Reserven, Stabilität und CSV-Vergleich |
| `streamlit_app.py` | Oberfläche, Formeln, Kennwertkarten, Diagramme und Tabellen |
| `requirements.txt` | reproduzierbare Laufzeitabhängigkeiten |
| `requirements-dev.txt` | Testabhängigkeiten |
| `examples/` | Beispielmessdaten im deutschen CSV-Format |
| `tests/test_calculations.py` | Tests des mathematischen Kerns und CSV-Imports |
| `tests/test_app.py` | Integrationstests der Streamlit-Oberfläche |
| `.streamlit/config.toml` | dunkles Farbschema und Serverkonfiguration |

Diese Trennung ermöglicht es, die mathematischen Funktionen ohne Browser und
ohne Streamlit-Oberfläche zu testen. Die Oberfläche ruft nur validierte
Funktionen aus dem Berechnungskern auf.

## 4.3 Datenfluss

1. Der Nutzer wählt ein Beispielsystem oder trägt Koeffizienten ein.
2. Die Eingaben werden geparst und auf endliche Zahlen, gültige Polynome und
   eine kausale Übertragungsfunktion geprüft.
3. Für einen logarithmischen Frequenzvektor werden Frequenzgang und
   Stabilitätskennwerte berechnet.
4. Aus $G_0(s)$ wird $G_w(s)$ gebildet; anschließend werden Pole und
   Stabilitätsklasse bestimmt.
5. Optional geladene Messdaten werden normalisiert, validiert und bei ihren
   Originalfrequenzen mit dem Modell verglichen.
6. Streamlit aktualisiert Kennwerte, Diagramme und Tabellen automatisch.

# 5. Umsetzung der Benutzeroberfläche

## 5.1 Eingabebereich

Die Seitenleiste enthält:

- eine Auswahl vorbereiteter Beispielsysteme,
- Eingabefelder für Zähler- und Nennerkoeffizienten,
- eine Umschaltung zwischen rad/s und Hz,
- minimale und maximale Darstellungsfrequenz,
- einen Schieberegler mit 200 bis 2000 Berechnungspunkten,
- eine Checkbox für die Markierung von Grenzfrequenzen sowie
- den CSV-Dateiupload.

Dezimalzahlen mit deutschem Komma werden unterstützt, wenn die Koeffizienten
mit Semikolon getrennt werden, beispielsweise `0,5; 1; 0`.

## 5.2 Ergebnisbereich

Im Hauptbereich werden zuerst $G_0(s)$ und $G_w(s)$ in mathematischer Form
angezeigt. Daneben erscheint eine farbige Stabilitätsmeldung. Vier Kennwertkarten
zeigen Durchtrittsfrequenz, Phasenreserve, Amplitudenreserve und
Stabilitätsreserve.

Die weiteren Inhalte sind in vier Register gegliedert:

| Register | Inhalt |
|---|---|
| Bode-Diagramm | Betrag und Phase, Messpunkte sowie optionale Grenzfrequenzen |
| Pole und Stabilität | Pol-Nullstellen-Diagramm, Stabilitätsbewertung und Wertetabelle |
| Messdatenvergleich | Fehlerkennwerte, Fehlerdiagramm und vollständige Vergleichstabelle |
| Hinweise | Erläuterung der Kennwerte und unterstütztes CSV-Format |

Das Farbschema ist in `.streamlit/config.toml` definiert. Nach dem letzten
Deployment wurde das dunkle Schema mit hellem Text und blauen Akzenten live
überprüft.

# 6. CSV-Import und Messdatenvergleich

## 6.1 Unterstütztes Format

Eine Datei benötigt genau eine Frequenzspalte sowie Betrag und Phase:

| Größe | Spaltenname |
|---|---|
| Kreisfrequenz | `omega_rad_s` |
| alternativ Frequenz | `frequency_hz` |
| Betrag | `magnitude_db` |
| Phase | `phase_deg` |

Die App erkennt Komma, Semikolon und Tabulator als Trennzeichen. Unterstützt
werden UTF-8 und Windows-1252. Bei Semikolon-Trennung wird das deutsche
Dezimalkomma verarbeitet. Zulässig sind höchstens 10.000 Messpunkte und eine
Dateigröße bis 5 MB. Jede Frequenz muss größer als null sein; mindestens zwei
Messpunkte sind erforderlich.

## 6.2 Vergleichsberechnung

Für jede Messfrequenz berechnet die App den theoretischen Frequenzgang des
eingegebenen Modells. Anschließend werden Betrags- und Phasenabweichung
bestimmt. Phasen werden modulo $360^\circ$ so ausgerichtet, dass äquivalente
Phasendarstellungen nicht fälschlich als großer Fehler erscheinen.

Ausgegeben werden:

- mittlere absolute Betragsabweichung,
- maximale absolute Betragsabweichung,
- mittlere absolute Phasenabweichung und
- maximale absolute Phasenabweichung.

Die vollständige Vergleichstabelle kann über die Downloadfunktion der
Streamlit-Datentabelle wieder als CSV gespeichert werden. Zusätzlich stellt
die App eine Beispiel-CSV als Vorlage bereit.

Die mitgelieferte Beispiel-CSV enthält acht Messpunkte. Im Referenztest ergeben
sich:

| Kennwert | Ergebnis |
|---|---:|
| mittlere absolute Betragsabweichung | 0,125 dB |
| maximale absolute Betragsabweichung | 0,180 dB |
| mittlere absolute Phasenabweichung | 0,612° |
| maximale absolute Phasenabweichung | 0,900° |

# 7. Veröffentlichung und Plattformwechsel

## 7.1 Ursprünglicher Plan: Hugging Face Spaces

Der schulische Leitfaden vom Juli 2026 beschreibt Hugging Face Spaces als
kostenloses Cloud-Hosting. Vorgesehen waren ein neuer Docker Space, das
Streamlit-Template und die kostenlose Stufe „CPU Basic“.

Diese Anleitung entspricht nicht mehr vollständig dem aktuellen Produktstand.
Laut offizieller Hugging-Face-Dokumentation wurde Streamlit am 30. April 2025
als eingebauter SDK eingestellt. Eine Streamlit-App muss seither über das
Docker-Template erstellt werden. Die aktuelle Spaces-Übersicht erklärt zudem,
dass statische Spaces kostenlos bleiben, während neue Gradio- und Docker-Spaces
mit Rechenleistung für persönliche Konten einen PRO-Tarif und für
Organisationen einen Team- oder Enterprise-Tarif erfordern.

Die häufig verwendete Kurzform „Hugging Face ist jetzt Bezahlware“ trifft für
den hier benötigten Anwendungsfall zu, ist allgemein aber zu pauschal: Der Hub,
statische Spaces und bestimmte ZeroGPU-Sonderfälle besitzen weiterhin
kostenlose Nutzungsmöglichkeiten. **Für diese ausführbare Streamlit-App wäre
jedoch ein Docker Space nötig gewesen, dessen Erstellung inzwischen einen
bezahlten Plan voraussetzt.**

## 7.2 Gewählte Alternative: Streamlit Community Cloud

Als Alternative wurde Streamlit Community Cloud verwendet. Der Dienst ist auf
Streamlit-Apps spezialisiert, verbindet sich direkt mit GitHub und bietet laut
offizieller Dokumentation eine kostenlose Bereitstellung für Community-Apps.

Der Ablauf war:

1. öffentliches GitHub-Repository anlegen,
2. Python-Dateien, Abhängigkeiten, Tests und Beispiel-CSV hochladen,
3. Streamlit Community Cloud mit GitHub verbinden,
4. Repository `raizon-hash/bode-stabilitaetsanalysator`, Branch `main` und
   Startdatei `streamlit_app.py` auswählen,
5. Python 3.12 verwenden und die App bereitstellen,
6. nach Änderungen auf `main` den automatischen Neuaufbau prüfen.

GitHub ist für eine lokal ausgeführte Streamlit-App nicht zwingend notwendig.
Für den hier gewählten Deployment-Weg ist ein GitHub-Repository jedoch die
Quellcodebasis, aus der Streamlit Community Cloud die App installiert und bei
neuen Commits aktualisiert.

# 8. Teststrategie

## 8.1 Automatisierte Tests

Die Tests wurden mit exakt den in `requirements.txt` festgelegten
Deployment-Versionen ausgeführt:

```bash
python -m pytest -q
```

Abschließendes Ergebnis:

```text
..................                                                       [100%]
18 passed
```

Die 18 Tests decken folgende Bereiche ab:

| Testgruppe | Geprüftes Verhalten |
|---|---|
| Koeffizienten | verschiedene Trennzeichen, leere Werte, Nullpolynom, Text und nicht endliche Zahlen |
| Übertragungsfunktion | Zurückweisung einer unechten beziehungsweise nichtkausalen Funktion |
| Referenzsystem | bekannte Reserven und stabiler geschlossener Kreis |
| Instabilität | Erkennung eines instabilen geschlossenen Kreises |
| deutsche CSV | Semikolon und Dezimalkomma |
| Hz-CSV | korrekte Umrechnung in rad/s |
| fehlerhafte CSV | fehlende Spalten, Frequenz null und ungültige Zahlen |
| Regression Pandas 3 | ausschließlich die tatsächlich fehlerhafte CSV-Zeile wird genannt |
| Phasenvergleich | um $360^\circ$ äquivalente Werte ergeben keinen Fehler |
| Streamlit-Integration | App-Start, instabiles Preset und Beispiel-CSV ohne Absturz |

## 8.2 Live-Tests der veröffentlichten App

Zusätzlich zu Pytest wurde die veröffentlichte Anwendung im Browser bedient.
Dabei wurden sichtbare Ergebnisse, Fehlermeldungen, Diagramme, Tabellen und
Browserprotokolle geprüft.

| Testfall | Beobachtetes Ergebnis | Status |
|---|---|:---:|
| Referenz $1/(s(s+1))$ | $\omega_D=0{,}786$ rad/s, $\varphi_R=51{,}8^\circ$, $A_R=\infty$, $s_m=0{,}681$ | bestanden |
| Umschaltung auf Hz | Durchtritt bei 0,125 Hz | bestanden |
| PT2-Preset | Durchtritt 2 rad/s, Phasenreserve 90°, stabil | bestanden |
| instabiles Preset | Instabilitätsmeldung, negative Phasen- und Amplitudenreserve | bestanden |
| Poltabelle Referenzsystem | offene Pole $0,-1$; geschlossene Pole $-0{,}5\pm j0{,}866$ | bestanden |
| eigenes System mit Dezimalkomma | Eingabe wird verarbeitet und stabil bewertet | bestanden |
| Nullnenner | verständliche Meldung statt Absturz | bestanden |
| Minimum gleich Maximum | klare Frequenzbereichsmeldung; Berechnung stoppt kontrolliert | bestanden |
| 200 und 2000 Punkte | beide Grenzwerte ohne Absturz | bestanden |
| Grenzfrequenz-Checkbox | Markierungen werden ein- und ausgeblendet | bestanden |
| gültige deutsche CSV | vier korrekte Fehlerkennwerte und acht Tabellenzeilen | bestanden |
| gültige Hz-CSV | gleiche Messdaten korrekt umgerechnet | bestanden |
| fehlende Phasenspalte | gezielte Fehlermeldung | bestanden |
| ungültiger Zahlenwert | gezielte Zeilenmeldung | bestanden nach Korrektur |
| Frequenz null | gezielte Fehlermeldung | bestanden |
| leere CSV | gezielte Fehlermeldung | bestanden |
| offener Pol rechts | Warnung vor unzureichender Aussage der Bode-Reserven | bestanden |
| Browserprotokoll | keine Fehler aus der App-Domain | bestanden |
| dunkles Theme | Hintergrund und Textfarben aus `config.toml` aktiv | bestanden |

## 8.3 Grenzen der Testumgebung

Der Beispiel-CSV-Downloadbutton war sichtbar, aktiviert und entsprechend der
offiziellen Streamlit-API implementiert. Der automatisierte Cloud-Browser
konnte das erzeugte Download-Ereignis jedoch nicht binär abfangen. Derselbe
Effekt trat bei der offiziellen Streamlit-Demoseite auf. Deshalb ist dies kein
nachgewiesener Fehler der App, aber ein manueller Klicktest in einem normalen
Desktop-Browser bleibt vor der Präsentation sinnvoll.

Eine echte mobile Viewport-Emulation stand im verwendeten Testbrowser nicht
zur Verfügung. Die Desktopdarstellung wurde visuell geprüft; eine zusätzliche
Kontrolle auf einem Smartphone oder mit den Entwicklerwerkzeugen eines lokalen
Browsers ist empfehlenswert.

# 9. Aufgetretene Probleme und Lösungen

## 9.1 Hugging-Face-Anleitung nicht mehr aktuell

**Beobachtung:** Das im Aufgabenleitfaden beschriebene kostenlose
Docker-/Streamlit-Template ließ sich mit einem neuen persönlichen Konto nicht
mehr kostenlos anlegen.

**Ursache:** Der eingebaute Streamlit-SDK ist eingestellt; Streamlit benötigt
einen Docker Space. Für neue Docker- und reguläre Gradio-Spaces mit Compute ist
inzwischen ein kostenpflichtiger Tarif erforderlich.

**Lösung:** Wechsel zu GitHub und Streamlit Community Cloud. Dadurch blieb die
App kostenlos öffentlich erreichbar und Updates konnten über GitHub-Commits
automatisiert bereitgestellt werden.

## 9.2 Verdeckter Ordner beim manuellen GitHub-Upload

**Beobachtung:** Beim ersten Upload fehlte `.streamlit/config.toml`. Die App
funktionierte, verwendete aber zunächst das Standardfarbschema.

**Ursache:** Ordner mit führendem Punkt sind auf vielen Systemen verborgen und
wurden beim manuellen Datei-Upload übersehen.

**Lösung:** Auf GitHub wurde der Zielpfad `.streamlit/config.toml` ausdrücklich
angelegt. Nach dem Commit baute Streamlit die App neu; das dunkle Farbschema
war anschließend live aktiv.

## 9.3 Getrennte lokale und entfernte Git-Historien

**Beobachtung:** Der lokale Entwicklungscommit und die über die GitHub-Webseite
erzeugten Upload-Commits hatten denselben Dateibestand, aber unterschiedliche
Commit-Historien. Ein direktes Zusammenführen meldete deshalb bei zwei Dateien
einen Add/Add-Konflikt.

**Lösung:** Die Konflikte wurden anhand der bereits getesteten Fassungen
aufgelöst. Inhaltlich wurden nur der CSV-Fix, sein Regressionstest und die
fehlende Streamlit-Konfiguration übernommen. Vor der Veröffentlichung wurden
alle Tests erneut ausgeführt. Die endgültigen Dateien wurden anschließend
manuell auf GitHub hochgeladen und der öffentliche Stand bytegenau mit der
getesteten lokalen Fassung verglichen.

## 9.4 Pandas-3-Fehler bei deutschem Dezimalkomma

**Beobachtung:** Eine Testdatei enthielt in CSV-Zeile 2 den Text `kein_wert`.
Die Live-App wies die Datei korrekt ab, meldete aber fälschlich die Zeilen
„2, 3“, obwohl Zeile 3 gültig war.

**Ursache:** Unter Pandas 3 können Textspalten den neuen String-Datentyp statt
des bisherigen Datentyps `object` erhalten. Der Importcode ersetzte deutsche
Dezimalkommas zunächst nur bei `object`. Dadurch blieb der gültige Wert
`-2,900` in Zeile 3 unverarbeitet und wurde zusätzlich als ungültig bewertet.

**Korrektur:** Die Typprüfung berücksichtigt nun sowohl Objekt- als auch
String-Datentypen:

```python
if pd.api.types.is_object_dtype(values.dtype) or \
        pd.api.types.is_string_dtype(values.dtype):
    values = values.astype(str).str.strip().str.replace(",", ".", regex=False)
```

**Absicherung:** Ein neuer Regressionstest verwendet exakt die zuvor
fehlerhafte deutsche CSV. Er verlangt den eindeutigen Text
`Ungültige oder fehlende Zahlenwerte in CSV-Zeile 2.`. Nach dem Fix bestanden
18 von 18 Tests. Der gleiche Fall wurde nach dem automatischen Streamlit-
Redeployment live hochgeladen; die App nannte nur noch Zeile 2.

## 9.5 Einschränkungen der automatisierten Browserbedienung

Beim Datei-Upload öffnete ein technisch verstecktes HTML-Dateifeld den
Auswahldialog nicht zuverlässig. Die sichtbare Streamlit-Schaltfläche
funktionierte. Beim CSV-Download wurde im Testbrowser kein Download-Ereignis
bereitgestellt, auch nicht bei der offiziellen Streamlit-Demo. Diese Punkte
wurden als Einschränkungen des Testwerkzeugs und nicht als App-Abstürze
klassifiziert.

# 10. Ergebnisbewertung

## 10.1 Erfüllung der Mindestanforderungen

| Anforderung aus dem Leitfaden | Umsetzung |
|---|---|
| interaktive Parametereingabe | Textfelder, Auswahllisten, Zahlenfelder, Slider und Checkbox |
| Datenimport | CSV-/TXT-Uploader mit Format- und Plausibilitätsprüfung |
| CSV-Export | Beispiel-CSV und Download der angezeigten Vergleichstabelle |
| automatisierte Berechnungen | Frequenzgang, Reserven, geschlossener Kreis, Pole und Abweichungen |
| dynamische Diagramme | Bode-, Pol-Nullstellen- und Fehlerdiagramm mit Plotly |
| strukturierte Ausgaben | Kennwertkarten, Formeln und Datentabellen |
| Fehlerbehandlung | gezielte Meldungen für Eingaben, Frequenzbereich und CSV-Dateien |
| intensives Testen | 18 automatisierte Tests plus umfangreiche Live-Testmatrix |
| Online-Bereitstellung | öffentliche Streamlit-Community-Cloud-URL |

## 10.2 Fachliche Bewertung

Das Referenzsystem liefert die erwarteten analytischen Kennwerte und die
korrekten geschlossenen Pole. Ein absichtlich instabiles Beispiel wird als
instabil erkannt. Die App unterscheidet zwischen offenen Bode-Reserven und der
tatsächlichen Stabilität des geschlossenen Kreises. Damit wird eine wichtige
fachliche Fehlinterpretation vermieden.

Der Messdatenvergleich arbeitet an den tatsächlichen Messfrequenzen und
behandelt äquivalente Phasendarstellungen korrekt. Durch die detaillierte
CSV-Validierung werden unvollständige oder unplausible Daten verständlich
zurückgewiesen.

## 10.3 Technische Bewertung

Die Trennung von Berechnungskern und Oberfläche, festgelegte
Abhängigkeitsversionen, automatisierte Tests und ein nachvollziehbares
Deployment verbessern Wartbarkeit und Reproduzierbarkeit. Nach dem letzten
Update wurden weder fachliche Fehler in den geprüften Referenzfällen noch
JavaScript- oder Streamlit-Fehler in den Browserprotokollen festgestellt.

# 11. Bekannte Einschränkungen

- Analysiert werden kontinuierliche SISO-Systeme mit reellen Koeffizienten.
- Unechte beziehungsweise nichtkausale Übertragungsfunktionen werden
  abgewiesen.
- Die Rückführung ist als negative Einheitsrückführung festgelegt.
- Die Stabilitätsreserven beziehen sich auf den offenen Kreis $G_0(s)$.
- Messdaten werden nur als Frequenzgang mit Betrag in dB und Phase in Grad
  verarbeitet.
- Eine Sprungantwort ist nicht Bestandteil der aktuellen App, da der
  bestätigte Kernumfang auf Bode-Diagramm, Reserven, Pole und
  Messdatenvergleich ausgerichtet wurde.
- Die kostenlose Cloud-Bereitstellung unterliegt den jeweils aktuellen
  Ressourcen- und Produktbedingungen des Anbieters.
- Download und Smartphoneansicht sollten unmittelbar vor der Präsentation
  noch einmal manuell geprüft werden.

# 12. Reproduzierbarkeit und Bedienung

## 12.1 Lokaler Start

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Linux oder macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 12.2 Tests ausführen

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## 12.3 Empfohlener Ablauf für die Live-Vorführung

1. Öffentliche URL aufrufen und das stabile Referenzsystem erklären.
2. Bode-Diagramm sowie $\omega_D$, $\varphi_R$, $A_R$ und $s_m$ zeigen.
3. Register „Pole und Stabilität“ öffnen und die geschlossenen Pole erklären.
4. Auf das instabile Preset wechseln und die Warnmeldung demonstrieren.
5. Beispiel-CSV laden und Messpunkte, Fehlerkennwerte und Tabelle zeigen.
6. Eine fehlerhafte CSV oder einen Nullnenner verwenden und die robuste
   Fehlermeldung erläutern.
7. Den Plattformwechsel von Hugging Face zu Streamlit Community Cloud und den
   behobenen Pandas-3-Fehler als Engineering-Review vorstellen.

# 13. Fazit

Das Projektziel wurde erreicht. Die Anwendung verbindet regelungstechnische
Berechnung, interaktive Visualisierung, Messdatenimport und robuste
Fehlerbehandlung in einer öffentlich erreichbaren Web-App. Alle wesentlichen
Mindestanforderungen des LF-10.2-Leitfadens sind umgesetzt.

Besonders relevant für den Entwicklungsprozess waren zwei praktische
Erkenntnisse: Erstens können sich Cloud-Angebote und schulische Anleitungen
zwischen Erstellung und Umsetzung verändern. Der Wechsel von Hugging Face zu
Streamlit Community Cloud war deshalb keine rein technische Vorliebe, sondern
eine notwendige Anpassung an den aktuellen Kosten- und Produktstand. Zweitens
können neue Bibliotheksversionen trotz korrekter Grundlogik unerwartetes
Verhalten erzeugen. Der Pandas-3-Fehler wurde durch einen realistischen
Live-Test entdeckt, ursächlich analysiert, korrigiert und mit einem
Regressionstest dauerhaft abgesichert.

Mit 18 bestandenen automatisierten Tests, den erfolgreichen Live-Tests und der
funktionsfähigen Veröffentlichung besitzt das Projekt einen belastbaren Stand
für Abgabe und Präsentation.

\newpage

# Quellen

Alle nachfolgend genannten Onlinequellen wurden zuletzt am 13. August 2026
abgerufen beziehungsweise geprüft.

1. Fachschule für Elektrotechnik - Leipzig: *Anleitung zum
   Anwendungsprojekt im LF 10.2 - Entwicklung einer technischen
   Web-Applikation mit Python*, Projektleitfaden, 1. Juli 2026.
2. [Projekt-Repository auf GitHub](https://github.com/raizon-hash/bode-stabilitaetsanalysator).
3. [Veröffentlichte Anwendung auf Streamlit Community Cloud](https://bode-stabilitaetsanalysator-agpzycecrpkmmtvdsobuqb.streamlit.app/).
4. Hugging Face: [*Spaces Overview*](https://huggingface.co/docs/hub/spaces-overview).
5. Hugging Face: [*Streamlit Spaces*](https://huggingface.co/docs/hub/spaces-sdks-streamlit).
6. Hugging Face: [*Spaces Changelog - Deprecate Streamlit SDK*](https://huggingface.co/docs/hub/spaces-changelog).
7. Streamlit: [*Streamlit Community Cloud*](https://docs.streamlit.io/deploy/streamlit-community-cloud).
8. Streamlit: [*Deploy your app on Community Cloud*](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).
