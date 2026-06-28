import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import colorsys
import random
import areas

SCALE = 4
STATE = {
    "root": None,
    "canvas": None,
    "photo": None,
    "rgb_to_settlement": {},
    "settlements": [],
    "display_width": 0,
    "display_height": 0
}

def random_area_colors():
    result = {}
    for area in areas.AREAS:
        h = random.random()
        s = random.uniform(0.55, 0.95)
        v = random.uniform(0.55, 0.90)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        result[area] = (int(r * 255), int(g * 255), int(b * 255))
    return result

def load_settlement_data():
    if not os.path.exists("settlement_coordinates.txt"):
        return
    with open("settlement_coordinates.txt", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                x = int(parts[0])
                y = int(parts[1])
                r = int(parts[2])
                g = int(parts[3])
                b = int(parts[4])
                STATE["settlements"].append((x, y, (r, g, b)))

def load_regions_dictionary():
    if not os.path.exists("descr_regions.txt"):
        return
    with open("descr_regions.txt", "r", encoding="utf-8", errors="ignore") as f:
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
                STATE["rgb_to_settlement"][rgb] = settlement_name

def setup_ui():
    STATE["root"] = tk.Tk()
    STATE["root"].title("Region Viewer")
    STATE["canvas"] = tk.Canvas(STATE["root"], bg="#f0f0f0")
    STATE["canvas"].pack(fill=tk.BOTH, expand=True)

def recolor_image(image):
    pixels = image.load()
    width, height = image.size
    settlement_to_area = {}
    for area, settlements in areas.AREAS.items():
        for s in settlements:
            settlement_to_area[s] = area
    rgb_to_area = {}
    color_map = {}
    for rgb, settlement_name in STATE["rgb_to_settlement"].items():
        area = settlement_to_area.get(settlement_name)
        if area:
            rgb_to_area[rgb] = area
        else:
            color_map[rgb] = (64, 64, 64)
    area_colors = random_area_colors()
    for rgb, area in rgb_to_area.items():
        color_map[rgb] = area_colors[area]
    for y in range(height):
        for x in range(width):
            current_rgb = pixels[x, y]
            if current_rgb in color_map:
                pixels[x, y] = color_map[current_rgb]
    for x, y, rgb in STATE["settlements"]:
        py = height - 1 - y
        if rgb in color_map and 0 <= x < width and 0 <= py < height:
            pixels[x, py] = color_map[rgb]
    white_pixels = [(x, y) for y in range(height) for x in range(width) if pixels[x, y] == (255, 255, 255)]
    changed = True
    while changed and white_pixels:
        changed = False
        remaining = []
        for x, y in white_pixels:
            counts = {}
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        c = pixels[nx, ny]
                        if c != (255, 255, 255):
                            counts[c] = counts.get(c, 0) + 1
            if counts:
                pixels[x, y] = max(counts, key=counts.get)
                changed = True
            else:
                remaining.append((x, y))
        white_pixels = remaining
    return image

def draw_area_labels(bg_height):
    settlement_coords = {}
    for x, y, rgb in STATE["settlements"]:
        name = STATE["rgb_to_settlement"].get(rgb)
        if name:
            settlement_coords[name] = (x, y)
    area_points = {}
    for area, settlements in areas.AREAS.items():
        coords = [settlement_coords[s] for s in settlements if s in settlement_coords]
        if coords:
            area_points[area] = coords
    for area, coords in area_points.items():
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        canvas_x = cx * SCALE
        canvas_y = (bg_height - 1 - cy) * SCALE
        STATE["canvas"].create_text(
            canvas_x, canvas_y,
            text=area,
            fill="white",
            font=("Arial", 8, "bold"),
            anchor=tk.CENTER
        )

def load_background():
    if not os.path.exists("map_background.png"):
        messagebox.showerror("Error", "map_background.png not found!")
        return
    bg_image = Image.open("map_background.png").convert("RGB")
    bg_image = recolor_image(bg_image)
    bg_width, bg_height = bg_image.size
    STATE["display_width"] = bg_width * SCALE
    STATE["display_height"] = bg_height * SCALE
    display_image = bg_image.resize((STATE["display_width"], STATE["display_height"]), Image.NEAREST)
    STATE["photo"] = ImageTk.PhotoImage(display_image)
    STATE["canvas"].config(width=STATE["display_width"], height=STATE["display_height"])
    STATE["canvas"].create_image(0, 0, anchor=tk.NW, image=STATE["photo"])
    STATE["root"].geometry(f"{STATE['display_width']}x{STATE['display_height']}")
    draw_area_labels(bg_height)

def main():
    setup_ui()
    load_settlement_data()
    load_regions_dictionary()
    if not STATE["rgb_to_settlement"]:
        messagebox.showerror("Error", "No region data found!")
        STATE["root"].destroy()
        return
    load_background()
    STATE["root"].mainloop()

if __name__ == "__main__":
    main()
