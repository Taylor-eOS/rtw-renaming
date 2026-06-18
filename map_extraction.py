import os
import math
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

def expand_polygon(hull, padding=15):
    if len(hull) < 3:
        return hull
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    expanded = []
    for x, y in hull:
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            expanded.append((x + (dx / dist) * padding, y + (dy / dist) * padding))
        else:
            expanded.append((x, y))
    return expanded

def is_point_in_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def get_html_boilerplate(disp_width, disp_height, bg_image_filename):
    return [
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

def build_settlement_elements(valid_settlements, rgb_to_settlement, settlement_to_area, scale, disp_height):
    html_lines = []
    area_points = {}
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
    return html_lines, area_points

def build_svg_elements(area_points, disp_width, disp_height):
    html_lines = [f'        <svg style="position: absolute; top: 0; left: 0; width: {disp_width}px; height: {disp_height}px; pointer-events: none;">']
    all_foreign_points = {}
    for name, pts in area_points.items():
        all_foreign_points[name] = [p for o_name, o_pts in area_points.items() if o_name != name for p in o_pts]
    for area_name, points in area_points.items():
        hull = calculate_convex_hull(points)
        if not hull:
            continue
        hue = abs(hash(area_name)) % 360
        stroke_color = f"hsla({hue}, 80%, 50%, 0.8)"
        fill_color = f"hsla({hue}, 80%, 50%, 0.2)"
        cx = sum(p[0] for p in hull) / len(hull)
        cy = sum(p[1] for p in hull) / len(hull)
        if len(hull) > 2:
            hull = expand_polygon(hull, padding=15)
            foreign_pts = all_foreign_points.get(area_name, [])
            for fx, fy in foreign_pts:
                if is_point_in_polygon(fx, fy, hull):
                    min_dist = float('inf')
                    insert_idx = 0
                    for i in range(len(hull)):
                        p1 = hull[i]
                        p2 = hull[(i + 1) % len(hull)]
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        if dx == 0 and dy == 0:
                            dist = math.sqrt((fx - p1[0])**2 + (fy - p1[1])**2)
                        else:
                            t = ((fx - p1[0]) * dx + (fy - p1[1]) * dy) / (dx * dx + dy * dy)
                            t = max(0, min(1, t))
                            closest_x = p1[0] + t * dx
                            closest_y = p1[1] + t * dy
                            dist = math.sqrt((fx - closest_x)**2 + (fy - closest_y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            insert_idx = i + 1
                    dcx = cx - fx
                    dcy = cy - fy
                    dc_dist = math.sqrt(dcx * dcx + dcy * dcy)
                    if dc_dist > 0:
                        ix = fx + (dcx / dc_dist) * 15
                        iy = fy + (dcy / dc_dist) * 15
                    else:
                        ix, iy = fx, fy
                    hull.insert(insert_idx, (ix, iy))
            path_segments = []
            for i in range(len(hull)):
                p0 = hull[i - 1]
                p1 = hull[i]
                p2 = hull[(i + 1) % len(hull)]
                v1x, v1y = p1[0] - p0[0], p1[1] - p0[1]
                v2x, v2y = p2[0] - p1[0], p2[1] - p1[1]
                d1 = math.sqrt(v1x * v1x + v1y * v1y)
                d2 = math.sqrt(v2x * v2x + v2y * v2y)
                r = 12
                r1 = min(r, d1 / 2) if d1 > 0 else 0
                r2 = min(r, d2 / 2) if d2 > 0 else 0
                start_x = p1[0] - (v1x / d1) * r1 if d1 > 0 else p1[0]
                start_y = p1[1] - (v1y / d1) * r1 if d1 > 0 else p1[1]
                end_x = p1[0] + (v2x / d2) * r2 if d2 > 0 else p1[0]
                end_y = p1[1] + (v2y / d2) * r2 if d2 > 0 else p1[1]
                if i == 0:
                    path_segments.append(f"M {start_x} {start_y}")
                else:
                    path_segments.append(f"L {start_x} {start_y}")
                path_segments.append(f"Q {p1[0]} {p1[1]}, {end_x} {end_y}")
            path_data = " ".join(path_segments) + " Z"
            html_lines.append(f'            <path d="{path_data}" style="fill:{fill_color};stroke:{stroke_color};stroke-width:2" />')
        elif len(hull) == 2:
            html_lines.append(f'            <line x1="{hull[0][0]}" y1="{hull[0][1]}" x2="{hull[1][0]}" y2="{hull[1][1]}" style="stroke:{stroke_color};stroke-width:2" />')
        display_name = area_name.removeprefix("local_")
        html_lines.append(f'            <text x="{cx}" y="{cy}" fill="{stroke_color}" font-size="12px" font-weight="bold" text-anchor="middle" dominant-baseline="central">{display_name}</text>')
    html_lines.append('        </svg>')
    return html_lines

def generate_html_map(html_filename, bg_image_filename, valid_settlements, width, height, rgb_to_settlement):
    scale = 4
    disp_width = width * scale
    disp_height = height * scale
    settlement_to_area = {}
    for area_name, settlements_list in AREAS.items():
        for s_name in settlements_list:
            settlement_to_area[s_name] = area_name
    html_lines = get_html_boilerplate(disp_width, disp_height, bg_image_filename)
    settlement_html, area_points = build_settlement_elements(valid_settlements, rgb_to_settlement, settlement_to_area, scale, disp_height)
    html_lines.extend(settlement_html)
    html_lines.extend(build_svg_elements(area_points, disp_width, disp_height))
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
