## Hilfsprogramm zum Erstellen von Uhrenvorlagen
## by Michael Mahrt
## V2.1  15.08.2025
## V3 (Logik-Überarbeitung):
## - Wortzonen: Stundenwörter (1-12, EIN, EINS, UHR) stehen NACH HALB,
##   alle anderen Wörter stehen VOR HALB. Leserichtung: links oben -> rechts unten
## - Jedes Wort hat genau ein festes Vorkommen, die Zone entscheidet welches
## - Vergleich zellweise (keine Treffer über leere Zellen mehr)
## - Script-Ausgabe pro Wortindex statt pro Wortstring (keine doppelten case-Labels)
## - Vorlage speichert die Minutenanzeige, Rasterdimensionen werden geprüft
## - Ergänzt: DXF Vorlage für Laser, Unterstützung für Minutenpunkte
## V3.1 Anpassung an V4.2
## .hpp angepasst
## TODO:
## !! Teilstring-Treffer möglich (z.B. IST in ChrISTtian) - Wortmaske fehlt noch


# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox
import json

import ezdxf
from ezdxf.enums import TextEntityAlignment

COLS = 11
ROWS = 10
CELL_SIZE = 30
LABEL_MARGIN_LEFT = 20  # Platz für Zeilenbeschriftung links
LABEL_MARGIN_TOP = 20   # Platz für Spaltenbeschriftung oben
RAHMENGROSS = 250       # Rahmen in mm für DXF Export
DEBUG = False           # True = Debug-Ausgaben

# ---------- Wortliste ----------
# Index bestimmt Zone und Ausgabe. Gleiche Texte können mehrfach vorkommen
# (FÜNF, ZEHN, DREI), die Zone unterscheidet sie.
WORDS = [
    "UHR", "EINS", "ZWEI", "DREI", "VIER", "FÜNF", "SECHS", "SIEBEN", "ACHT", "NEUN", "ZEHN",
    "ELF", "ZWÖLF", "EIN",                          # 0-13  Stundenwörter, nach HALB
    "ES", "IST",                                    # 14-15 vor HALB
    "FÜNF", "ZEHN",                                 # 16-17 Minutenwörter, vor HALB
    "HALB",                                         # 18    Trennwort
    "ZWANZIG", "VOR", "NACH", "DREI", "VIERTEL",    # 19-23 vor HALB
]
# h = nach HALB (Stunde/UHR), m = vor HALB, sep = Trennwort
ZONE = ["h"] * 14 + ["m", "m", "m", "m", "sep", "m", "m", "m", "m", "m"]

HALB_IDX = 18
ES_IDX = 14
IST_IDX = 15
ZWANZIG_IDX = 19
DREI_VIERTEL_IDX = 22
VIERTEL_IDX = 23

# Name des FrontWord-Enums je Wortindex (None = Sonderausgabe)
FRONT_ENUM = [
    "uhr", "eins", "hour_2", "hour_3", "hour_4", "hour_5", "hour_6", "hour_7",
    "hour_8", "hour_9", "hour_10", "hour_11", "hour_12", "hour_1",
    None, None,                       # ES, IST -> case es_ist
    "min_5", "min_10", "halb", "min_20", "vor", "nach",
    None,                             # DREI aus DREIVIERTEL -> case dreiviertel
    "viertel",
]
# Zusätzliche case-Labels (wie bisher für vor/nach)
EXTRA_CASE = {"vor": "v_vor", "nach": "v_nach"}


def zone_name(i):
    return {"h": "Stunde", "m": "Minute", "sep": "Trennwort"}[ZONE[i]]


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class GridApp(tk.Tk):  # Hauptklasse für die Anwendung

    def __init__(self):
        super().__init__()

        self.title("Scriptmaker by MAHTec (C) M.Mahrt V3.0")
        self.configure(bg="#f0f0f0")

        self.cells = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.selected = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.placed = {}      # Wortindex -> (Reihe, Startspalte, Endspalte), Anzeige-Koordinaten
        self.ambiguous = []   # Wortindizes mit mehreren gültigen Vorkommen

        self.words = WORDS

        # Main frame für Wörter und Raster nebeneinander
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Wortliste links
        self.word_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.word_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.word_labels = []
        for i, w in enumerate(self.words):
            lbl = tk.Label(self.word_frame, text=w, font=("Helvetica", 12), anchor="w", width=15, bg="#f0f0f0")
            r = i % 12
            c = i // 12
            lbl.grid(row=r, column=c, sticky="w", pady=1)
            self.word_labels.append(lbl)

        self.varzwanzig = tk.IntVar()
        self.varviertel = tk.IntVar()
        self.minanzeige = tk.IntVar()

        cb1 = tk.Checkbutton(self.word_frame, text="Uhr hat KEINE Anzeige ZWANZIG",
                             variable=self.varzwanzig, command=self.check_words)
        cb2 = tk.Checkbutton(self.word_frame, text="Uhr hat KEINE Anzeige DREIVIERTEL",
                             variable=self.varviertel, command=self.check_words)
        cb3 = tk.Checkbutton(self.word_frame, text="Uhr hat KEINE Minutenanzeige",
                             variable=self.minanzeige, command=self.check_words)

        max_rows = 12
        max_cols = (len(self.words) + max_rows - 1) // max_rows

        cb1.grid(row=max_rows, column=0, columnspan=max_cols, sticky="w", padx=7, pady=5)
        cb2.grid(row=max_rows + 1, column=0, columnspan=max_cols, sticky="w", padx=7, pady=1)
        cb3.grid(row=max_rows + 2, column=0, columnspan=max_cols, sticky="w", padx=7, pady=1)

        # Raster rechts
        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.LEFT, fill=tk.NONE)

        tk.Label(right_frame, text=f"Raster {COLS}×{ROWS}",
                 font=("Helvetica", 14, "bold"), bg="#f0f0f0").pack(pady=(10, 0))

        self.canvas = tk.Canvas(right_frame, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE,
                                bg="white", highlightthickness=2, highlightbackground="#999999")
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)

        self.rectangles, self.text_items = {}, {}
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = c * CELL_SIZE, r * CELL_SIZE
                rect = self.canvas.create_rectangle(x0, y0, x0 + CELL_SIZE, y0 + CELL_SIZE,
                                                    outline="#cccccc", fill="white")
                text = self.canvas.create_text(x0 + CELL_SIZE / 2, y0 + CELL_SIZE / 2,
                                               text="", font=("Helvetica", 14))
                self.rectangles[(r, c)], self.text_items[(r, c)] = rect, text

        self.canvas.bind("<Button-1>", self.click_cell)
        self.bind("<Key>", self.key_press)
        self.current_cell = (0, 0)
        self.highlight_current_cell()
        self.focus_set()

        # Buttons unten
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(side=tk.BOTTOM, pady=10)

        tk.Button(button_frame, text="DXF Vorlage", width=15, command=self.save_letter_grid).grid(row=0, column=0, padx=4)
        tk.Button(button_frame, text="Speichern Vorlage", width=15, command=self.save_template).grid(row=0, column=1, padx=4)
        tk.Button(button_frame, text="Vorlage laden", width=13, command=self.load_template).grid(row=0, column=2, padx=4)
        tk.Button(button_frame, text="Lösche alles", width=13, command=self.clear_grid).grid(row=0, column=3, padx=4)
        tk.Button(button_frame, text="Exit", width=10, command=self.quit).grid(row=0, column=4, padx=4)
        tk.Button(button_frame, text="Einstellungen", width=10, command=self.Einstellungen).grid(row=0, column=5, padx=4)

        btn_frame = tk.Frame(right_frame, bg="#f0f0f0")
        btn_frame.pack(side=tk.TOP, pady=(0, 10))

        self.script_button = tk.Button(btn_frame, text="Layoutscript erstellen", command=self.generate_script)
        self.script_button.pack(side="left", padx=4)

        self.export_button = tk.Button(btn_frame, text="icons erstellen", command=self.export_txt)
        self.export_button.pack(side="left", padx=4)

        self.check_words()

    # ---------- Eingabe ----------
    def click_cell(self, event):
        col, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        debug_print(f"Clicked cell: ({row}, {col})")
        if 0 <= row < ROWS and 0 <= col < COLS:
            self.current_cell = (row, col)
            if self.cells[row][col]:
                self.selected[row][col] = not self.selected[row][col]
            else:
                self.selected[row][col] = False
            self.refresh_all()

    def key_press(self, event):
        if self.current_cell is None:
            return
        r, c = self.current_cell
        if event.keysym in ("BackSpace", "Delete", "space"):
            self.cells[r][c] = ""
            self.selected[r][c] = False
            self.move_to_next_cell()
        else:
            ch = event.char.upper()
            if ch.isalnum() and len(ch) == 1:
                self.cells[r][c] = ch
                self.selected[r][c] = False
                self.move_to_next_cell()
        self.refresh_all()
        self.check_words()

    def move_to_next_cell(self):
        r, c = self.current_cell
        c += 1
        if c >= len(self.cells[0]):
            c = 0
            r += 1
            if r >= len(self.cells):
                r = 0
        self.current_cell = (r, c)

    # ---------- Prüflogik ----------
    def find_occurrences(self, word):
        """Alle Vorkommen von word als (Reihe, Startspalte, Endspalte).
        Zellweise Prüfung: leere Zellen können keine Buchstaben verbinden."""
        rows, cols = len(self.cells), len(self.cells[0])
        length = len(word)
        result = []
        for r in range(rows):
            for c in range(cols - length + 1):
                if all(self.cells[r][c + k].upper() == word[k].upper() for k in range(length)):
                    result.append((r, c, c + length - 1))
        return result

    def check_words(self):
        occ = [self.find_occurrences(w) for w in WORDS]

        self.placed = {}
        self.ambiguous = []

        # Alle Treffer aller Wörter als (Text, Reihe, Start, Ende), für die Überlappungsregel
        all_hits = []
        for idx, w in enumerate(WORDS):
            for (r, s, e) in occ[idx]:
                all_hits.append((w, r, s, e))

        def classify(word, r, s, e):
            """None = Treffer verwerfen (Teil eines längeren Wortes, das sich teilweise überlappt)
            'sub' = steckt vollständig in einem längeren Wort (z.B. EIN in EINS)
            'ok' = eigenständiger Treffer"""
            longer = [(s2, e2) for (w2, r2, s2, e2) in all_hits
                      if len(w2) > len(word) and r2 == r]
            if any(s2 <= s and e <= e2 for s2, e2 in longer):
                return "sub"                      # vollständig im längeren Wort enthalten
            # Überlappung um mindestens 2 Buchstaben (z.B. EI in DREINEUN) = Zufallstreffer.
            # 1 gemeinsamer Buchstabe (ELF/FÜNF in ELFÜNF) ist erlaubt.
            if any(min(e, e2) - max(s, s2) + 1 >= 2 for s2, e2 in longer):
                return None
            return "ok"

        # Trennwort HALB muss genau einmal vorkommen, sonst ist die Zonenteilung unklar
        halb = [o for o in occ[HALB_IDX] if classify(WORDS[HALB_IDX], *o)]
        halb_pos = (halb[0][0], halb[0][1]) if len(halb) == 1 else None
        if halb_pos is not None:
            self.placed[HALB_IDX] = halb[0]

        for i, zone in enumerate(ZONE):
            if zone == "sep" or halb_pos is None:
                continue
            hits = []
            for o in occ[i]:
                st = classify(WORDS[i], *o)
                if st is None:
                    continue
                pos = (o[0], o[1])
                in_zone = pos < halb_pos if zone == "m" else pos > halb_pos
                if in_zone:
                    hits.append((st, o))
            # eigenständige Treffer zuerst, Teilwörter (EIN in EINS) nur als Ersatz
            real = [o for st, o in hits if st == "ok"]
            sub = [o for st, o in hits if st == "sub"]
            if real or sub:
                self.placed[i] = (real or sub)[0]
            # Mehrfach nur bei eigenständigen Treffern zählen
            if len(real) > 1:
                self.ambiguous.append(i)

        debug_print("placed:", self.placed, "ambiguous:", self.ambiguous)

        # Farben
        for i in range(len(WORDS)):
            if i == ZWANZIG_IDX and self.varzwanzig.get():
                fg = "blue"
            elif i == DREI_VIERTEL_IDX and self.varviertel.get():
                fg = "blue"
            elif i in self.ambiguous and ZONE[i] == "h":
                fg = "#FF8C00"  # orange: Stundenwort mehrfach nach HALB vorhanden
            elif i in self.placed:
                fg = "green"
            else:
                fg = "red"
            self.word_labels[i].config(fg=fg)

    def required_indices(self):
        """Wörter, die für das aktuelle Script vorhanden sein müssen."""
        req = []
        for i in range(len(WORDS)):
            if i == ZWANZIG_IDX and self.varzwanzig.get():
                continue
            if i == DREI_VIERTEL_IDX and self.varviertel.get():
                continue
            req.append(i)
        return req

    # ---------- Anzeige ----------
    def refresh_cell(self, r, c):
        if (r, c) == self.current_cell:
            bg = "#add8e6"
        else:
            bg = "#ffcc66" if self.selected[r][c] else ("#aaffaa" if self.cells[r][c] else "white")
        self.canvas.itemconfig(self.rectangles[(r, c)], fill=bg)
        self.canvas.itemconfig(self.text_items[(r, c)], text=self.cells[r][c])

    def refresh_all(self):
        for r in range(ROWS):
            for c in range(COLS):
                self.refresh_cell(r, c)
        self.highlight_current_cell()

    def highlight_current_cell(self):
        for rect in self.rectangles.values():
            self.canvas.itemconfig(rect, outline="#cccccc")
        r, c = self.current_cell
        self.canvas.itemconfig(self.rectangles[(r, c)], outline="blue")

    # ---------- Ausgabe Icons ----------
    def export_txt(self):
        lines = []
        bin_strs = []
        letters_list = []

        for r in range(ROWS):
            bits = ''.join('1' if self.selected[r][col] else '0' for col in reversed(range(COLS)))
            # Nur Buchstaben anzeigen, deren Bit im Binärstring 1 ist; sonst "." (wie bei den fertigen Symbolen)
            letters = ' '.join(
                (self.cells[r][col] or '0') if self.selected[r][col] else '.'
                for col in range(COLS)
            )
            bin_strs.append(bits)
            letters_list.append(letters)

        for r in range(ROWS):
            if r == 0:
                bin_part = f'{{0b{bin_strs[r]}, '
            elif r == ROWS - 1:
                bin_part = f' 0b{bin_strs[r]}}},'
            else:
                bin_part = f' 0b{bin_strs[r]}, '

            total_bin_width = len(f'{{0b{"0" * COLS},')
            spaces_needed = max(total_bin_width - len(bin_part), 0)

            line = bin_part + (" " * spaces_needed) + " " + f"//           {letters_list[r]}//"
            lines.append(line)

        header = """#pragma once

#define SYMBOL_11X10_ROWS 10
#define SYMBOL_11X10_COLS 11

const uint16_t symbol_11x10[][11] PROGMEM = {
"""
        Hstart = """    {0b00011111000,  // 0  WLAN100  0: . . . 0 0 0 0 0 . . . : 10
     0b01111111110,  // 1          21: . 0 0 0 0 0 0 0 0 0 . : 11
     0b11100000111,  // 2          22: 0 0 0 . . . . . 0 0 0 : 32
     0b10011111001,  // 3          43: 0 . . 0 0 0 0 0 . . 0 : 33
     0b00111111100,  // 4          44: . . 0 0 0 0 0 0 0 . . : 54
     0b00100000100,  // 5          65: . . 0 . . . . . 0 . . : 55
     0b00000100000,  // 6          66: . . . . . 0 . . . . . : 76
     0b00001110000,  // 7          87: . . . . 0 0 0 . . . . : 77
     0b00000100000,  // 8          88: . . . . . 0 . . . . . : 98
     0b00000000000}, // 9         109: . . . . . . . . . . . : 99

"""
        Hend = """
    {0b00110001100,  // 0  HEART    0: . . 0 0 . . . 0 0 . . : 10
     0b01111011110,  // 1          21: . 0 0 0 0 . 0 0 0 0 . : 11
     0b11111111111,  // 2          22: 0 0 0 0 0 0 0 0 0 0 0 : 32
     0b11111111111,  // 3          43: 0 0 0 0 0 0 0 0 0 0 0 : 33
     0b11111111111,  // 4          44: 0 0 0 0 0 0 0 0 0 0 0 : 54
     0b01111111110,  // 5          65: . 0 0 0 0 0 0 0 0 0 . : 55
     0b00111111100,  // 6          66: . . 0 0 0 0 0 0 0 . . : 76
     0b00011111000,  // 7          87: . . . 0 0 0 0 0 . . . : 77
     0b00001110000,  // 8          88: . . . . 0 0 0 . . . . : 98
     0b00000100000}, // 9         109: . . . . . 0 . . . . . : 99

    {0b00011111000,  // 0  SMILEY   0: . . . 0 0 0 0 0 . . . : 10
     0b00111111100,  // 1          21: . . 0 0 0 0 0 0 0 . . : 11
     0b01101110110,  // 2          22: . 0 0 . 0 0 0 . 0 0 . : 32
     0b11111111111,  // 3          43: 0 0 0 0 0 0 0 0 0 0 0 : 33
     0b11111111111,  // 4          44: 0 0 0 0 0 0 0 0 0 0 0 : 54
     0b10111111101,  // 5          65: 0 . 0 0 0 0 0 0 0 . 0 : 55
     0b11001110011,  // 6          66: 0 0 . . 0 0 0 . . 0 0 : 76
     0b01110001110,  // 7          87: . 0 0 0 . . . 0 0 0 . : 77
     0b00111111100,  // 8          88: . . 0 0 0 0 0 0 0 . . : 98
     0b00011111000}, // 9         109: . . . 0 0 0 0 0 . . . : 99

    {0b00000000000,  // 0  NOTE     0: . . . . . . . . . . . : 10
     0b00000011111,  // 1          21: . . . . . . 0 0 0 0 0 : 11
     0b00011111111,  // 2          22: . . . . 0 0 0 0 0 0 0 : 32
     0b00110000011,  // 3          43: . . 0 0 . . . . . 0 0 : 33
     0b00110000011,  // 4          44: . . 0 0 . . . . . 0 0 : 54
     0b00110000011,  // 5          65: . . 0 0 . . . . . 0 0 : 55
     0b01110001110,  // 6          66: . 0 0 0 . . . 0 0 0 . : 76
     0b11111011111,  // 7          87: 0 0 0 0 0 . 0 0 0 0 0 : 77
     0b01110001110,  // 8          88: . 0 0 0 . . . 0 0 0 . : 98
     0b00000000000}, // 9         109: . . . . . . . . . . . : 99

    {0b00000100000,  // 0 SNOW      0: . . . . . 0 . . . . . : 10
     0b00000100000,  // 1          21: . . . . . 0 . . . . . : 11
     0b00110101100,  // 2          22: . . 0 0 . 0 . 0 0 . . : 32
     0b00110101100,  // 3          43: . . 0 0 . 0 . 0 0 . . : 33
     0b00001110000,  // 4          44: . . . . 0 0 0 . . . . : 54
     0b01111111110,  // 5          65: . 0 0 0 0 0 0 0 0 0 . : 55
     0b00001110000,  // 6          66: . . . . 0 0 0 . . . . : 76
     0b00110101100,  // 7          87: . . 0 0 . 0 . 0 0 . . : 77
     0b00110101100,  // 8          88: . . 0 0 . 0 . 0 0 . . : 98
     0b00000100000}, // 9         109: . . . . . 0 . . . . . : 99

    {0b00000000000,  // 0  MAIL     0: . . . . . . . . . . . : 10
     0b11111111111,  // 1          21: 0 0 0 0 0 0 0 0 0 0 0 : 11
     0b11000000011,  // 2          22: 0 0 . . . . . . . 0 0 : 32
     0b10100000101,  // 3          43: 0 . 0 . . . . . 0 . 0 : 33
     0b10011111001,  // 4          44: 0 . . 0 0 0 0 0 . . 0 : 54
     0b10000100001,  // 5          65: 0 . . . . 0 . . . . 0 : 55
     0b10000000001,  // 6          66: 0 . . . . . . . . . 0 : 76
     0b10000000001,  // 7          87: 0 . . . . . . . . . 0 : 77
     0b11111111111,  // 8          88: 0 0 0 0 0 0 0 0 0 0 0 : 98
     0b00000000000}, // 9         109: . . . . . . . . . . . : 99

    {0b00000100000,  // 0  BELL    0: . . . . . 0 . . . . . : 10
     0b00001110000,  // 1          21: . . . . 0 0 0 . . . . : 11
     0b00010001000,  // 2          22: . . . 0 . . . 0 . . . : 32
     0b00100000100,  // 3          43: . . 0 . . . . . 0 . . : 33
     0b00100000100,  // 4          44: . . 0 . . . . . 0 . . : 54
     0b01100000110,  // 5          65: . 0 0 . . . . . 0 0 . : 55
     0b01100000011,  // 6          66: 0 0 . . . . . . . 0 0 : 76
     0b01111111110,  // 7          87: . 0 0 0 0 0 0 0 0 0 . : 77
     0b00001110000,  // 8          88: . . . . 0 0 0 . . . . : 98
     0b00000100000}, // 9         109: . . . . . 0 . . . . . : 99

    {0b00001110000,  // 0  STOP    0: . . . . 0 0 0 . . . . : 10
     0b00111111100,  // 1          21: . . 0 0 0 0 0 0 0 . . : 11
     0b01110001110,  // 2          22: . 0 0 0 . . . 0 0 0 . : 32
     0b11001010011,  // 3          43: 0 0 . . 0 . 0 . . 0 0 : 33
     0b11000100011,  // 4          44: 0 0 . . . 0 . . . 0 0 : 54
     0b11001010011,  // 5          65: 0 0 . . 0 . 0 . . 0 0 : 55
     0b11010001011,  // 6          66: 0 0 . 0 . . . 0 . 0 0 : 76
     0b01100000110,  // 7          87: . 0 0 . . . . . 0 0 . : 77
     0b00111111100,  // 8          88: . . 0 0 0 0 0 0 0 . . : 98
     0b00001110000}, // 9         109: . . . . 0 0 0 . . . . : 99

"""
        # STBY (11x10) = berechnetes Symbol, wird beim Schreiben zwischen Hend und Hend2 eingefügt
        Hend2 = """};

#define SYMBOL_8X8_ROWS 8
#define SYMBOL_8X8_COLS 8

const uint16_t symbol_8x8[][8] PROGMEM = {
    {0b01111110,  // 0  WLAN100  0: . 0 0 0 0 0 0 . :  7
     0b11111111,  // 1          15: 0 0 0 0 0 0 0 0 :  8
     0b10000001,  // 2          16: 0 . . . . . . 0 : 23
     0b00111100,  // 3          31: . . 0 0 0 0 . . : 24
     0b01111110,  // 4          32: . 0 0 0 0 0 0 . : 39
     0b01000010,  // 5          47: . 0 . . . . 0 . : 40
     0b00011000,  // 6          48: . . . 0 0 . . . : 49
     0b00011000}, // 7          57: . . . 0 0 . . . : 50

    {0b00000000,  // 0  FIRE1    0: . . . . . . . . :  7
     0b00000000,  // 1          15: . . . . . . . . :  8
     0b00000000,  // 2          16: . . . . . . . . : 23
     0b00000000,  // 3          31: . . . . . . . . : 24
     0b00000000,  // 4          32: . . . . . . . . : 39
     0b00000000,  // 5          47: . . . . . . . . : 40
     0b00000000,  // 6          48: . . . . . . . . : 49
     0b10000000}, // 7          57: 0 . . . . . . . : 50

    {0b00000000,  // 0  FIRE2    0: . . . . . . . . :  7
     0b00000000,  // 1          15: . . . . . . . . :  8
     0b00000000,  // 2          16: . . . . . . . . : 23
     0b00000000,  // 3          31: . . . . . . . . : 24
     0b00000000,  // 4          32: . . . . . . . . : 39
     0b00000000,  // 5          47: . . . . . . . . : 40
     0b00100000,  // 6          48: . . 0 . . . . . : 49
     0b01000000}, // 7          57: . 0 . . . . . . : 50

    {0b00000000,  // 0  FIRE3    0: . . . . . . . . :  7
     0b00000000,  // 1          15: . . . . . . . . :  8
     0b00000000,  // 2          16: . . . . . . . . : 23
     0b00000000,  // 3          31: . . . . . . . . : 24
     0b00010000,  // 4          32: . . . 0 . . . . : 39
     0b00100000,  // 5          47: . . 0 . . . . . : 40
     0b00100000,  // 6          48: . . 0 . . . . . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b00000000,  // 0  FIRE4    0: . . . . . . . . :  7
     0b00000000,  // 1          15: . . . . . . . . :  8
     0b00001000,  // 2          16: . . . . 0 . . . : 23
     0b00010100,  // 3          31: . . . 0 . 0 . . : 24
     0b00001000,  // 4          32: . . . . 0 . . . : 39
     0b00000000,  // 5          47: . . . . . . . . : 40
     0b00000000,  // 6          48: . . . . . . . . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b00000000,  // 0  FIRE5    0: . . . . . . . . :  7
     0b00001000,  // 1          15: . . . . 0 . . . :  8
     0b00010100,  // 2          16: . . . 0 . 0 . . : 23
     0b00100010,  // 3          31: . . 0 . . . 0 . : 24
     0b00010100,  // 4          32: . . . 0 . 0 . . : 39
     0b00001000,  // 5          47: . . . . 0 . . . : 40
     0b00000000,  // 6          48: . . . . . . . . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b00011100,  // 0  FIRE6    0: . . . 0 0 0 . . :  7
     0b00100010,  // 1          15: . . 0 . . . 0 . :  8
     0b01000001,  // 2          16: . 0 . . . . . 0 : 23
     0b01000001,  // 3          31: . 0 . . . . . 0 : 24
     0b01000001,  // 4          32: . 0 . . . . . 0 : 39
     0b00100010,  // 5          47: . . 0 . . . 0 . : 40
     0b00011100,  // 6          48: . . . 0 0 0 . . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b01100110,  // 0  HEART    0: . 0 0 . . 0 0 . :  7
     0b11111111,  // 1          15: 0 0 0 0 0 0 0 0 :  8
     0b11111111,  // 2          16: 0 0 0 0 0 0 0 0 : 23
     0b11111111,  // 3          31: 0 0 0 0 0 0 0 0 : 24
     0b11111111,  // 4          32: 0 0 0 0 0 0 0 0 : 39
     0b01111110,  // 5          47: . 0 0 0 0 0 0 . : 40
     0b00111100,  // 6          48: . . 0 0 0 0 . . : 49
     0b00011000}, // 7          57: . . . 0 0 . . . : 50

    {0b00111100,  // 0  SMILEY   0: . . 0 0 0 0 . . :  7
     0b01111110,  // 1          15: . 0 0 0 0 0 0 . :  8
     0b11011011,  // 2          16: 0 0 . 0 0 . 0 0 : 23
     0b11111111,  // 3          31: 0 0 0 0 0 0 0 0 : 24
     0b10111101,  // 4          32: 0 . 0 0 0 0 . 0 : 39
     0b10000001,  // 5          47: 0 0 . . . . 0 0 : 40
     0b01111110,  // 6          48: . 0 0 0 0 0 0 . : 49
     0b00111100}, // 7          57: . . 0 0 0 0 . . : 50

    {0b00000000,  // 0  NOTE     0: . . . . . . . . :  7
     0b00011111,  // 1          15: . . . 0 0 0 0 0 :  8
     0b01111111,  // 2          16: . 0 0 0 0 0 0 0 : 23
     0b01100011,  // 3          31: . 0 0 . . . 0 0 : 24
     0b01100011,  // 4          32: . 0 0 . . . 0 0 : 39
     0b11100111,  // 5          47: 0 0 0 . . 0 0 0 : 40
     0b11000110,  // 6          48: 0 0 . . . 0 0 . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b10011001,  // 0  SNOW     0: 0 . . 0 0 . . 0 :  7
     0b01011010,  // 1          15: . 0 . 0 0 . 0 . :  8
     0b00100100,  // 2          16: . . 0 . . 0 . . : 23
     0b11011011,  // 3          31: 0 0 . 0 0 . 0 0 : 24
     0b11011011,  // 4          32: 0 0 . 0 0 . 0 0 : 39
     0b00100100,  // 5          47: . . 0 . . 0 . . : 40
     0b01011010,  // 6          48: . 0 . 0 0 . 0 . : 49
     0b10011001}, // 7          57: 0 . . 0 0 . . 0 : 50

    {0b00000000,  // 0  MAIL     0: . . . . . . . . :  7
     0b11111111,  // 1          15: 0 0 0 0 0 0 0 0 :  8
     0b11000011,  // 2          16: 0 0 . . . . 0 0 : 23
     0b10100101,  // 3          31: 0 . 0 . . 0 . 0 : 24
     0b10011001,  // 4          32: 0 . . 0 0 . . 0 : 39
     0b10000001,  // 5          47: 0 . . . . . . 0 : 40
     0b11111111,  // 6          48: 0 0 0 0 0 0 0 0 : 49
     0b00000000}, // 7          57: . . . . . . . . : 50

    {0b00010000,  // 0  BELL     0: . . . 0 . . . . :  7
     0b00011000,  // 1          15: . . . 0 0 . . . :  8
     0b00100100,  // 2          16: . . 0 . . 0 . . : 23
     0b01000010,  // 3          31: . 0 . . . . 0 . : 24
     0b01000010,  // 4          32: . 0 . . . . 0 . : 39
     0b11000011,  // 5          47: 0 0 . . . . 0 0 : 40
     0b11111111,  // 6          48: 0 0 0 0 0 0 0 0 : 49
     0b00011000}, // 7          57: . . . 0 0 . . . : 50

    {0b00111100,  // 0  STOP     0: . . 0 0 0 0 . . :  7
     0b01000010,  // 1          15: . 0 . . . . 0 . :  8
     0b10100101,  // 2          16: 0 . 0 . . 0 . 0 : 23
     0b10011001,  // 3          31: 0 . . 0 0 . . 0 : 24
     0b10011001,  // 4          32: 0 . . 0 0 . . 0 : 39
     0b10100101,  // 5          47: 0 . 0 . . 0 . 0 : 40
     0b01000010,  // 6          48: . 0 . . . . 0 . : 49
     0b00111100}, // 7          57: . . 0 0 0 0 . . : 50

    {0b00011100,  // 0  STBY     0: . . . 0 0 0 . . :  7
     0b00100010,  // 1          15: . . 0 . . . 0 . :  8
     0b01000001,  // 2          16: . 0 . . . . . 0 : 23
     0b01000001,  // 3          31: . 0 . . . . . 0 : 24
     0b01000001,  // 4          32: . 0 . . . . . 0 : 39
     0b00100010,  // 5          47: . . 0 . . . 0 . : 40
     0b00011100,  // 6          48: . . . 0 0 0 . . : 49
     0b00000000}, // 7          57: . . . . . . . . : 50
};
"""
        try:
            path = filedialog.asksaveasfilename(defaultextension=".h", filetypes=[("icon files", "*.h")])
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(header)
                    f.write(Hstart)          # Symbol 0: WLAN100
                    for _ in range(6):       # danach 6x das berechnete Symbol
                        f.write("\n".join("    " + line for line in lines) + "\n" + "\n")
                    f.write(Hend)            # HEART ... STOP
                    f.write("\n".join("    " + line for line in lines) + "\n")  # STBY = berechnetes Symbol
                    f.write(Hend2)           # Abschluss 11x10 + 8x8-Tabelle
                messagebox.showinfo("Export", "Gespeichert als " + path)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Das Icon.h konnte nicht gespeichert werden:\n{e}")

    # ---------- Vorlage ----------
    def save_template(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if path:
                data = {
                    "cells": self.cells,
                    "selected": self.selected,
                    "varzwanzig": self.varzwanzig.get(),
                    "varviertel": self.varviertel.get(),
                    "minanzeige": self.minanzeige.get(),
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                messagebox.showinfo("Vorlage", "Vorlage gespeichert")
                self.canvas.focus_set()
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Die Vorlage konnte nicht gespeichert werden:\n{e}")

    def load_template(self):
        path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cells = data["cells"]
            rows_new = len(cells)
            cols_new = len(cells[0]) if cells else 0
            if rows_new != len(self.cells) or any(len(row) != len(self.cells[0]) for row in cells):
                messagebox.showerror(
                    "Fehler",
                    f"Die Vorlage passt nicht zum aktuellen Raster.\n"
                    f"Vorlage: {cols_new}×{rows_new}, aktuell: {len(self.cells[0])}×{len(self.cells)}"
                )
                return

            self.cells = cells
            sel = data.get("selected")
            if sel and len(sel) == rows_new and all(len(r) == cols_new for r in sel):
                self.selected = sel
            else:
                self.selected = [[False] * cols_new for _ in range(rows_new)]

            self.varzwanzig.set(data.get("varzwanzig", 0))
            self.varviertel.set(data.get("varviertel", 0))
            self.minanzeige.set(data.get("minanzeige", 0))

            self.refresh_all()
            self.check_words()
            messagebox.showinfo("Vorlage", "Vorlage geladen")
            self.canvas.focus_set()
        except FileNotFoundError:
            messagebox.showerror("Fehler", f"Die Datei wurde nicht gefunden:\n{path}")
        except json.JSONDecodeError:
            messagebox.showerror("Fehler", "Die Vorlage ist keine gültige JSON-Datei.")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", f"Die Vorlage konnte nicht geladen werden:\n{e}")

    def clear_grid(self):
        self.cells = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.selected = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.varzwanzig.set(0)
        self.varviertel.set(0)
        self.refresh_all()
        self.check_words()

    # ---------- Layout-Script ----------
    def get_grid_layout_text(self):
        rows, cols = len(self.cells), len(self.cells[0])
        header = """#pragma once

#include "ClockType.hpp"

"""
        header += "/*\n"
        header += "* Script erstellt mit Scriptmaker by M. Mahrt\n"
        header += " *           Layout Front \n"
        header += " *                COL\n"
        header += " *    X " + " ".join(str(c) for c in reversed(range(cols))) + "\n"
        header += " * ROW + " + " ".join("-" for _ in range(cols)) + "\n"

        rows_text = ""
        for r in range(rows):
            # Ausgabe wie im Raster: links = Spalte 0; Spaltennummern oben sind 10..0
            row_letters = [self.cells[r][c] if self.cells[r][c] else " " for c in range(cols)]
            rows_text += f" *  {r}  | " + " ".join(row_letters) + "\n"

        footer = " */\n"
        return header + rows_text + footer

    def _rev(self, occ):
        """Anzeige-Koordinaten -> Script-Koordinaten (Spalten von rechts gezählt)."""
        r, s, e = occ
        cols = len(self.cells[0])
        return r, cols - 1 - e, cols - 1 - s

    def _case(self, labels, occ):
        r, start, end = self._rev(occ)
        out = [f"        case FrontWord::{lbl}:" for lbl in labels]
        out.append(f"            setFrontMatrixWord({r}, {start}, {end});")
        out.append("             break;")
        out.append("")
        return out

    def generate_script(self):
        missing = [f"{WORDS[i]} ({zone_name(i)})" for i in self.required_indices() if i not in self.placed]
        ambiguous = [f"{WORDS[i]} ({zone_name(i)})" for i in self.ambiguous]
        if missing or ambiguous:
            text = "Nicht alle Wörter sind korrekt platziert."
            if missing:
                text += "\nFehlend: " + ", ".join(missing)
            if ambiguous:
                text += "\nMehrfach gefunden: " + ", ".join(ambiguous)
            text += "\n\nTrotzdem speichern?"
            if not messagebox.askyesno("Warnung", text):
                return

        lines = []

        # Einzelwörter
        for i, name in enumerate(FRONT_ENUM):
            if name is None or i not in self.placed:
                continue
            if i == ZWANZIG_IDX and self.varzwanzig.get():
                continue  # Uhr hat keine Anzeige ZWANZIG
            labels = [name] + ([EXTRA_CASE[name]] if name in EXTRA_CASE else [])
            lines += self._case(labels, self.placed[i])

        # ES IST
        if ES_IDX in self.placed and IST_IDX in self.placed:
            lines.append("        case FrontWord::es_ist:")
            for i in (ES_IDX, IST_IDX):
                r, start, end = self._rev(self.placed[i])
                lines.append(f"            setFrontMatrixWord({r}, {start}, {end});")
            lines += ["             break;", ""]

        # DREIVIERTEL (nur wenn angezeigt)
        if not self.varviertel.get() and DREI_VIERTEL_IDX in self.placed and VIERTEL_IDX in self.placed:
            lines.append("        case FrontWord::dreiviertel:")
            for i in (DREI_VIERTEL_IDX, VIERTEL_IDX):
                r, start, end = self._rev(self.placed[i])
                lines.append(f"            setFrontMatrixWord({r}, {start}, {end});")
            lines += ["             break;", ""]

        # ZWANZIG (nur wenn angezeigt)
        # if not self.varzwanzig.get() and ZWANZIG_IDX in self.placed:
        #     lines += self._case(["zwanzig"], self.placed[ZWANZIG_IDX])

        text_block = self.get_grid_layout_text()
        text_block += """
class De10x11_t : public ClockType {
public:
    virtual LanguageAbbreviation usedLang() override {
        return LanguageAbbreviation::DE;
    };

    virtual bool hasDreiviertel() override { return """
        text_block += "false" if self.varviertel.get() == 1 else "true"
        text_block += """; }

    void show(FrontWord word) override {
        switch (word) {
"""
        text_block_end = """
        case FrontWord::funk:
            setFrontMatrixWord(3, 4, 7);
			setFrontMatrixWord(8, 5, 10);
			setFrontMatrixWord(9, 2, 4);
            break;

        default:
            break;
        };
    };
};

De10x11_t _de10x11;
    """
        file_path = filedialog.asksaveasfilename(defaultextension=".hpp",
                                                 filetypes=[("HeaderTextdatei", "*.hpp")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text_block)
                    f.write("\n".join(lines))
                    f.write(text_block_end)
                messagebox.showinfo("Script", "Script gespeichert")
                self.canvas.focus_set()
            except Exception as e:
                messagebox.showerror("Fehler beim Speichern", f"Das Script konnte nicht gespeichert werden:\n{e}")

    # ---------- DXF ----------
    def save_letter_grid(self):
        letters = self.cells

        if any(cell == "" for row in letters for cell in row):
            if not messagebox.askyesno("Warnung", "Nicht alle Felder gefüllt.\nTrotzdem speichern?"):
                return

        row_count = len(letters)
        col_count = len(letters[0])

        if RAHMENGROSS == 250:
            rahmen_mm = 250
            x_spacing = 16.6666
            y_spacing = 16.6666
            text_height = 11.55
        else:
            rahmen_mm = 500
            x_spacing = 16.6666 * 2
            y_spacing = 16.6666 * 2
            text_height = 20.55

        filename = "buchstaben.dxf"
        self.create_letter_grid(letters, row_count, col_count, x_spacing, y_spacing, text_height, rahmen_mm, filename)

    def create_letter_grid(self, letters, row_count, col_count, x_spacing, y_spacing, text_height, rahmen_mm, filename):
        doc = ezdxf.new(dxfversion='AC1027')
        doc.units = ezdxf.units.MM
        msp = doc.modelspace()
        old_text_height = text_height

        if "myStandard" not in doc.styles:
            doc.styles.new("myStandard", dxfattribs={"font": "MS Gothic.ttf"})

        for row in range(row_count):
            for col in range(col_count):
                letter = letters[row][col]
                x = col * x_spacing
                y = -row * y_spacing
                x = x + ((rahmen_mm / 2) - (5 * x_spacing))
                y = y + ((rahmen_mm / 2) + (4.5001 * y_spacing))

                if letter in ("Ü", "Ö", "Ä"):
                    old_text_height = text_height
                    if RAHMENGROSS == 250:
                        text_height = text_height * 0.8571
                    else:
                        text_height = text_height * 0.93
                    y = y - ((old_text_height - text_height) / 2)
                    breite = "1.15"
                else:
                    text_height = old_text_height
                    breite = "1.0"

                if letter == "":
                    continue

                text_entity = msp.add_text(
                    letter,
                    dxfattribs={"height": text_height, "style": "myStandard", "width": breite}
                )
                text_entity.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

        # Minutenpunkte
        if self.minanzeige.get() != 1:
            radius = y_spacing / 8
            y = (rahmen_mm / 2) - (5.5 * y_spacing)
            for i in range(4):
                x = (rahmen_mm / 2) - (3 * x_spacing) + (i * x_spacing * 2)
                msp.add_circle(center=(x, y), radius=radius)

        # Rahmen
        square_points = [(0, 0), (rahmen_mm, 0), (rahmen_mm, rahmen_mm), (0, rahmen_mm)]
        msp.add_lwpolyline(square_points, close=True)

        try:
            path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")])
            if path:
                doc.saveas(path)
                messagebox.showinfo("DXF Vorlage", "Gespeichert als " + path)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Die DXF Vorlage konnte nicht gespeichert werden:\n{e}")

    # ---------- Einstellungen ----------
    def Einstellungen(self):
        settings_win = tk.Toplevel(self)
        settings_win.title("Grundeinstellungen")
        settings_win.geometry("300x250")
        settings_win.grab_set()

        tk.Label(settings_win, text="Anzahl Spalten:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        cols_var = tk.StringVar(value=str(COLS))
        tk.Entry(settings_win, textvariable=cols_var, width=5).grid(row=1, column=1, padx=10, pady=5)

        tk.Label(settings_win, text="Anzahl Reihen:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        rows_var = tk.StringVar(value=str(ROWS))
        tk.Entry(settings_win, textvariable=rows_var, width=5).grid(row=0, column=1, padx=10, pady=5)

        def save_and_close():
            global ROWS, COLS
            try:
                new_rows = int(rows_var.get())
                new_cols = int(cols_var.get())
            except ValueError:
                messagebox.showerror("Fehler", "Bitte ganze Zahlen für Spalten und Reihen eingeben.",
                                     parent=settings_win)
                return
            if new_rows < 1 or new_cols < 1:
                messagebox.showerror("Fehler", "Spalten und Reihen müssen mindestens 1 sein.",
                                     parent=settings_win)
                return
            ROWS, COLS = new_rows, new_cols
            settings_win.destroy()
            self.destroy()
            GridApp().mainloop()

        tk.Button(settings_win, text="Speichern", command=save_and_close).grid(pady=10)
        tk.Button(settings_win, text="Abbrechen", command=settings_win.destroy).grid()


if __name__ == "__main__":
    GridApp().mainloop()
