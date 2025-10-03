## Hilfsprogramm zum Erstellen von Uhrenvorlagen
## by Michael Mahrt
## V2.0  15.08.2025
## Ergänzt:
## - DXF Vorlage für Laser
## - Unterstützung für Minutenpunkte hinzugefügt


# -*- coding: utf-8 -*-

import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText  # <-- neu
from matplotlib import font_manager
import json

import ezdxf
from ezdxf.enums import TextEntityAlignment

COLS = 11
ROWS = 10
CELL_SIZE = 30
LABEL_MARGIN_LEFT = 20  # Platz für Zeilenbeschriftung links
LABEL_MARGIN_TOP = 20   # Platz für Spaltenbeschriftung oben

DEBUG = True # True  # auf False setzen, um alle Debug-Ausgaben zu unterdrücken

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs) 

class GridApp(tk.Tk):  # Hauptklasse für die Anwendung


    def __init__(self):  # Konstruktor der Hauptklasse

        super().__init__()  # Aufruf des Konstruktors der Basisklasse

        self.title("Scriptmaker by MAHTec (C) M.Mahrt V2.1")  # Fenster Titel
        self.configure(bg="#f0f0f0")  # Hintergrundfarbe

        self.cells = [["" for _ in range(COLS)] for _ in range(ROWS)] #
        self.selected = [[False for _ in range(COLS)] for _ in range(ROWS)]

        self.words = [
            "UHR","EINS", "ZWEI", "DREI",
            "VIER", "FÜNF", "SECHS", "SIEBEN", "ACHT", "NEUN", "ZEHN",
            "ELF", "ZWÖLF", "EIN", "ES", "IST", "FÜNF", "ZEHN", "HALB", "ZWANZIG",
            "VOR", "NACH", "DREI", "VIERTEL"
        ]                                                          # Wortliste

        # Main frame für Wörter und Raster nebeneinander
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=10, pady=10) #

        # Wortliste links
        self.word_frame = tk.Frame(main_frame, bg="#f0f0f0") #
        self.word_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))

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

        cb1 = tk.Checkbutton(
            self.word_frame,
            text="Uhr hat KEINE Anzeige ZWANZIG",
            variable=self.varzwanzig,
            command=self.check_words  # <-- hier
        )
        cb2 = tk.Checkbutton(
            self.word_frame,
            text="Uhr hat KEINE Anzeige DREIVIERTEL",
            variable=self.varviertel,
            command=self.check_words  # <-- hier
        )

        cb3 = tk.Checkbutton(
            self.word_frame,
            text="Uhr hat KEINE Minutenanzeige",
            variable=self.minanzeige,
            command=self.check_words  # <-- hier
        )
        # Anzahl der Zeilen und Spalten für Labels
        max_rows = 12
        max_cols = (len(self.words) + max_rows - 1) // max_rows  # runden auf volle Spalten

        # Checkboxen unterhalb der Labels platzieren
        cb1.grid(row=max_rows, column=0, columnspan=max_cols, sticky="w", padx=7, pady=5)
        cb2.grid(row=max_rows+1, column=0, columnspan=max_cols, sticky="w", padx=7, pady=1)
        cb3.grid(row=max_rows+2, column=0, columnspan=max_cols, sticky="w", padx=7, pady=1)

        # Raster rechts
        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.LEFT, fill=tk.NONE)

        #tk.Label(right_frame, text="Raster 11×10", font=("Helvetica", 14, "bold"), bg="#f0f0f0").pack(pady=(10, 0))
        tk.Label(
            right_frame,
             text=f"Raster {COLS}×{ROWS}",   # f-String für Variablen
            font=("Helvetica", 14, "bold"),
            bg="#f0f0f0"
            ).pack(pady=(10, 0))

        self.canvas = tk.Canvas(right_frame, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE,
                                bg="white", highlightthickness=2, highlightbackground="#999999")
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)

        self.rectangles, self.text_items = {}, {}
        for r in range(ROWS):
            for c in range(COLS):
                x0, y0 = c*CELL_SIZE, r*CELL_SIZE
                rect = self.canvas.create_rectangle(x0, y0, x0+CELL_SIZE, y0+CELL_SIZE,
                                                     outline="#cccccc", fill="white")
                text = self.canvas.create_text(x0+CELL_SIZE/2, y0+CELL_SIZE/2,
                                                text="", font=("Helvetica", 14), )
                self.rectangles[(r,c)], self.text_items[(r,c)] = rect, text

        self.canvas.bind("<Button-1>", self.click_cell)
        self.bind("<Key>", self.key_press)
        self.current_cell = (0, 0)
        self.highlight_current_cell()
        self.focus_set()

        # Buttons unten quer über das ganze Fenster
        button_frame = tk.Frame(self, bg="#f0f0f0")
        button_frame.pack(side=tk.BOTTOM, pady=10)


        #tk.Button(button_frame, text="Export TXT", width=13, command=self.export_txt).grid(row=0, column=0, padx=4)
        tk.Button(button_frame, text="DXF Vorlage", width=15, command=self.save_letter_grid).grid(row=0, column=0, padx=4)
        tk.Button(button_frame, text="Speichern Vorlage", width=15, command=self.save_template).grid(row=0, column=1, padx=4)
        tk.Button(button_frame, text="Vorlage laden", width=13, command=self.load_template).grid(row=0, column=2, padx=4)
        tk.Button(button_frame, text="Lösche alles", width=13, command=self.clear_grid).grid(row=0, column=3, padx=4)
        tk.Button(button_frame, text="Exit", width=10, command=self.quit).grid(row=0, column=4, padx=4)
        tk.Button(button_frame, text="Einstellungen", width=10, command=self.Einstellungen).grid(row=0, column=5, padx=4)

        btn_frame = tk.Frame(right_frame, bg="#f0f0f0")
        btn_frame.pack(side=tk.TOP, pady=(0,10))

        self.script_button = tk.Button(btn_frame, text="Layoutscript erstellen", command=self.generate_script)
        self.script_button.pack(side="left", padx=4)  # Nebeneinander anordnen

        self.export_button = tk.Button(btn_frame, text="icons erstellen", command=self.export_txt)
        self.export_button.pack(side="left", padx=4)

        self.check_words()

    
    def click_cell(self, event):
        col, row = event.x//CELL_SIZE, event.y//CELL_SIZE
        debug_print(f"Clicked cell: ({row}, {col})")  # Debug-Ausgabe
        if 0<=row<ROWS and 0<=col<COLS:
            self.current_cell = (row,col)
            if self.cells[row][col]:
                self.selected[row][col] = not self.selected[row][col]
            else:
                self.selected[row][col] = False
            self.refresh_all()

    def key_press(self, event):
        if self.current_cell is None: return
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
        self.check_words() # <= Hier aktualisieren

 
    def check_words(self):
        
        ROWS = len(self.cells)
        COLS = len(self.cells[0])
        
        # Vorherige Positionen leeren
        self.word_positions = []
        results = [False] * len(self.words)
        
        # Hilfsfunktion zur Positionssuche
        def find_word_positions(word):
            positions = []
            length = len(word)
            for r in range(ROWS):
                for c in range(COLS - length + 1):
                    segment = ''.join(self.cells[r][c + i] for i in range(length))
                    if segment.upper() == word.upper():
                        # Positionszählung von rechts nach links
                        start_rev = COLS - 1 - (c + length - 1)
                        end_rev = COLS - 1 - c
                        positions.append((r, start_rev, end_rev))
            return positions

        for i, word in enumerate(self.words):
            # EIN wird zu Zahlenwort (Index 13 in self.words)
            if word == "EIN":
                word_index = 13
            else:
                word_index = i
            
            found_positions = find_word_positions(word)
            
            # Bereichsregel
            if word_index == 0 or (1 <= word_index <= 12) or word_index == 13:  # Zahlenwörter
                allowed_rows = set(range(3, ROWS))  # ab Reihe 3
            else:  # sonstige Wörter
                allowed_rows = set(range(0, 5))  # bis Reihe 4

            # Filter auf erlaubte Reihen
            valid_positions = [(r, s, e) for r, s, e in found_positions if r in allowed_rows]
            
            if valid_positions:
                for r, s, e in valid_positions:
                    self.word_positions.append((word_index, word, r, s, e, True))
                results[i] = True
            else:
                self.word_positions.append((word_index, word, None, None, None, False))
                results[i] = False

        # Debug-Ausgabe
        for idx, wort, r, s, e, gefunden in self.word_positions:
            debug_print(f"Index {idx}: Wort '{wort}', Reihe={r}, Start={s}, Ende={e}, Gefunden={'Ja' if gefunden else 'Nein'}")
        
        # Farben setzen
        for idx, wort, r, s, e, gefunden in self.word_positions:
            # Zuerst die Sonderfälle prüfen
            if (wort == "ZWANZIG" and getattr(self, "varzwanzig", tk.IntVar()).get()) \
            or (wort == "DREI" and getattr(self, "varviertel", tk.IntVar()).get() and idx >= 13):
                fg_color = "blue"
            else:
                # Normale Logik
                if gefunden:
                    fg_color = "green"
                else:
                    fg_color = "red"

            self.word_labels[idx].config(fg=fg_color)


    def move_to_next_cell(self):
        r, c = self.current_cell
        c += 1
        if c >= COLS:
            c = 0
            r += 1
            if r >= ROWS:
                r = 0
        self.current_cell = (r, c)


    def refresh_cell(self, r, c):
        if (r, c) == self.current_cell:
            bg = "#add8e6"
        else:
            bg = "#ffcc66" if self.selected[r][c] else ("#aaffaa" if self.cells[r][c] else "white")
        self.canvas.itemconfig(self.rectangles[(r,c)], fill=bg)
        self.canvas.itemconfig(self.text_items[(r,c)], text=self.cells[r][c])


    def refresh_all(self):
        for r in range(ROWS):
            for c in range(COLS):
                self.refresh_cell(r,c)
                self.highlight_current_cell()

                
    def highlight_current_cell(self):
        for (r, c), rect in self.rectangles.items():
            self.canvas.itemconfig(rect, outline="#cccccc")
        r, c = self.current_cell
        self.canvas.itemconfig(self.rectangles[(r,c)], outline="blue")
    


    # ---------- IO ----------
    def export_txt(self):
        lines = []
        bin_strs = []
        letters_list = []

        # Erzeuge alle Binärstrings + Buchstaben separat
        for r in range(ROWS):
            bits = ''.join('1' if self.selected[r][col] else '0' for col in reversed(range(COLS)))
            letters = ' '.join(self.cells[r][col] if self.cells[r][col] else ' ' for col in range(COLS))
            bin_strs.append(bits)
            letters_list.append(letters)

        # Formatiere jede Zeile mit korrektem Abstand
        for r in range(ROWS):
            if r == 0:
                bin_part = f'{{0b{bin_strs[r]}, '   # öffnende Klammer voran, Komma dahinter
            elif r == ROWS - 1:
                bin_part = f' 0b{bin_strs[r]}}},'  # schließende Klammer hinten, Komma dahinter
            else:
                bin_part = f' 0b{bin_strs[r]}, '    # normal mit Komma

            # Definiere Gesamtabstand bis zu den Buchstaben (z.B. 15 Zeichen)
            total_bin_width = len(f'{{0b{"0"*COLS},') 


            # Berechne wie viele Leerzeichen noch, damit alle Buchstaben bei gleicher Spalte starten
            spaces_needed = total_bin_width - len(bin_part)
            spaces_needed = max(spaces_needed, 0)

            # Erzeuge Leerzeichen, dann Buchstaben mit Kommentar
            line = bin_part + (" " * spaces_needed) + " " + f"//           {letters_list[r]}//"
            lines.append(line)

        header = """#pragma once

#define GRAFIK_11X10_ROWS 10
#define GRAFIK_11X10_COLS 11

const uint16_t grafik_11x10[][11] PROGMEM = {
"""
        Hend = """ 
    {0b00110001100,  // 0  7 HEART  0: . . 0 0 . . . 0 0 . . : 10
     0b01111011110,  // 1          21: . 0 0 0 0 . 0 0 0 0 . : 11
     0b11111111111,  // 2          22: 0 0 0 0 0 0 0 0 0 0 0 : 32
     0b11111111111,  // 3          43: 0 0 0 0 0 0 0 0 0 0 0 : 33
     0b11111111111,  // 4          44: 0 0 0 0 0 0 0 0 0 0 0 : 54
     0b01111111110,  // 5          65: . 0 0 0 0 0 0 0 0 0 . : 55
     0b00111111100,  // 6          66: . . 0 0 0 0 0 0 0 . . : 76
     0b00011111000,  // 7          87: . . . 0 0 0 0 0 . . . : 77
     0b00001110000,  // 8          88: . . . . 0 0 0 . . . . : 98
     0b00000100000}, // 9         109: . . . . . 0 . . . . . : 99

    {0b00011111000,  // 0   8       0: . . . 0 0 0 0 0 . . . : 10
     0b00111111100,  // 1          21: . . 0 0 0 0 0 0 0 . . : 11
     0b01101110110,  // 2          22: . 0 0 . 0 0 0 . 0 0 . : 32
     0b11111111111,  // 3          43: 0 0 0 0 0 0 0 0 0 0 0 : 33
     0b11111111111,  // 4          44: 0 0 0 0 0 0 0 0 0 0 0 : 54
     0b10111111101,  // 5          65: 0 . 0 0 0 0 0 0 0 . 0 : 55
     0b11001110011,  // 6          66: 0 0 . . 0 0 0 . . 0 0 : 76
     0b01110001110,  // 7          87: . 0 0 0 . . . 0 0 0 . : 77
     0b00111111100,  // 8          88: . . 0 0 0 0 0 0 0 . . : 98
     0b00011111000}, // 9         109: . . . 0 0 0 0 0 . . . : 99

    {0b00110000000,  // 0   9       0: . . . . . 0 . . . . . : 10
     0b00000000000,  // 1          21: . . . . . 0 . . . . . : 11
     0b00000000000,  // 2          22: . . 0 0 . 0 . 0 0 . . : 32
     0b00000000000,  // 3          43: . . 0 0 . 0 . 0 0 . . : 33
     0b00000001100,  // 4          44: . . . . 0 0 0 . . . . : 54
     0b00000000000,  // 5          65: . 0 0 0 0 0 0 0 0 0 . : 55
     0b00000000000,  // 6          66: . . . . 0 0 0 . . . . : 76
     0b00000000000,  // 7          87: . . 0 0 . 0 . 0 0 . . : 77
     0b00000000000,  // 8          88: . . 0 0 . 0 . 0 0 . . : 98
     0b00000111000}, // 9         109: . . . . . 0 . . . . . : 99

    {0b00000000000,  //   10        0: . . . . . . . . . . . : 10
     0b00000000000,  //             0: . . . . . . . . . . . : 21
     0b00000000000,  //             0: . . . . . . . . . . . : 32
     0b10001010001,  //             0: 0 . . . 0 . 0 . . . 0 : 43
     0b11011011011,  //             0: 0 0 . 0 0 . 0 0 . 0 0 : 54
     0b10101010101,  //             0: 0 . 0 . 0 . 0 . 0 . 0 : 65
     0b10001010001,  //             0: 0 . . . 0. .0. . . .0.: 76
     0b10001010001,  //             0: 0. . . .0 . 0 . . . 0 : 87
     0b00000000000,  //             0: . . . . . . . . . . . : 98
     0b00000000000}, //             0: . . . . . . . . . . . : 99
};
    """
        try:
            path = filedialog.asksaveasfilename(defaultextension=".h", filetypes=[("icon files","*.h")])
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(header)
                    for _ in range(7):
                        f.write("\n".join("    " + line for line in lines) + "\n"+ "\n")
                    f.write(Hend)
                messagebox.showinfo("Export", "Gespeichert als " + path)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Das Icon.h konnte nicht gespeichert werden:\n{e}")

    def save_template(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
            if path:
                data = {
                    "cells": self.cells,
                    "selected": self.selected,
                    "varzwanzig": self.varzwanzig.get(),   # Wert der Checkbox ZWANZIG
                    "varviertel": self.varviertel.get()  # Wert der Checkbox DREIVIERTEL
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                messagebox.showinfo("Vorlage", "Vorlage gespeichert")
                self.canvas.focus_set()
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Die Vorlage konnte nicht gespeichert werden:\n{e}")

    def load_template(self):
        path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.cells = data.get("cells", self.cells)
                self.selected = data.get("selected", [[False] * COLS for _ in range(ROWS)])

                # Checkboxen wiederherstellen
                self.varzwanzig.set(data.get("varzwanzig", 0))
                self.varviertel.set(data.get("varviertel", 0))

                self.refresh_all()
                messagebox.showinfo("Vorlage", "Vorlage geladen")
                self.check_words()
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
        
        # Checkboxen zurücksetzen
        self.varzwanzig.set(0)
        self.varviertel.set(0)
        
        self.refresh_all()
        self.check_words()

    def find_word_in_row(self, word, row):
        length = len(word)
        for start_col in range(COLS - length + 1):
            matched = True
            for i in range(length):
                col = start_col + i
                if self.cells[row][col].upper() != word[i].upper():
                    matched = False
                    break
            if matched:
                # Gefunden an Reihe 'row', von Spalte start_col bis start_col+length-1
                return (row, start_col, start_col + length - 1)
        return None    
    
    def get_grid_layout_text(self):
        # cells: 2D-Liste (ROWS x COLS) mit Großbuchstaben-Strings
        ROWS, COLS = len(self.cells), len(self.cells[0])
        header = """#pragma once

#include "Uhrtype.hpp"

"""
        header += "/*\n"
        header += """* Script erstellt mit Scriptmaker by M. Mahrt\n"""
        
        header += " *           Layout Front \n"
        header += " *                COL\n"
        header += " *    X " + " ".join(str(c) for c in reversed(range(COLS))) + "\n"
        header += " * ROW + " + " ".join("-" for _ in range(COLS)) + "\n"

        rows_text = ""
        for r in range(ROWS):
            # Zellen in Reihe, von links nach rechts in cells, werden aber rechtsbündig mit Spalten 10..0 angezeigt
            row_letters = [self.cells[r][c] if self.cells[r][c] else " " for c in range(COLS)]
            # Die Ausgabe soll von Spalte 10 bis 0, also reversed
            row_letters_reversed = list((row_letters))
            rows_text += f" *  {r}  | " + " ".join(row_letters_reversed) + "\n"

        footer = " */\n"
        return header + rows_text + footer


       
    def generate_script(self):

        tesv = ""
        tesh = ""
        tdreiv = ""
        tdreih = ""

        word_map = {
            "EIN": "hour_1",
            "ZWEI": "hour_2",
            "DREI": "hour_3",
            "VIER": "hour_4",
            "FÜNF": "min_5",
            "SECHS": "hour_6",
            "SIEBEN": "hour_7",
            "ACHT": "hour_8",
            "NEUN": "hour_9",
            "ZEHN": "hour_10",
            "ELF": "hour_11",
            "ZWÖLF": "hour_12",
            "EINS": "eins",
            "UHR": "uhr",
            "FÜNF": "hour_5",
            "ZEHN": "min_10",
            "HALB": "halb",
            "ZWANZIG": "min_20",
            "VOR": "vor",
            "NACH": "nach",
            "VIERTEL": "viertel",
            #DREI": "drei",
            "ES": "es",
            "IST": "ist",
        }


        # Status der Wörter
        words_fg = [lbl.cget("fg") for lbl in self.word_labels]

        # Indizes der Sonderwörter
        # idx_viertel = self.words.index(22)  #("DREI")
        idx_zwanzig = self.words.index("ZWANZIG")

        # Alle Indizes des Wortes "DREI" finden
        drei_indices = [i for i, w in enumerate(self.words) if w == "DREI"]

        # Angenommen, wir wollen den zweiten DREI prüfen:
        idx_viertel = drei_indices[1]

        # Normale Wörter außer Sonderwörter
        normal_indices = [i for i in range(len(self.words)) if i not in (idx_viertel, idx_zwanzig)]
        normal_all_green = all(words_fg[i] == "green" for i in normal_indices)

        # Sonderwörter: nur Warnung, wenn sie **nicht grün** **und** Checkbox **nicht aktiviert** ist
        viertel_problem = (words_fg[idx_viertel] != "green") and (not self.varviertel.get())
        zwanzig_problem = (words_fg[idx_zwanzig] != "green") and (not self.varzwanzig.get())
 

        # Meldung nur anzeigen, wenn irgendein Problem vorliegt
        if not normal_all_green or viertel_problem or zwanzig_problem :
            result = messagebox.askyesno(
                "Warnung",
                "Nicht alle Wörter sind korrekt markiert.\nTrotzdem speichern?"
            )
            if not result:
                return


        lines = []
        skip_next = False

        # self.word_positions ist: [(wort, reihe, start, ende), ...]
        for i, (word_index, _, reihe, start_col, end_col, _) in enumerate(self.word_positions):
            wort = self.words[word_index]  # echtes Wort holen

            if skip_next:
                skip_next = False
                continue

            mapped_name = None


            # Einzelwort-Mapping
            if mapped_name is None:
                mapped_name = word_map.get(wort, wort)

            if reihe is not None:
                start_script_col = start_col
                end_script_col = end_col
                if mapped_name=="hour_3" and reihe <=4:
                    mapped_name = ""
                    tdreiv = reihe, start_script_col, end_script_col 

                if mapped_name=="hour_5" and reihe < 4:
                    
                    mapped_name = "min_5"
                if mapped_name=="min_10" and reihe > 4:
                    mapped_name = "hour_10"
                if mapped_name == "es":
                    tesv = reihe, start_script_col, end_script_col
                    mapped_name = ""
                if mapped_name == "ist":
                    tesh = reihe, start_script_col, end_script_col    
                    mapped_name = ""
                
                     
                if mapped_name == "viertel":
                    tdreih = reihe, start_script_col, end_script_col 
                if self.varzwanzig.get() == 1 and mapped_name =="min_20":
                    mapped_name =""
                if mapped_name == "vor":
                    mapped_name = "vor:\n        case FrontWord::v_vor"
                if mapped_name == "nach":
                    mapped_name = "nach:\n        case FrontWord::v_nach"
                
                if mapped_name != "":
                    lines.append(f"        case FrontWord::{mapped_name}:")
                    lines.append(f"            setFrontMatrixWord({reihe}, {start_script_col}, {end_script_col});")
                    lines.append("             break;")
                    lines.append("")
            #lse:
                # lines.append(f"        case FrontWord::{mapped_name}:")
                # lines.append("            setFrontMatrixWord(0, 0, 0);")
                # lines.append("            setFrontMatrixWord(0, 10, 10);")
                # lines.append("           break;")
                # lines.append("")
           
        lines.append(f"        case FrontWord::es_ist:")
        lines.append(f"            setFrontMatrixWord({tesv[0]}, {tesv[1]}, {tesv[2]});")
        lines.append(f"            setFrontMatrixWord({tesh[0]}, {tesh[1]}, {tesh[2]});")
        lines.append("             break;")
        lines.append("")   

        if self.varviertel.get() == 0 and mapped_name =="viertel":
            lines.append(f"        case FrontWord::dreiviertel:")
            lines.append(f"            setFrontMatrixWord({tdreiv[0]}, {tdreih[1]}, {tdreiv[2]});")
            lines.append("             break;")
            lines.append("") 
        
        if self.varzwanzig.get() == 0 and mapped_name =="min_20":
            lines.append(f"        case FrontWord::zwanzig:")
            lines.append(f"            setFrontMatrixWord({tdreiv[0]}, {tdreih[1]}, {tdreiv[2]});")
            lines.append("             break;")
            lines.append("") 

        # Datei speichern

        text_block = self.get_grid_layout_text()
        text_block += """
class De10x11_t : public iUhrType {
public:
    virtual LanguageAbbreviation usedLang() override {
        return LanguageAbbreviation::DE;
    };

    virtual const bool hasZwanzig() override { return """
        if self.varzwanzig.get() == 1:
            text_block += """false"""
        elif self.varzwanzig.get() == 0:
            text_block += """true"""
        text_block += """; }
    virtual const bool hasDreiviertel() override { return """
        if self.varviertel.get() == 1:
            text_block += """false"""
        elif self.varviertel.get() == 0:
            text_block += """true"""
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
        file_path = filedialog.asksaveasfilename(defaultextension=".hpp", filetypes=[("HeaderTextdatei","*.hpp")])

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text_block)    
                    f.write("\n".join(lines))
                    f.write(text_block_end)
                messagebox.showinfo("Script","Script gespeichert")
                self.canvas.focus_set()
            except Exception as e:
                messagebox.showerror("Fehler beim Speichern", f"Das Script konnte nicht gespeichert werden:\n{e}")
           

    def save_letter_grid(self):
        letters = self.cells


#for i in range(ROWS):
 #           letters.append([f"{chr(65 + j)}" for j in range(COLS)])

        row_count = ROWS
        col_count = COLS
        rahmen_mm = 250
        x_spacing = 16.6666
        y_spacing = 16.6666
        text_height = 11.55
        filename = "buchstaben.dxf"

        self.create_letter_grid(letters, row_count, col_count, x_spacing, y_spacing, text_height, rahmen_mm, filename)

    def create_letter_grid(self, letters, row_count, col_count, x_spacing, y_spacing, text_height, rahmen_mm, filename):
        # Neue DXF-Datei
        doc = ezdxf.new(dxfversion='AC1027')
        doc.units = ezdxf.units.MM
        msp = doc.modelspace()
        old_text_height = text_height   

        # Textstil anlegen (falls nicht vorhanden)
        if "myStandard" not in doc.styles:
            doc.styles.new("myStandard", dxfattribs={"font": "MS UI Gothic.ttf"})

        # Buchstaben platzieren
        for row in range(row_count):
            for col in range(col_count):
                if row < len(letters) and col < len(letters[row]):
                    letter = letters[row][col]
                    x = col * x_spacing
                    y = -row * y_spacing  # Reihen nach unten
                    x=x+((rahmen_mm/2)-(5*x_spacing))
                    y=y+((rahmen_mm/2)+(4.5001*y_spacing))

                    if letter =="Ü" or letter =="Ö" or letter =="Ä":
                        old_text_height = text_height
                        text_height = text_height * 0.8571
                        y = y - ((old_text_height-text_height) / 2)
                        Buchbreite ="1.15"
                        
                    else:
                        text_height = old_text_height
                        Buchbreite ="1.0"

                    text_entity = msp.add_text(
                        letter,
                        dxfattribs={
                            "height": text_height,
                            "style": "myStandard",
                            "width": Buchbreite
                        }
                    )
                    # zentrierte Platzierung
                    text_entity.set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

        # Minutenpunkte
        if self.minanzeige.get() != 1:
            radius = y_spacing/8
            y = (rahmen_mm/2) - (5.5 * y_spacing)  # Reihen nach unten
            for i in range(4):
                x = (rahmen_mm/2) -(3 * x_spacing) + (i * x_spacing * 2)
                center = (x, y)
                msp.add_circle(center=center, radius=radius)

        # RRahmen
        square_points = [
            (0, 0),
            (rahmen_mm, 0),
            (rahmen_mm, rahmen_mm),
            (0, rahmen_mm),
        ]
       # geschlossenes Quadrat als eine Polyline
        msp.add_lwpolyline(square_points, close=True)
        # DXF speichern

        # Alle Felder gefüllt? Sonst Warnung
        for row in range(row_count):
            for col in range(col_count):
                bu=letters[row][col]
                if bu == "":
                    #print(f"Leeres Feld bei {row},{col}")
                    result = messagebox.askyesno(
                        "Warnung",
                        "Nicht alle Felder gefüllt.\nTrotzdem speichern?"
                    )
                    if not result:
                        return
            
        
        try:
            
            path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files","*.dxf")])
            if path:
                doc.saveas(path)
                print(f"DXF gespeichert: {path}")
                messagebox.showinfo("DXF Vorlage", "Gespeichert als " + path)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Die DXF Vorlage konnte nicht gespeichert werden:\n{e}")
    


    # Einstellungsfenster
    def Einstellungen(self):
        # Neues Fenster erstellen
        settings_win = tk.Toplevel(self)
        settings_win.title("Grundeinstellungen")
        settings_win.geometry("300x250")
        settings_win.grab_set()  # macht das Fenster modal

        # Beispiel-Optionen
        
        
        tk.Label(settings_win, text="Anzahl Spalten:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        cols_var = tk.DoubleVar(value=COLS)  # Standardwert
        tk.Entry(settings_win, textvariable=cols_var, width=5).grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(settings_win, text="Anzahl Reihen:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        rows_var = tk.DoubleVar(value=ROWS)  # Standardwert
        tk.Entry(settings_win, textvariable=rows_var, width=5).grid(row=0, column=1, padx=10, pady=5)

        show_grid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_win, text="Raster anzeigen", variable=show_grid_var).grid(row=0, column=3, padx=10, pady=5)

        # Buttons
        def save_and_close():
            # Hier kannst du Werte übernehmen
            print("Spalten:", cols_var.get())
            print("Reihen:", rows_var.get())
            global ROWS
            ROWS=int(rows_var.get())
            global COLS
            COLS=int(cols_var.get())    
            print("Raster anzeigen:", show_grid_var.get())
            settings_win.destroy()
            self.destroy()           # Fenster schließen
            GridApp().mainloop()     # neue Instanz starten

        tk.Button(settings_win, text="Speichern", command=save_and_close).grid(pady=10)
        tk.Button(settings_win, text="Abbrechen", command=settings_win.destroy).grid()






if __name__=="__main__":
    GridApp().mainloop()
