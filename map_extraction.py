import os
from PIL import Image
from areas import AREAS

input_filename = "map_regions.tga"
txt_filename = "settlement_coordinates.txt"
html_filename = "settlement_map.html"
bg_image_filename = "map_background.png"
descr_regions_path = "descr_regions.txt"

def load_image_pixels(input_filename):
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return None, 0, 0, None
    img = Image.open(input_filename).convert("RGB")
    return img.load(), img.size[0], img.size[1], img

def find_potential_settlements(pixels, width, height):
    settlements = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if r == 0 and g == 0 and b == 0:
                game_y = height - 1 - y
                settlements.append((x, game_y, x, y))
    return settlements

def get_neighbor_pixels(pixels, orig_x, orig_y, width, height):
    neighbors = []
    if orig_x > 0:
        neighbors.append(pixels[orig_x - 1, orig_y])
    if orig_x < width - 1:
        neighbors.append(pixels[orig_x + 1, orig_y])
    if orig_y > 0:
        neighbors.append(pixels[orig_x, orig_y - 1])
    if orig_y < height - 1:
        neighbors.append(pixels[orig_x, orig_y + 1])
    return neighbors

def determine_settlement_color(neighbors):
    water_color = (41, 140, 233)
    land_neighbors = [c for c in neighbors if c != (0, 0, 0) and c != water_color]
    if not land_neighbors:
        return False, (0, 0, 0)
    color_counts = {}
    for color in land_neighbors:
        color_counts[color] = color_counts.get(color, 0) + 1
    sorted_colors = sorted(color_counts.items(), key=lambda item: item[1], reverse=True)
    top_color, top_count = sorted_colors[0]
    if top_count >= 2 or len(neighbors) - neighbors.count(water_color) - neighbors.count((0, 0, 0)) == 1:
        return True, top_color
    return False, top_color

def filter_valid_settlements(settlements, pixels, width, height):
    valid_settlements = []
    for x, game_y, orig_x, orig_y in settlements:
        neighbors = get_neighbor_pixels(pixels, orig_x, orig_y, width, height)
        is_valid, region_color = determine_settlement_color(neighbors)
        if is_valid:
            valid_settlements.append((x, game_y, region_color, orig_x, orig_y))
        else:
            print(f"Settlement at X: {x}, Y: {game_y} does not have enough matching neighbor colors.")
    return valid_settlements

def write_coordinates_file(txt_filename, valid_settlements):
    with open(txt_filename, "w") as f:
        for x, y, (r, g, b), _, _ in valid_settlements:
            f.write(f"{x} {y} {r} {g} {b}\n")

def generate_background_map(img_object, valid_settlements, output_bg_filename):
    bg_img = img_object.copy()
    bg_pixels = bg_img.load()
    for _, _, region_color, orig_x, orig_y in valid_settlements:
        bg_pixels[orig_x, orig_y] = region_color
    bg_img.save(output_bg_filename, "PNG")

def load_regions_dictionary(descr_regions_path):
    rgb_to_settlement = {}
    if not os.path.exists(descr_regions_path):
        return rgb_to_settlement
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
                rgb_to_settlement[rgb] = settlement_name
    return rgb_to_settlement

def calculate_convex_hull(points):
    if len(points) <= 1:
        return points
    points = sorted(set(points))
    lower = []
    for p in points:
        while len(lower) >= 2 and (lower[-1][0] - lower[-2][0]) * (p[1] - lower[-2][1]) - (lower[-1][1] - lower[-2][1]) * (p[0] - lower[-2][0]) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and (upper[-1][0] - upper[-2][0]) * (p[1] - upper[-2][1]) - (upper[-1][1] - upper[-2][1]) * (p[0] - upper[-2][0]) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]

def generate_html_map(html_filename, bg_image_filename, valid_settlements, width, height, rgb_to_settlement):
    scale = 4
    disp_width = width * scale
    disp_height = height * scale
    settlement_to_area = {}
    for area_name, settlements_list in AREAS.items():
        for s_name in settlements_list:
            settlement_to_area[s_name] = area_name
    area_points = {}
    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Settlement Map</title>",
        "<style>",
        "body { background-color: #ffffff; color: #000000; font-family: sans-serif; margin: 0; padding: 40px; }",
        f".container {{ max-width: {disp_width}px; margin: 0 auto; }}",
        f".map-canvas {{ position: relative; width: {disp_width}px; height: {disp_height}px; background-image: url('{bg_image_filename}'); background-size: contain; background-repeat: no-repeat; border: 1px solid #000000; image-rendering: pixelated; }}",
        ".settlement { position: absolute; width: 6px; height: 6px; background-color: #000000; border-radius: 50%; transform: translate(-3px, 3px); cursor: pointer; }",
        ".settlement:hover { background-color: #ff0000; box-shadow: 0 0 8px #ff0000; z-index: 10; }",
        ".tooltip { visibility: hidden; background-color: #000000; color: #ffffff; padding: 4px 8px; border-radius: 4px; position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 11px; }",
        ".settlement:hover .tooltip { visibility: visible; }",
        "</style>",
        "</head>",
        "<body>",
        '<div class="container">',
        '<div class="map-canvas">'
    ]
    for idx, (x, y, region_color, _, _) in enumerate(valid_settlements):
        settlement_name = rgb_to_settlement.get(region_color)
        if not settlement_name:
            print(f"Warning: No settlement found in text file for RGB {region_color} at X: {x}, Y: {y}")
            settlement_name = f"Unknown (RGB {region_color[0]} {region_color[1]} {region_color[2]})"
        left_pos = x * scale
        bottom_pos = y * scale
        svg_y = disp_height - bottom_pos
        if settlement_name in settlement_to_area:
            area_name = settlement_to_area[settlement_name]
            if area_name not in area_points:
                area_points[area_name] = []
            area_points[area_name].append((left_pos, svg_y))
        html_lines.append(f'        <div class="settlement" style="left: {left_pos}px; bottom: {bottom_pos}px;">')
        html_lines.append(f'            <span class="tooltip">{settlement_name}<br>X: {x}, Y: {y}</span>')
        html_lines.append('        </div>')
    html_lines.append(f'        <svg style="position: absolute; top: 0; left: 0; width: {disp_width}px; height: {disp_height}px; pointer-events: none;">')
    for area_name, points in area_points.items():
        hull = calculate_convex_hull(points)
        if not hull:
            continue
        hue = abs(hash(area_name)) % 360
        stroke_color = f"hsla({hue}, 80%, 50%, 0.8)"
        fill_color = f"hsla({hue}, 80%, 50%, 0.2)"
        if len(hull) > 2:
            points_str = " ".join(f"{px},{py}" for px, py in hull)
            html_lines.append(f'            <polygon points="{points_str}" style="fill:{fill_color};stroke:{stroke_color};stroke-width:2" />')
        elif len(hull) == 2:
            html_lines.append(f'            <line x1="{hull[0][0]}" y1="{hull[0][1]}" x2="{hull[1][0]}" y2="{hull[1][1]}" style="stroke:{stroke_color};stroke-width:2" />')
    html_lines.append('        </svg>')
    html_lines.extend([
        "    </div>",
        "</div>",
        "</body>",
        "</html>"
    ])
    with open(html_filename, "w") as f:
        f.write("\n".join(html_lines))

def generate_settlement_map():
    rgb_to_settlement = load_regions_dictionary(descr_regions_path)
    pixels, width, height, img_object = load_image_pixels(input_filename)
    if pixels is None:
        return
    settlements = find_potential_settlements(pixels, width, height)
    if not settlements:
        print("No settlements found in the image.")
        return
    valid_settlements = filter_valid_settlements(settlements, pixels, width, height)
    write_coordinates_file(txt_filename, valid_settlements)
    if not valid_settlements:
        print("No valid settlements left to map.")
        return
    generate_background_map(img_object, valid_settlements, bg_image_filename)
    generate_html_map(html_filename, bg_image_filename, valid_settlements, width, height, rgb_to_settlement)
    print("Files successfully generated.")

if __name__ == "__main__":
    generate_settlement_map()
