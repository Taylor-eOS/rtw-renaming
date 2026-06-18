import os
from PIL import Image


def load_image_pixels(input_filename):
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return None, 0, 0
    with Image.open(input_filename) as img:
        img = img.convert("RGB")
        return img.load(), img.size[0], img.size[1]


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
            valid_settlements.append((x, game_y, region_color))
        else:
            print(f"Settlement at X: {x}, Y: {game_y} does not have enough matching neighbor colors.")
    return valid_settlements


def write_coordinates_file(txt_filename, valid_settlements):
    with open(txt_filename, "w") as f:
        for x, y, (r, g, b) in valid_settlements:
            f.write(f"{x}, {y}, {r}, {g}, {b}\n")


def generate_html_map(html_filename, valid_settlements, width, height):
    scale = 4
    disp_width = width * scale
    disp_height = height * scale
    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Settlement Map</title>",
        "<style>",
        "body { background-color: #ffffff; color: #000000; font-family: sans-serif; margin: 0; padding: 40px; }",
        f".container {{ max-width: {disp_width}px; margin: 0 auto; }}",
        f".map-canvas {{ position: relative; width: {disp_width}px; height: {disp_height}px; background-color: #ffffff; border: 1px solid #000000; }}",
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
    for idx, (x, y, _) in enumerate(valid_settlements):
        left_pos = x * scale
        bottom_pos = y * scale
        html_lines.append(f'        <div class="settlement" style="left: {left_pos}px; bottom: {bottom_pos}px;">')
        html_lines.append(f'            <span class="tooltip">Settlement #{idx+1}<br>X: {x}, Y: {y}</span>')
        html_lines.append('        </div>')
    html_lines.extend([
        "    </div>",
        "</div>",
        "</body>",
        "</html>"
    ])
    with open(html_filename, "w") as f:
        f.write("\n".join(html_lines))


def generate_settlement_map():
    input_filename = "map_regions.tga"
    txt_filename = "settlement_coordinates.txt"
    html_filename = "settlement_map.html"
    pixels, width, height = load_image_pixels(input_filename)
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
    generate_html_map(html_filename, valid_settlements, width, height)
    print("Files successfully generated.")


if __name__ == "__main__":
    generate_settlement_map()
