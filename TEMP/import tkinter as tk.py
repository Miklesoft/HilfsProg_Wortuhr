import tkinter as tk
from tkinter import ttk

# --- LetterGrid Klasse (wie vorher) ---
class LetterGrid(ttk.Frame):
    def __init__(self, master, rows=11, cols=10):
        super().__init__(master)
        self.rows = rows
        self.cols = cols
        self.entries = [[None for _ in range(cols)] for _ in range(rows)]
        self.create_grid()

    def create_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell_frame = tk.Frame(self, bg="black", bd=0)
                cell_frame.grid(row=r, column=c, padx=1, pady=1)
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
                    return

    def select_cell(self, event):
        widget = event.widget
        widget.focus()
        widget.select_range(0, tk.END)
        return "break"

    def get_cell(self, row, col):
        text = self.entries[row][col].get()
        if text != "":
            return True, text
        else:
            return False, None

# --- Steuer-Frame Klasse ---
class ControlPanel(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.create_widgets()

    def create_widgets(self):
        # 24 Label-Felder
        label_frame = ttk.LabelFrame(self, text="Labels")
        label_frame.pack(pady=10, padx=10, fill="x")
        for i in range(24):
            lbl = ttk.Label(label_frame, text=f"Label {i+1}", width=10, anchor="center")
            lbl.grid(row=i//4, column=i%4, padx=2, pady=2)

        # 3 Radiobuttons
        radio_frame = ttk.LabelFrame(self, text="Optionen")
        radio_frame.pack(pady=10, padx=10, fill="x")
        self.radio_var = tk.StringVar(value="1")
        for i in range(3):
            rb = ttk.Radiobutton(radio_frame, text=f"Radio {i+1}", variable=self.radio_var, value=str(i+1))
            rb.pack(anchor="w", pady=2)

        # 4 Checkbuttons
        check_frame = ttk.LabelFrame(self, text="Kontrolle")
        check_frame.pack(pady=10, padx=10, fill="x")
        self.check_vars = []
        for i in range(4):
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(check_frame, text=f"Check {i+1}", variable=var)
            cb.pack(anchor="w", pady=2)
            self.check_vars.append(var)


# --- Hauptprogramm ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Grid + Steuerpanel")
    root.configure(bg="#ADD8E6")  # hellblauer Hintergrund

    # Hauptframe für nebeneinander Anordnung
    main_frame = tk.Frame(root, bg="#ADD8E6")
    main_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Links: ControlPanel
    control_panel = ControlPanel(main_frame)
    control_panel.pack(side="left", fill="y", padx=10, pady=10)

    # Rechts: LetterGrid
    grid = LetterGrid(main_frame, rows=11, cols=10)
    grid.pack(side="left", padx=10, pady=10)

    root.mainloop()
