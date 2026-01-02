import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json

# ---------------- Globale Variablen ----------------
ROWS = 10
COLS = 11
Wortstelle = []
DEBUG = True  # True  # auf False setzen, um alle Debug-Ausgaben zu unterdrücken


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


# ---------------- LetterGrid ----------------
class LetterGrid(ttk.Frame):
    def __init__(self, master, rows=ROWS, cols=COLS):
        super().__init__(master)
        self.rows = rows
        self.cols = cols
        self.entries = [[None for _ in range(cols)] for _ in range(rows)]
        self.create_grid()

    def create_grid(self):
        """
        Erzeugt ein Raster mit:
         - Spaltenbeschriftung oben (von rechts nach links absteigend, beginnend mit 0 oben rechts)
         - Zeilenbeschriftung links (0, 1, 2, 3 … von oben nach unten)
        Die Entry-Zellen liegen in grid-Position (r+1, c+1)
        """
        grid_frame = ttk.Frame(self)
        grid_frame.grid(row=0, column=0)

        # ---- Spaltenbeschriftungen (oben) ----
        for c in range(self.cols):
            # Berechne Index für Spalte c (rechts nach links absteigend)
            top_index = (self.cols - 1 - c)
            lbl = ttk.Label(grid_frame, text=str(top_index), font=("Arial", 12))
            lbl.grid(row=0, column=c+1, padx=2, pady=(2, 0), sticky="s")

        # ---- Zeilenbeschriftungen (links) + Eingabefelder ----
        for r in range(self.rows):
            # Zeilennummer (einfach 0..n)
            lbl_row = ttk.Label(grid_frame, text=str(r), font=("Arial", 12))
            lbl_row.grid(row=r+1, column=0, padx=(2, 8), pady=2, sticky="e")

            for c in range(self.cols):
                cell_frame = tk.Frame(grid_frame, bg="black", bd=0)
                cell_frame.grid(row=r+1, column=c+1, padx=2, pady=2)

                e = tk.Entry(
                    cell_frame,
                    width=2,
                    justify="center",
                    font=("Arial", 14),
                    bg="black",
                    fg="white",
                    insertbackground="white",
                    relief="flat",
                    bd=0,
                    highlightthickness=0
                )
                e.pack(padx=4, pady=4, fill="both", expand=True)

                vcmd = (self.register(self.validate_entry), "%P", "%d", "%i", "%W")
                e.config(validate="key", validatecommand=vcmd)
                e.bind("<KeyRelease>", self.next_cell)
                e.bind("<Button-1>", self.select_cell)
                self.entries[r][c] = e

        # Optionaler Hinweis
        info = ttk.Label(
            grid_frame,
            text=f"Raster = {self.cols} x {self.rows} ",
            font=("Arial", 12, "italic")
        )
        info.grid(row=self.rows + 1, column=0, columnspan=self.cols + 1, pady=(6, 0))

    def validate_entry(self, new_value, action_type, index, widget_name):
        if action_type == '0':
            return True
        if new_value == " ":
            return True
        if new_value.isalpha() and len(new_value) <= 1:
            return True
        return False

    def next_cell(self, event):
        widget = event.widget
        text = widget.get()
        if text.isalpha():
            widget.delete(0, tk.END)
            widget.insert(0, text.upper())
        elif text == " ":
            widget.delete(0, tk.END)
            widget.insert(0, " ")

        # Fokus auf nächste Zelle
        for r in range(self.rows):
            for c in range(self.cols):
                if self.entries[r][c] == widget:
                    next_r, next_c = r, c + 1
                    if next_c >= self.cols:
                        next_c = 0
                        next_r += 1
                    if next_r < self.rows:
                        next_widget = self.entries[next_r][next_c]
                        next_widget.focus()
                        next_widget.select_range(0, tk.END)
                    check_words_in_grid(self, self.master.control_panel)
                    return

    def select_cell(self, event):
        widget = event.widget
        widget.focus()
        widget.select_range(0, tk.END)
        return "break"

    def clear_grid(self):
        for row in self.entries:
            for cell in row:
                cell.delete(0, tk.END)
                cell.insert(0, "")





# ---------------- ControlPanel ----------------
class ControlPanel(ttk.Frame):
    def __init__(self, master, words):
        super().__init__(master)
        self.first_col_words = words[:12]
        self.second_col_words = words[12:24]
        self.first_col_labels = []
        self.second_col_labels = []
        self.create_widgets()

    def create_widgets(self):
        label_frame = ttk.LabelFrame(self, text="Worte")
        label_frame.pack(pady=10, padx=10)

        for i, word in enumerate(self.first_col_words):
            lbl = ttk.Label(label_frame, text=word, width=12, anchor="center", foreground="red")
            lbl.grid(row=i, column=0, padx=2, pady=2)
            self.first_col_labels.append(lbl)

        for i, word in enumerate(self.second_col_words):
            lbl = ttk.Label(label_frame, text=word, width=12, anchor="center", foreground="red")
            lbl.grid(row=i, column=1, padx=2, pady=2)
            self.second_col_labels.append(lbl)

        check_frame = ttk.LabelFrame(self, text="Optionen")
        check_frame.pack(pady=10, padx=10, fill="x")
        self.check_vars = []
        texts = [
            "Uhr hat KEINE Anzeige ZWANZIG",
            "Uhr hat KEINE Anzeige DREIVIERTEL",
            "Uhr hat KEINE Minutenanzeige"
        ]
        for i, text in enumerate(texts):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(check_frame, text=text, variable=var,
                                 command=lambda i=i: self.on_check(i))
            cb.pack(anchor="w", pady=2)
            self.check_vars.append(var)

    def on_check(self, index):
        if index == 0:
            word = "ZWANZIG"
            lbl = None
            if word in self.first_col_words:
                lbl = self.first_col_labels[self.first_col_words.index(word)]
            elif word in self.second_col_words:
                lbl = self.second_col_labels[self.second_col_words.index(word)]
            if lbl:
                lbl.configure(foreground="blue" if self.check_vars[0].get() else "green")
        elif index == 1:
            word = "DREI"
            lbl = None
            if word in self.second_col_words:
                lbl = self.second_col_labels[self.second_col_words.index(word)]
            if lbl:
                lbl.configure(foreground="blue" if self.check_vars[1].get() else "red")


# ---------------- BottomPanel ----------------
class BottomPanel(ttk.Frame):
    def __init__(self, master, letter_grid, control_panel, ausgabe_text):
        super().__init__(master)
        self.letter_grid = letter_grid
        self.control_panel = control_panel
        self.ausgabe_text = ausgabe_text
        self.create_widgets()

    def create_widgets(self):
        button_texts = [
            "Alle Eingaben löschen",
            "Wortpositionen speichern",
            "Grid speichern",
            "Grid laden",
            "Wortliste anzeigen"
        ]

        for i, text in enumerate(button_texts):
            if i == 0:
                btn = ttk.Button(self, text=text, command=self.clear_grid)
            elif i == 1:
                btn = ttk.Button(self, text=text,
                                 command=lambda: button2_save_word_positions(self.letter_grid, self.control_panel))
            elif i == 2:
                btn = ttk.Button(self, text=text,
                                 command=lambda: save_grid_to_json(self.letter_grid))
            elif i == 3:
                btn = ttk.Button(self, text=text,
                                 command=lambda: load_grid_from_json(self.letter_grid, self.control_panel))
            elif i == 4:
                btn = ttk.Button(self, text=text, command=self.list_wort)
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

        for i in range(5):
            self.columnconfigure(i, weight=1)

    def list_wort(self):
        self.ausgabe_text.delete("1.0", tk.END)
        self.ausgabe_text.insert(tk.END, "Wortstelle (grüne Wörter mit Position):\n\n")
        for ws in Wortstelle:
            self.ausgabe_text.insert(tk.END, f"{ws}\n")

    def clear_grid(self):
        self.letter_grid.clear_grid()
        check_words_in_grid(self.letter_grid, self.control_panel)


# ---------------- Funktionen ----------------
def check_words_in_grid(grid, control_panel):
    global Wortstelle
    Wortstelle = []
    linear_grid = "".join([e.get().upper() if e.get() != "" else " "
                           for row in grid.entries for e in row])
    halb_index = linear_grid.find("HALB")
    special_words = ["DREI", "VIER", "FÜNF", "ZEHN"]
    all_words = control_panel.first_col_words + control_panel.second_col_words
    found_words = []
    for word in all_words:
        start = 0
        while True:
            idx = linear_grid.find(word, start)
            if idx == -1:
                break
            found_words.append((word, idx))
            start = idx + 1

    for i, word in enumerate(control_panel.first_col_words):
        color = "red"
        green_added = False
        for fw, idx in found_words:
            if fw == word and not green_added:
                if word in special_words and halb_index != -1:
                    if idx > halb_index:
                        color = "green"
                        Wortstelle.append((word, idx // grid.cols, grid.cols - (idx % grid.cols) - len(word),
                                           grid.cols - (idx % grid.cols) - 1))
                        green_added = True
                else:
                    color = "green"
                    Wortstelle.append((word, idx // grid.cols, grid.cols - (idx % grid.cols) - len(word),
                                       grid.cols - (idx % grid.cols) - 1))
                    green_added = True
        control_panel.first_col_labels[i].configure(foreground=color)

    for i, word in enumerate(control_panel.second_col_words):
        color = "red"
        green_added = False
        for fw, idx in found_words:
            if fw == word and not green_added:
                if word in special_words and halb_index != -1:
                    if idx < halb_index:
                        color = "green"
                        Wortstelle.append((word, idx // grid.cols, grid.cols - (idx % grid.cols) - len(word),
                                           grid.cols - (idx % grid.cols) - 1))
                        green_added = True
                else:
                    color = "green"
                    Wortstelle.append((word, idx // grid.cols, grid.cols - (idx % grid.cols) - len(word),
                                       grid.cols - (idx % grid.cols) - 1))
                    green_added = True
        control_panel.second_col_labels[i].configure(foreground=color)


def button2_save_word_positions(letter_grid, control_panel):
    all_words = control_panel.first_col_words + control_panel.second_col_words
    positions = []

    for row_idx, row in enumerate(letter_grid.entries):
        row_text = "".join([e.get().upper() if e.get() != "" else " " for e in row])
        row_len = len(row_text)

        for word_idx, word in enumerate(all_words):
            start = 0
            while True:
                idx = row_text.find(word, start)
                if idx == -1:
                    break
                start_from_right = row_len - idx - len(word)
                end_from_right = row_len - idx - 1
                positions.append((word_idx, word, row_idx, start_from_right, end_from_right))
                start = idx + 1
    positions.sort(key=lambda x: x[0])
    debug_print("Wortpositionen im Grid:")
    for pos in positions:
        debug_print(pos)


def save_grid_to_json(letter_grid):
    data = [[cell.get().upper() if cell.get() != "" else " " for cell in row] for row in letter_grid.entries]
    file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                             filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        debug_print(f"Grid in {file_path} gespeichert.")


def load_grid_from_json(letter_grid, control_panel):
    file_path = filedialog.askopenfilename(defaultextension=".json",
                                           filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for r, row in enumerate(letter_grid.entries):
            for c, cell in enumerate(row):
                if r < len(data) and c < len(data[r]):
                    cell.delete(0, tk.END)
                    cell.insert(0, data[r][c])
        check_words_in_grid(letter_grid, control_panel)


# ---------------- Hauptprogramm ----------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Grid + Steuerpanel + Tabs")
    root.geometry("950x600")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Tab 1: Eingabe ---
    tab_eingabe = ttk.Frame(notebook)
    notebook.add(tab_eingabe, text="Eingabe")

    words = [
        "EINS", "ZWEI", "DREI",
        "VIER", "FÜNF", "SECHS", "SIEBEN", "ACHT", "NEUN", "ZEHN",
        "ELF", "ZWÖLF", "UHR", "EIN", "ES", "IST", "FÜNF", "ZEHN", "HALB", "ZWANZIG",
        "VOR", "NACH", "DREI", "VIERTEL"
    ]

    top_frame = tk.Frame(tab_eingabe)
    top_frame.pack(padx=10, pady=10, fill="both", expand=True)

    control_panel = ControlPanel(top_frame, words)
    control_panel.pack(side="left", fill="y", padx=10, pady=10)

    grid = LetterGrid(top_frame)
    grid.pack(side="left", padx=10, pady=10)
    grid.master.control_panel = control_panel

    
    # --- Tab 2: Ausgabe ---
    tab_ausgabe = ttk.Frame(notebook)
    notebook.add(tab_ausgabe, text="Ausgabe")

    # ---------------- Platzhalter-Funktionen für Buttons ----------------
    def generate_uhrtype():
        text_view.config(state="normal")
        text_view.insert(tk.END, "\n// uhrtype.h erzeugt\n")
        text_view.config(state="disabled")
        messagebox.showinfo("Info", "uhrtype.h erzeugt!")

    def generate_icon():
        text_view.config(state="normal")
        text_view.insert(tk.END, "\n// Icon.h erzeugt\n")
        text_view.config(state="disabled")
        messagebox.showinfo("Info", "Icon.h erzeugt!")

    # ---------------- Buttons oben ----------------
    btn_uhrtype = ttk.Button(tab_ausgabe, text="uhrtype.h erzeugen", command=generate_uhrtype)
    btn_uhrtype.place(x=10, y=10, width=180, height=30)

    btn_icon = ttk.Button(tab_ausgabe, text="Icon.h erzeugen", command=generate_icon)
    btn_icon.place(x=210, y=10, width=180, height=30)

    # ---------------- ScrolledText darunter ----------------
    text_view = scrolledtext.ScrolledText(tab_ausgabe, 
                                        wrap="word",
                                        font=("Consolas", 8),
                                        width=20,
                                        height=10)
    text_view.place(x=10, y=50, width=380, height=260)  # y=50, damit Buttons frei bleiben




# Button zum Laden der Datei
    

# --- Tab 3: Einstellungen ---
    tab_settings = ttk.Frame(notebook)
    notebook.add(tab_settings, text="Einstellungen")

    # Rahmen für Eingabefelder
    settings_frame = ttk.LabelFrame(tab_settings, text="Grid-Einstellungen")
    settings_frame.pack(padx=20, pady=20, fill="x")

    # --- Eingabefeld: Reihen ---
    lbl_rows = ttk.Label(settings_frame, text="Anzahl Reihen:")
    lbl_rows.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_rows = ttk.Entry(settings_frame, width=10)
    entry_rows.insert(0, str(ROWS))  # Standardwert aus globaler Variable
    entry_rows.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # --- Eingabefeld: Spalten ---
    lbl_cols = ttk.Label(settings_frame, text="Anzahl Spalten:")
    lbl_cols.grid(row=1, column=0, padx=5, pady=5, sticky="e")
    entry_cols = ttk.Entry(settings_frame, width=10)
    entry_cols.insert(0, str(COLS))
    entry_cols.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # --- Eingabefeld: Schriftart ---
    lbl_font = ttk.Label(settings_frame, text="Schriftart:")
    lbl_font.grid(row=2, column=0, padx=5, pady=5, sticky="e")
    entry_font = ttk.Entry(settings_frame, width=20)
    entry_font.insert(0, "Arial")  # Standardwert
    entry_font.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # --- Button zum Übernehmen der Änderungen ---
    def apply_settings():
        global grid  # wichtig!
        try:
            new_rows = int(entry_rows.get())
            new_cols = int(entry_cols.get())
            new_font = entry_font.get()
            messagebox.showinfo("Einstellungen übernommen",
                                f"Reihen: {new_rows}\nSpalten: {new_cols}\nSchriftart: {new_font}")
            #Hier kannst du optional das Grid dynamisch neu erzeugen:
            grid.destroy()
            grid = LetterGrid(top_frame, rows=new_rows, cols=new_cols)
            grid.pack(side="left", padx=10, pady=10)
            grid.master.control_panel = control_panel
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlen für Reihen und Spalten eingeben!")

    apply_btn = ttk.Button(settings_frame, text="Übernehmen", command=apply_settings)
    apply_btn.grid(row=3, column=0, columnspan=2, pady=(10, 5))


  

    # --- Bottom Panel (in Eingabe-Tab) ---
    bottom_panel = BottomPanel(tab_eingabe, grid, control_panel, text_view)
    bottom_panel.pack(fill="x", padx=10, pady=10)

    root.mainloop()
