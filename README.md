# Mit DXF_Trennsteg_Generator können Gitter erzeugt werden
Mit Scriptmaker können Layouts erzeugt werden

# Scriptmaker V2

Hilfsprogramm zum Erstellen von Uhrenvorlagen
by Michael Mahrt
**Version 2.0 (15.08.2025)**

## Ergänzungen in V2.0

* Export als DXF-Vorlage für Laserbearbeitung
* Unterstützung für Minutenpunkte hinzugefügt

## Beschreibung

Mit diesem Programm lassen sich Layout-Vorlagen für Wortuhren erstellen.
Es bietet eine grafische Oberfläche, in der Buchstaben in ein 11×10-Raster eingetragen werden.
Die erstellten Vorlagen können gespeichert, wieder geladen und in verschiedene Formate exportiert werden.

### Hauptfunktionen

* Rastereditor (11×10) mit Tastatureingabe und Zellenmarkierung
* Prüfung von Wörtern (z. B. „ES“, „IST“, „VIERTEL“, „ZWANZIG“) mit farbiger Anzeige
* Speichern & Laden von Vorlagen als JSON-Dateien
* **Export:**

  * DXF Vorlage → CAD-Datei für Laser oder CNC
  * Icons erstellen → Export als C++ Headerdatei (.h) für Mikrocontroller
  * Layoutscript erstellen → Erzeugt .hpp-Datei für Uhr-Firmware

### Bedienung

1. **Programm starten**
   Python starten mit:

   ```bash
   python uhr_scriptmakerV2.py
   ```

2. **Buchstaben eingeben**

   * Mit der Tastatur Buchstaben ins Raster schreiben
   * Mit der Maus einzelne Felder aktivieren/deaktivieren

3. **Optionen**

   * Checkboxen für ZWANZIG, DREIVIERTEL und Minutenpunkte aktivieren/deaktivieren

4. **Exportieren**

   * **DXF Vorlage:** Speichert eine CAD-Datei für den Laserschnitt
   * **Icons erstellen:** Exportiert ein Headerfile mit Icons (C++/Arduino)
   * **Layoutscript erstellen:** Erzeugt ein C++-Skript für die Uhr

### Hinweis

* Das Programm wurde speziell für Wortuhren im 11×10 Raster entwickelt
* In den Einstellungen können Reihen und Spalten angepasst werden

---

# Trennsteg Generator – Anleitung

Dieses Programm erstellt Vorschauen und DXF-Dateien für Trennstege (z. B. für IKEA-Rahmen).

## Benötigte Programme

* Python 3
* Bibliotheken: `ezdxf`, `matplotlib`
  Installation: `pip install ezdxf matplotlib`
* Tkinter (ist bei Python normalerweise enthalten)

## 1. Programm starten

* Doppelklicke auf die Python-Datei oder starte sie über die Konsole:

  ```bash
  python trennsteg_generatorV1.py
  ```

## 2. Werte eingeben

* **Länge \[mm]:** Breite des Trennstegs
* **Höhe \[mm]:** Höhe des Trennstegs
* **Schlitzbreite \[mm]:** Breite der einzelnen Schlitze

Hinweis: Dezimalzahlen können mit Punkt oder Komma eingegeben werden.

## 3. Position wählen

* Senkrecht (Standard)
* Waagerecht

## 4. Vorschau anzeigen

* Klicke auf "Vorschau"
* Das Programm zeigt ein Diagramm:

  * Außenrahmen (blau)
  * Mittellinie (grün)
  * Schlitze (rot)
  * Abstände werden angezeigt

## 5. DXF speichern

* Klicke auf "DXF speichern"
* Wähle einen Speicherort und Dateinamen
* DXF-Datei enthält:

  * Außenrahmen
  * Mittellinie
  * Schlitze
* Kann in AutoCAD oder LibreCAD geöffnet werden

## 6. Einstellungen ändern

* Klicke auf "Einstellungen"
* Ändere:

  * Schlitzabstand \[mm]
  * Anzahl Schlitze
  * Verschiebung \[mm] (bei waagerechter Position)

Optionen:

* **Speichern** → Speichert die Einstellungen als JSON-Datei
* **Laden** → Lädt gespeicherte Einstellungen
* **Übernehmen** → Werte übernehmen

## 7. Hinweise

* Länge und Höhe müssen > 0 sein

* Schlitzbreite ≥ 0.1 mm und ≤ (Schlitzabstand - 1)

* Anzahl Schlitze: 1 bis 24

* Verschiebung ≤ Schlitzabstand

* Fehlerhafte Eingaben werden mit einer Meldung angezeigt

* Nach Änderungen in den Einstellungen die Vorschau oder DXF neu erstellen

## 8. Programm beenden

* Klicke auf "Beenden"
