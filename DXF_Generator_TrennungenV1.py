# DXF_Generator_TrennungenV1.py
# Trennsteg Generator 
# Erstellt von Michael Mahrt   
# Version 1.1 - 2025-10-31
# Benötigte Bibliotheken: ezdxf, matplotlib, tkinter    
# Beschreibung: Dieses Skript generiert DXF-Dateien für Trennstege mit Schlitzen
#               basierend auf benutzerdefinierten Abmessungen und Einstellungen.
#              Es bietet eine Vorschaufunktion und ermöglicht das Speichern von Einstellungen.
# 
# Lizenz: Dieses Skript ist Open Source und darf frei verwendet und modifiziert werden.
#        Der Autor übernimmt keine Haftung für Schäden, die durch die Nutzung dieses Skripts entstehen.
# ------------------------------------------------------
# Importierte Bibliotheken

import ezdxf
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import Pmw

# -----------------------------

plt.rcParams['toolbar'] = 'None'   # keine Toolbar (keine Save/Configure-Buttons)

# -----------------------------
# Globale Vorgaben für IKEA Rahmen 250x250
# -----------------------------
SCHLITZABSTAND = 16.6666  # mm Abstand Mitte -> Mitte
ANZAHL_SCHLITZE = 12      # Anzahl der Schlitze für Gitter  
VERSCHIEBUNG = 8.3333     # mm für "Waagerecht"-Option
position = "Senkrecht"    # Radiobutton Auswahl
TRENNSTEGHOEHE = 44.8     # mm Höhe der Trennstege
# -----------------------------
# Funktionen
# -----------------------------

def draw_preview(laenge, hoehe, schlitzbreite, erstes_schlitzauslinks):
    schlitzhoehe = round(hoehe / 2 + 1, 2)
    y_unten = round((hoehe - schlitzhoehe) / 2, 2)
    y_oben = round(y_unten + schlitzhoehe, 2)

    fig = plt.figure(num="Vorschau Trennstege", figsize=(laenge/20, hoehe/20))

    # Toolbar & Kopf/Fußzeile ausblenden
    fig.canvas.toolbar_visible = False
    fig.canvas.header_visible = False
    fig.canvas.footer_visible = False

    # Außenrahmen
    plt.plot([0, laenge, laenge, 0, 0],
             [0, 0, hoehe, hoehe, 0], 'b-', linewidth=1.5)

    # Schlitze & Mittellinie
    linie_x_start = 0
    x = erstes_schlitzauslinks
    schlitz_mitten = []
    for i in range(ANZAHL_SCHLITZE):
        plt.plot([linie_x_start, x - schlitzbreite/2], [hoehe/2, hoehe/2], 'g-')
        xs = [x - schlitzbreite/2, x + schlitzbreite/2,
              x + schlitzbreite/2, x - schlitzbreite/2, x - schlitzbreite/2]
        ys = [y_unten, y_unten, y_oben, y_oben, y_unten]
        plt.plot(xs, ys, 'r-', linewidth=2)
        linie_x_start = x + schlitzbreite/2
        schlitz_mitten.append(x)
        x += SCHLITZABSTAND

    plt.plot([linie_x_start, laenge], [hoehe/2, hoehe/2], 'g-')

    plt.gca().set_aspect('equal', adjustable='box')
    plt.xlim(-0.1*laenge, 1.1*laenge)
    plt.ylim(-0.1*hoehe, hoehe)
    plt.axis('off')

    # Länge und Höhe beschriften (2 Nachkommastellen)
    plt.text(laenge/2, hoehe, f"Länge: {laenge:.2f} mm", ha='center', va='bottom', color='blue')
    plt.text(-0.05*laenge, hoehe/2, f"Höhe: {hoehe:.2f} mm", ha='right', va='center', rotation='vertical', color='blue')
    plt.text(erstes_schlitzauslinks, y_oben + 0.05*hoehe, f"Schlitzbreite: {schlitzbreite:.2f} mm", ha='left', va='bottom', color='red')

    # Abstand von links bis zum 1. Schlitz
    x1 = 0
    x2 = schlitz_mitten[0]
    y_pos = y_oben + hoehe
    plt.annotate('', xy=(x1, y_pos), xytext=(x2, y_pos),
                 arrowprops=dict(arrowstyle='<->', color='green'))
    plt.text((x1+x2)/2, y_pos + 0.02*hoehe, f"{(x2-x1):.4f} mm", ha='center', va='bottom', color='green')

    # Abstand vorletztes Schlitzpaar
    if len(schlitz_mitten) >= 2:
        x1 = schlitz_mitten[-2]
        x2 = schlitz_mitten[-1]
        y_pos = y_oben + hoehe
        plt.annotate('', xy=(x1, y_pos), xytext=(x2, y_pos),
                     arrowprops=dict(arrowstyle='<->', color='blue'))
        plt.text((x1+x2)/2, y_pos + 0.02*hoehe, f"{(x2-x1):.4f} mm",
                 ha='center', va='bottom', color='blue')

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    plt.show()




def create_dxf(laenge, hoehe, schlitzbreite, erstes_schlitzauslinks, dateipfad):
    schlitzhoehe = round(hoehe / 2 , 2)
    y_unten = round((hoehe - schlitzhoehe) / 2, 2)
    y_oben = round(y_unten + schlitzhoehe, 2)

    doc = ezdxf.new(dxfversion='AC1009', units=3)
    msp = doc.modelspace()

    msp.add_lwpolyline([(0, 0), (laenge, 0), (laenge, hoehe),
                        (0, hoehe), (0, 0)], close=True, dxfattribs={"layer": "Kontur"})

    x = erstes_schlitzauslinks
    linie_x_start = 0
    for i in range(ANZAHL_SCHLITZE):
        msp.add_line((linie_x_start, hoehe/2),
                     (x - schlitzbreite/2, hoehe/2),
                     dxfattribs={"layer": "Mittellinie"})
        msp.add_lwpolyline([
            (x - schlitzbreite/2, y_unten),
            (x + schlitzbreite/2, y_unten),
            (x + schlitzbreite/2, y_oben),
            (x - schlitzbreite/2, y_oben),
            (x - schlitzbreite/2, y_unten)
        ], close=True, dxfattribs={"layer": "Schlitze"})
        linie_x_start = x + schlitzbreite/2
        x += SCHLITZABSTAND

    msp.add_line((linie_x_start, hoehe/2),
                 (laenge, hoehe/2), dxfattribs={"layer": "Mittellinie"})

    doc.saveas(dateipfad)
    messagebox.showinfo("Erfolg", f"DXF gespeichert unter:\n{dateipfad}")


def start_preview():
    try:
        laenge = float(entry_laenge.get().replace(',', '.'))
        hoehe = float(entry_hoehe.get().replace(',', '.'))*2
        schlitzbreite = float(entry_schlitz.get().replace(',', '.'))

        # --- Prüfungen ---
        if not check_values(schlitzbreite, ANZAHL_SCHLITZE, VERSCHIEBUNG, SCHLITZABSTAND):
            return
        # ------------------

        if position == "Waagerecht":
            erstes_schlitzauslinks = round(
                (laenge - (ANZAHL_SCHLITZE-1)*SCHLITZABSTAND)/2 + VERSCHIEBUNG, 4)
        else:
            erstes_schlitzauslinks = round(
                (laenge - (ANZAHL_SCHLITZE-1)*SCHLITZABSTAND)/2, 4)

        draw_preview(laenge, hoehe, schlitzbreite, erstes_schlitzauslinks)
    except ValueError:
        messagebox.showerror("Fehler", "Bitte gültige Zahlen eingeben.")


def start_save():
    try:
        laenge = float(entry_laenge.get().replace(',', '.'))
        hoehe = float(entry_hoehe.get().replace(',', '.'))*2
        schlitzbreite = float(entry_schlitz.get().replace(',', '.'))

        # --- Prüfungen Eingabewerte ---
        if laenge <= 0:
            messagebox.showerror("Fehler", "Länge muss größer als 0 sein.")
            return
        if hoehe <= 0:
            messagebox.showerror("Fehler", "Höhe muss größer als 0 sein.")
            return
        if schlitzbreite < 0.1:
            messagebox.showerror("Fehler", "Schlitzbreite darf nicht kleiner als 0.1 mm sein.")
            return
        # ------------------------------

        # --- Prüfungen globale Werte ---
        if not check_values(schlitzbreite, ANZAHL_SCHLITZE, VERSCHIEBUNG, SCHLITZABSTAND):
            return
        # -------------------------------

        if position == "Waagerecht":
            erstes_schlitzauslinks = round(
                (laenge - (ANZAHL_SCHLITZE-1)*SCHLITZABSTAND)/2 + VERSCHIEBUNG, 4)
        else:
            erstes_schlitzauslinks = round(
                (laenge - (ANZAHL_SCHLITZE-1)*SCHLITZABSTAND)/2, 4)

        dateipfad = filedialog.asksaveasfilename(
            defaultextension=".dxf", filetypes=[("DXF-Dateien", "*.dxf")])
        if dateipfad:
            create_dxf(laenge, hoehe, schlitzbreite, erstes_schlitzauslinks, dateipfad)

    except ValueError:
        messagebox.showerror("Fehler", "Bitte gültige Zahlen eingeben.")


 # Überprüfung der Eingabewerte
def check_values(schlitzbreite, anzahl_schlitze, verschiebung, schlitzabstand):
    if schlitzbreite < 0.1:
        messagebox.showerror("Fehler", "Die Schlitzbreite darf nicht kleiner als 0,1 mm sein.")
        return False
    if schlitzbreite > schlitzabstand - 1:
        messagebox.showerror("Fehler", f"Schlitzbreite darf maximal {schlitzabstand - 1:.2f} mm betragen.")
        return False
    if anzahl_schlitze < 1 or anzahl_schlitze > 24:
        messagebox.showerror("Fehler", "Die Anzahl der Schlitze muss zwischen 1 und 24 liegen.")
        return False
    if verschiebung > schlitzabstand:
        messagebox.showerror("Fehler", f"Die Verschiebung darf maximal {schlitzabstand:.2f} mm betragen.")
        return False
    return True

# -----------------------------
# Einstellungsfenster
# -----------------------------
def open_settings():
    def save_settings():
        try:
            dateipfad = filedialog.asksaveasfilename(defaultextension=".json",
                                                     filetypes=[("JSON-Dateien", "*.json")],
                                                     title="Einstellungen speichern")
            if dateipfad:
                data = {
                    "SCHLITZABSTAND": float(entry_schlitzabstand.get().replace(',', '.')),
                    "ANZAHL_SCHLITZE": int(entry_anzahl.get()),
                    "VERSCHIEBUNG": float(entry_verschiebung.get().replace(',', '.'))
                }
                with open(dateipfad, "w") as f:
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Erfolg", f"Einstellungen gespeichert:\n{dateipfad}")
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlen eingeben!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern:\n{e}")

    def load_settings():
        global SCHLITZABSTAND, ANZAHL_SCHLITZE, VERSCHIEBUNG

        def _validate_loaded_data(data_dict):
            # 1) Struktur prüfen
            if not isinstance(data_dict, dict):
                return False, "Die Datei enthält kein JSON-Objekt (Dictionary).", None

            # 2) Pflichtschlüssel prüfen
            required = ["SCHLITZABSTAND", "ANZAHL_SCHLITZE", "VERSCHIEBUNG"]
            missing = [k for k in required if k not in data_dict]
            if missing:
                return False, f"Fehlende Schlüssel: {', '.join(missing)}", None

            # 3) Typen / Numerik prüfen (Komma als Dezimaltrenner tolerieren)
            try:
                sa = float(str(data_dict["SCHLITZABSTAND"]).replace(",", "."))
                anz = int(data_dict["ANZAHL_SCHLITZE"])
                ver = float(str(data_dict["VERSCHIEBUNG"]).replace(",", "."))
            except (TypeError, ValueError):
                return False, "Werte müssen numerisch sein (Zahlen).", None

            # 4) Wertebereiche validieren (an deine Logik angelehnt)
            if sa <= 0:
                return False, "SCHLITZABSTAND muss größer als 0 sein.", None
            if not (1 <= anz <= 24):
                return False, "ANZAHL_SCHLITZE muss zwischen 1 und 24 liegen.", None
            if ver < 0:
                return False, "VERSCHIEBUNG darf nicht negativ sein.", None
            if ver > sa:
                return False, "VERSCHIEBUNG darf den SCHLITZABSTAND nicht überschreiten.", None

            # Alles ok – normalisierte Werte zurückgeben
            return True, "", {"SCHLITZABSTAND": sa, "ANZAHL_SCHLITZE": anz, "VERSCHIEBUNG": ver}

        try:
            dateipfad = filedialog.askopenfilename(
                defaultextension=".json",
                filetypes=[("JSON-Dateien", "*.json")],
                title="Einstellungen laden"
            )
            if not dateipfad:
                return  # Abbrechen durch Nutzer

            # Datei lesen (mit Encoding) und leere Datei abfangen
            try:
                with open(dateipfad, "r", encoding="utf-8") as f:
                    raw = f.read()
            except (OSError, PermissionError, UnicodeDecodeError) as e:
                messagebox.showerror("Fehler", f"Datei konnte nicht gelesen werden:\n{e}")
                return

            if not raw.strip():
                messagebox.showerror("Fehler", "Die ausgewählte Datei ist leer.")
                return

            # JSON parsen
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                messagebox.showerror("Fehler", f"Ungültige JSON-Struktur:\n{e}")
                return

            # Inhalt validieren
            ok, msg, values = _validate_loaded_data(data)
            if not ok:
                messagebox.showerror("Fehler", f"Einstellungsdatei unvollständig/ungültig:\n{msg}")
                return

            # Felder befüllen – schön formatiert
            entry_schlitzabstand.delete(0, tk.END)
            entry_schlitzabstand.insert(0, f"{values['SCHLITZABSTAND']:.4f}")

            entry_anzahl.delete(0, tk.END)
            entry_anzahl.insert(0, str(values['ANZAHL_SCHLITZE']))

            entry_verschiebung.delete(0, tk.END)
            entry_verschiebung.insert(0, f"{values['VERSCHIEBUNG']:.4f}")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden:\n{e}")
        finally:
            # Fenster wieder nach vorne holen
            settings.lift()
            settings.focus_force()



    def apply_settings():
        global SCHLITZABSTAND, ANZAHL_SCHLITZE, VERSCHIEBUNG
        SCHLITZABSTAND = float(entry_schlitzabstand.get().replace(',', '.'))
        ANZAHL_SCHLITZE = int(entry_anzahl.get())
        VERSCHIEBUNG = float(entry_verschiebung.get().replace(',', '.'))
        label_vorgaben.config(
            text=f"SCHLITZABSTAND = {SCHLITZABSTAND} mm | "
                 f"ANZAHL_SCHLITZE = {ANZAHL_SCHLITZE} | "
                 f"VERSCHIEBUNG = {VERSCHIEBUNG} mm"
        )
        settings.destroy()

    settings = tk.Toplevel(root)
    settings.title("Einstellungen")

    tk.Label(settings, text="Schlitzabstand [mm]").grid(row=0, column=0, sticky="e")
    entry_schlitzabstand = tk.Entry(settings)
    entry_schlitzabstand.grid(row=0, column=1)
    entry_schlitzabstand.insert(0, str(SCHLITZABSTAND))

    tk.Label(settings, text="Anzahl Schlitze").grid(row=1, column=0, sticky="e")
    entry_anzahl = tk.Entry(settings)
    entry_anzahl.grid(row=1, column=1)
    entry_anzahl.insert(0, str(ANZAHL_SCHLITZE))

    tk.Label(settings, text="Verschiebung [mm]").grid(row=2, column=0, sticky="e")
    entry_verschiebung = tk.Entry(settings)
    entry_verschiebung.grid(row=2, column=1)
    entry_verschiebung.insert(0, str(VERSCHIEBUNG))

    tk.Button(settings, text="Speichern", command=save_settings).grid(row=3, column=0, pady=5)
    tk.Button(settings, text="Laden", command=load_settings).grid(row=3, column=1, pady=5)
    tk.Button(settings, text="Übernehmen", command=apply_settings).grid(row=3, column=2, columnspan=2, pady=5)


# -----------------------------
# Haupt-GUI
# -----------------------------
root = tk.Tk()
root.title("Trennsteg Generator by Michael Mahrt")
root.geometry("460x200")

Pmw.initialise(root)
# Überschrift
tk.Label(root, text="Trennsteg Generator", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

# Eingabefelder
tk.Label(root, text="Länge [mm]").grid(row=1, column=0, sticky="e")
entry_laenge = tk.Entry(root)
entry_laenge.grid(row=1, column=1)
entry_laenge.insert(0, "239.50")
Pmw.Balloon(root).bind(entry_laenge, "Hier die Länge des Trennstegs in mm eingeben")

tk.Label(root, text="Höhe [mm]").grid(row=2, column=0, sticky="e")
entry_hoehe = tk.Entry(root)
entry_hoehe.grid(row=2, column=1)
entry_hoehe.insert(0, "44.8")
Pmw.Balloon(root).bind(entry_hoehe, "Hier die Höhe des Trennstegs in mm eingeben")

tk.Label(root, text="Schlitzbreite [mm]").grid(row=3, column=0, sticky="e")
entry_schlitz = tk.Entry(root)
entry_schlitz.grid(row=3, column=1)
entry_schlitz.insert(0, "0.3")
Pmw.Balloon(root).bind(entry_schlitz, "Hier die Breite der Schlitze in mm eingeben")

# Radiobuttons
position_var = tk.StringVar(value="Senkrecht")
def update_position():
    global position
    position = position_var.get()
r1=tk.Radiobutton(root, text="Senkrecht   ", variable=position_var, value="Senkrecht", command=update_position)
r1.grid(row=1, column=2)
r2=tk.Radiobutton(root, text="Waagerecht", variable=position_var, value="Waagerecht", command=update_position)
r2.grid(row=2, column=2)

Pmw.Balloon(root).bind(r1, "Bei Wahl Senkrecht werden die Schlitze mittig angeordnet.")
Pmw.Balloon(root).bind(r2, "Bei Wahl Waagerecht werden die Schlitze verschoben angeordnet.")

# Vorgaben-Label
label_vorgaben = tk.Label(root,
    text=f"SCHLITZABSTAND = {SCHLITZABSTAND} mm | ANZAHL_SCHLITZE = {ANZAHL_SCHLITZE} | VERSCHIEBUNG = {VERSCHIEBUNG} mm",
    font=("Arial", 8))
label_vorgaben.grid(row=4, column=0, columnspan=4, pady=5)

# Buttons in Reihe
tk.Button(root, text="Vorschau", command=start_preview).grid(row=5, column=0, pady=10)
tk.Button(root, text="DXF speichern", command=start_save).grid(row=5, column=1, pady=10)
tk.Button(root, text="Einstellungen", command=open_settings).grid(row=5, column=2, pady=10)
tk.Button(root, text="Beenden", command=root.destroy).grid(row=5, column=3, pady=10)

def verdopple_hoehe(event=None):
    try:
        hoehe = float(entry_hoehe.get())
        hoehe = hoehe * 2
        entry_hoehe.delete(0, tk.END)
        entry_hoehe.insert(0, f"{hoehe:.2f}")
    except ValueError:
        pass  # Ignoriert ungültige Eingaben

# Event-Bindung: wenn Enter gedrückt wird
# entry_hoehe.bind("<FocusOut>", verdopple_hoehe)

root.mainloop()
