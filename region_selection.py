import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

settlement_file = "settlement_coordinates.txt"
background_image = "map_background.png"
descr_regions_path = "descr_regions.txt"
SCALE = 4
MARKER_RADIUS = 6
HIT_RADIUS = 18

class SettlementSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Region Selection")
        self.settlements = []
        self.rgb_to_settlement = {}
        self.selected_settlements = []
        self.copied_settlements = set()
        self.settlement_regions = []
        self.load_settlement_data()
        self.load_regions_dictionary()
        if not self.settlements:
            messagebox.showerror("Error", "No settlement data found!")
            root.destroy()
            return
        self.create_widgets()
        self.load_background()
        self.draw_settlements()

    def load_settlement_data(self):
        if not os.path.exists(settlement_file):
            messagebox.showerror("Error", f"{settlement_file} not found!")
            return
        with open(settlement_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    x = int(parts[0])
                    y = int(parts[1])
                    r = int(parts[2])
                    g = int(parts[3])
                    b = int(parts[4])
                    self.settlements.append((x, y, (r, g, b)))

    def load_regions_dictionary(self):
        if not os.path.exists(descr_regions_path):
            return
        with open(descr_regions_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f]
        valid_lines = []
        for line in lines:
            cleaned = "".join(c for c in line if ord(c) != 160).strip()
            if cleaned and not cleaned.startswith(";"):
                valid_lines.append(cleaned)
        for i in range(len(valid_lines)):
            parts = valid_lines[i].split()
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                if i >= 4:
                    settlement_name = valid_lines[i - 3]
                    rgb = (int(parts[0]), int(parts[1]), int(parts[2]))
                    self.rgb_to_settlement[rgb] = settlement_name

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, bg='#f0f0f0')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_panel = tk.Frame(main_frame, width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        tk.Label(right_panel, text="Click settlements to select/deselect.\nPress 'Copy Selection' when done.",
                font=("Arial", 10, "bold"), pady=10, wraplength=280).pack()
        self.listbox = tk.Listbox(right_panel, width=40, height=20)
        self.listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(right_panel)
        button_frame.pack(pady=10, padx=10, fill=tk.X)
        tk.Button(button_frame, text="Copy Selection",
                 command=self.copy_selection).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="Clear Selection",
                 command=self.clear_selection).pack(fill=tk.X, pady=2)
        self.status_label = tk.Label(right_panel, text="Ready", fg="gray")
        self.status_label.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

    def load_background(self):
        if not os.path.exists(background_image):
            messagebox.showerror("Error", f"{background_image} not found!")
            return
        self.bg_image = Image.open(background_image)
        bg_width, bg_height = self.bg_image.size
        self.display_width = bg_width * SCALE
        self.display_height = bg_height * SCALE
        display_image = self.bg_image.resize((self.display_width, self.display_height),Image.NEAREST)
        self.photo = ImageTk.PhotoImage(display_image)
        self.canvas.config(width=self.display_width, height=self.display_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.root.geometry(f"{self.display_width + 320}x{self.display_height + 50}")

    def draw_settlements(self):
        self.settlement_regions = []
        for x, y, rgb in self.settlements:
            canvas_x = x * SCALE
            canvas_y = self.display_height - (y * SCALE)
            if rgb in self.copied_settlements:
                fill_color = '#404040'
            else:
                fill_color = self._rgb_to_hex(rgb)
            region = self.canvas.create_rectangle(
                canvas_x - MARKER_RADIUS, canvas_y - MARKER_RADIUS,
                canvas_x + MARKER_RADIUS, canvas_y + MARKER_RADIUS,
                fill=fill_color, outline='white', width=1,
                tags=('settlement',)
            )
            self.settlement_regions.append((region, (x, y, rgb)))
        self.canvas.tag_bind('settlement', '<Enter>',
                           lambda e: self.canvas.config(cursor='hand2'))
        self.canvas.tag_bind('settlement', '<Leave>',
                           lambda e: self.canvas.config(cursor=''))

    def get_settlement_name(self, rgb):
        return self.rgb_to_settlement.get(rgb, f"Unknown ({rgb[0]},{rgb[1]},{rgb[2]})")

    def _rgb_to_hex(self, rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def on_click(self, event):
        closest = None
        min_distance = float('inf')
        for region, (x, y, rgb) in self.settlement_regions:
            canvas_x = x * SCALE
            canvas_y = self.display_height - (y * SCALE)
            distance = ((event.x - canvas_x) ** 2 + (event.y - canvas_y) ** 2) ** 0.5
            if distance < HIT_RADIUS and distance < min_distance:
                closest = (region, (x, y, rgb))
                min_distance = distance
        if closest:
            region, (x, y, rgb) = closest
            if rgb in self.selected_settlements:
                self.selected_settlements.remove(rgb)
                self.canvas.itemconfig(region, outline='white', width=1)
                self.status_label.config(text=f"Deselected: {self.get_settlement_name(rgb)}")
            else:
                self.selected_settlements.append(rgb)
                self.canvas.itemconfig(region, outline='yellow', width=3)
                self.status_label.config(text=f"Selected: {self.get_settlement_name(rgb)}")
            self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for rgb in self.selected_settlements:
            name = self.get_settlement_name(rgb)
            self.listbox.insert(tk.END, name)

    def copy_selection(self):
        if not self.selected_settlements:
            self.status_label.config(text="No settlements selected")
            return
        names = [f'"{self.get_settlement_name(rgb)}"' for rgb in self.selected_settlements]
        output = '    "region": [' + ", ".join(names) + '],'
        self.root.clipboard_clear()
        self.root.clipboard_append(output)
        for rgb in self.selected_settlements:
            self.copied_settlements.add(rgb)
        self.status_label.config(text=f"Copied {len(self.selected_settlements)} settlements to clipboard!")
        self.update_marker_colors()
        self.clear_selection()

    def update_marker_colors(self):
        for region, (x, y, rgb) in self.settlement_regions:
            if rgb in self.copied_settlements:
                self.canvas.itemconfig(region, fill='#404040')
            else:
                self.canvas.itemconfig(region, fill=self._rgb_to_hex(rgb))

    def clear_selection(self):
        for region, (x, y, rgb) in self.settlement_regions:
            if rgb in self.selected_settlements:
                self.canvas.itemconfig(region, outline='white', width=1)
        self.selected_settlements.clear()
        self.listbox.delete(0, tk.END)
        self.status_label.config(text="Selection cleared")

def main():
    root = tk.Tk()
    app = SettlementSelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()
