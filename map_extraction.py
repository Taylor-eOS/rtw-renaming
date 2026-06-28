import os
import math
from PIL import Image
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union
from areas import AREAS

input_filename = "map_regions.tga"
descr_regions_path = "descr_regions.txt"
txt_filename = "settlement_coordinates.txt"
html_filename = "settlement_map.html"
bg_image_filename = "map_background.png"
CLUSTER_THRESHOLD = 100

STATE = {
    "pixels": None,
    "width": 0,
    "height": 0,
    "img_object": None,
    "settlements": [],
    "valid_settlements": [],
    "rgb_to_settlement": {},
    "area_points": {},
    "html_lines": [],
    "disp_width": 0,
    "disp_height": 0,
    "scale": 4,
    "settlement_to_area": {}
}

def load_image_pixels():
    if not os.path.exists(input_filename):
        print(f"Error: {input_filename} not found.")
        return
    img = Image.open(input_filename).convert("RGB")
    STATE["img_object"] = img
    STATE["pixels"] = img.load()
    STATE["width"], STATE["height"] = img.size

def find_potential_settlements():
    for y in range(STATE["height"]):
        for x in range(STATE["width"]):
            r, g, b = STATE["pixels"][x, y]
            if r == 0 and g == 0 and b == 0:
                game_y = STATE["height"] - 1 - y
                STATE["settlements"].append((x, game_y, x, y))

def get_neighbor_pixels(orig_x, orig_y):
    neighbors = []
    if orig_x > 0:
        neighbors.append(STATE["pixels"][orig_x - 1, orig_y])
    if orig_x < STATE["width"] - 1:
        neighbors.append(STATE["pixels"][orig_x + 1, orig_y])
    if orig_y > 0:
        neighbors.append(STATE["pixels"][orig_x, orig_y - 1])
    if orig_y < STATE["height"] - 1:
        neighbors.append(STATE["pixels"][orig_x, orig_y + 1])
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

def filter_valid_settlements():
    for x, game_y, orig_x, orig_y in STATE["settlements"]:
        neighbors = get_neighbor_pixels(orig_x, orig_y)
        is_valid, region_color = determine_settlement_color(neighbors)
        if is_valid:
            STATE["valid_settlements"].append((x, game_y, region_color, orig_x, orig_y))
        else:
            print(f"Settlement at X: {x}, Y: {game_y} does not have enough matching neighbor colors.")

def write_coordinates_file():
    with open(txt_filename, "w") as f:
        for x, y, (r, g, b), _, _ in STATE["valid_settlements"]:
            f.write(f"{x} {y} {r} {g} {b}\n")

def generate_background_map():
    bg_img = STATE["img_object"].copy()
    bg_pixels = bg_img.load()
    for _, _, region_color, orig_x, orig_y in STATE["valid_settlements"]:
        bg_pixels[orig_x, orig_y] = region_color
    bg_img.save(bg_image_filename, "PNG")

def load_regions_dictionary():
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
                STATE["rgb_to_settlement"][rgb] = settlement_name

def get_html_boilerplate():
    STATE["html_lines"].extend([
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Settlement Map</title>",
        "<style>",
        "body { background-color: #ffffff; color: #000000; font-family: sans-serif; margin: 0; padding: 40px; }",
        f'.container {{ max-width: {STATE["disp_width"]}px; margin: 0 auto; }}',
        f'.map-canvas {{ position: relative; width: {STATE["disp_width"]}px; height: {STATE["disp_height"]}px; background-image: url(\'{bg_image_filename}\'); background-size: contain; background-repeat: no-repeat; border: 1px solid #000000; image-rendering: pixelated; }}',
        ".settlement { position: absolute; width: 6px; height: 6px; background-color: #000000; border-radius: 50%; transform: translate(-3px, 3px); cursor: pointer; }",
        ".settlement:hover { background-color: #ff0000; box-shadow: 0 0 8px #ff0000; z-index: 10; }",
        ".tooltip { visibility: hidden; background-color: #000000; color: #ffffff; padding: 4px 8px; border-radius: 4px; position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 11px; }",
        ".settlement:hover .tooltip { visibility: visible; }",
        "</style>",
        "</head>",
        "<body>",
        '<div class="container">',
        '<div class="map-canvas">'
    ])

def build_settlement_elements():
    for x, y, region_color, _, _ in STATE["valid_settlements"]:
        settlement_name = STATE["rgb_to_settlement"].get(region_color)
        if not settlement_name:
            print(f"Warning: No settlement found in text file for RGB {region_color} at X: {x}, Y: {y}")
            settlement_name = f"Unknown (RGB {region_color[0]} {region_color[1]} {region_color[2]})"
        left_pos = x * STATE["scale"]
        bottom_pos = y * STATE["scale"]
        svg_y = STATE["disp_height"] - bottom_pos
        if settlement_name in STATE["settlement_to_area"]:
            area_name = STATE["settlement_to_area"][settlement_name]
            if area_name not in STATE["area_points"]:
                STATE["area_points"][area_name] = []
            STATE["area_points"][area_name].append((left_pos, svg_y))
        STATE["html_lines"].append(f'        <div class="settlement" style="left: {left_pos}px; bottom: {bottom_pos}px;">')
        STATE["html_lines"].append(f'            <span class="tooltip">{settlement_name}<br>X: {x}, Y: {y}</span>')
        STATE["html_lines"].append('        </div>')

def cluster_points(points):
    if not points:
        return []
    n = len(points)
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            dx = points[i][0] - points[j][0]
            dy = points[i][1] - points[j][1]
            if dx * dx + dy * dy < CLUSTER_THRESHOLD * CLUSTER_THRESHOLD:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(points[i])
    return list(groups.values())

def mst_inter_cluster_edges(clusters):
    if len(clusters) <= 1:
        return []
    n = len(clusters)
    centroids = [(sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)) for c in clusters]
    in_mst = [False] * n
    min_dist = [float('inf')] * n
    nearest = [-1] * n
    in_mst[0] = True
    for j in range(1, n):
        dx = centroids[0][0] - centroids[j][0]
        dy = centroids[0][1] - centroids[j][1]
        min_dist[j] = dx * dx + dy * dy
        nearest[j] = 0
    idx_edges = []
    for _ in range(n - 1):
        best = min((j for j in range(n) if not in_mst[j]), key=lambda j: min_dist[j])
        in_mst[best] = True
        idx_edges.append((nearest[best], best))
        for j in range(n):
            if not in_mst[j]:
                dx = centroids[best][0] - centroids[j][0]
                dy = centroids[best][1] - centroids[j][1]
                d = dx * dx + dy * dy
                if d < min_dist[j]:
                    min_dist[j] = d
                    nearest[j] = best
    result = []
    for i, j in idx_edges:
        best_d = float('inf')
        p1_best, p2_best = centroids[i], centroids[j]
        for p1 in clusters[i]:
            for p2 in clusters[j]:
                dx = p1[0] - p2[0]
                dy = p1[1] - p2[1]
                d = dx * dx + dy * dy
                if d < best_d:
                    best_d = d
                    p1_best, p2_best = p1, p2
        result.append((p1_best, p2_best))
    return result

def geometry_to_svg_path(geom):
    if geom.is_empty:
        return ""
    if geom.geom_type == 'Polygon':
        polygons = [geom]
    elif geom.geom_type == 'MultiPolygon':
        polygons = list(geom.geoms)
    else:
        return ""
    path_segments = []
    for poly in polygons:
        ext_coords = list(poly.exterior.coords)
        if not ext_coords:
            continue
        path_segments.append(f"M {ext_coords[0][0]:.1f} {ext_coords[0][1]:.1f}")
        for x, y in ext_coords[1:]:
            path_segments.append(f"L {x:.1f} {y:.1f}")
        path_segments.append("Z")
        for interior in poly.interiors:
            int_coords = list(interior.coords)
            if not int_coords:
                continue
            path_segments.append(f"M {int_coords[0][0]:.1f} {int_coords[0][1]:.1f}")
            for x, y in int_coords[1:]:
                path_segments.append(f"L {x:.1f} {y:.1f}")
            path_segments.append("Z")
    return " ".join(path_segments)

def build_svg_elements():
    def point_segment_distance(px, py, ax, ay, bx, by):
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        cx = ax + t * dx
        cy = ay + t * dy
        return math.hypot(px - cx, py - cy)
    all_points = []
    for other_area, pts in STATE["area_points"].items():
        for p in pts:
            all_points.append((other_area, p))
    STATE["html_lines"].append(f'        <svg style="position: absolute; top: 0; left: 0; width: {STATE["disp_width"]}px; height: {STATE["disp_height"]}px; pointer-events: none;">')
    for area_name, points in STATE["area_points"].items():
        hue = abs(hash(area_name)) % 360
        fill_color = f"hsla({hue}, 80%, 50%, 0.15)"
        stroke_color = f"hsla({hue}, 80%, 50%, 0.9)"
        all_cx = sum(p[0] for p in points) / len(points)
        all_cy = sum(p[1] for p in points) / len(points)
        clusters = cluster_points(points)
        changed = True
        while changed and len(clusters) > 1:
            changed = False
            for i in range(len(clusters)):
                if changed:
                    break
                for j in range(i + 1, len(clusters)):
                    best_pair = None
                    best_dist = float("inf")
                    for p1 in clusters[i]:
                        for p2 in clusters[j]:
                            d = (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2
                            if d < best_dist:
                                best_dist = d
                                best_pair = (p1, p2)
                    p1, p2 = best_pair
                    blocked = False
                    for other_area, op in all_points:
                        if other_area == area_name:
                            continue
                        if point_segment_distance(op[0], op[1], p1[0], p1[1], p2[0], p2[1]) < 20:
                            blocked = True
                            break
                    if not blocked:
                        clusters[i].extend(clusters[j])
                        del clusters[j]
                        changed = True
                        break
        shapes_to_union = []
        for cluster in clusters:
            if len(cluster) >= 3:
                hull = unary_union([Point(p) for p in cluster]).convex_hull
                shapes_to_union.append(hull.buffer(15, join_style=1))
            elif len(cluster) == 2:
                shapes_to_union.append(LineString(cluster).buffer(15, join_style=1))
            else:
                shapes_to_union.append(Point(cluster[0]).buffer(15))
        if shapes_to_union:
            merged_shape = unary_union(shapes_to_union)
            changed = True
            while changed and not merged_shape.is_empty:
                changed = False
                for other_area, op in all_points:
                    if other_area == area_name:
                        continue
                    pt = Point(op)
                    if merged_shape.covers(pt):
                        merged_shape = merged_shape.difference(pt.buffer(18))
                        changed = True
            path_data = geometry_to_svg_path(merged_shape)
            if path_data:
                STATE["html_lines"].append(f'            <path d="{path_data}" style="fill:{fill_color};stroke:{stroke_color};stroke-width:2;fill-rule:evenodd;" />')
        display_name = area_name.removeprefix("local_")
        STATE["html_lines"].append(f'            <text x="{all_cx:.1f}" y="{all_cy:.1f}" fill="{stroke_color}" font-size="12px" font-weight="bold" text-anchor="middle" dominant-baseline="central">{display_name}</text>')
    STATE["html_lines"].append('        </svg>')

def generate_html_map():
    STATE["disp_width"] = STATE["width"] * STATE["scale"]
    STATE["disp_height"] = STATE["height"] * STATE["scale"]
    for area_name, settlements_list in AREAS.items():
        for s_name in settlements_list:
            STATE["settlement_to_area"][s_name] = area_name
    get_html_boilerplate()
    build_settlement_elements()
    build_svg_elements()
    STATE["html_lines"].extend([
        "    </div>",
        "</div>",
        "</body>",
        "</html>"
    ])
    with open(html_filename, "w") as f:
        f.write("\n".join(STATE["html_lines"]))

def generate_settlement_map():
    load_regions_dictionary()
    load_image_pixels()
    if STATE["pixels"] is None:
        return
    find_potential_settlements()
    if not STATE["settlements"]:
        print("No settlements found in the image.")
        return
    filter_valid_settlements()
    write_coordinates_file()
    if not STATE["valid_settlements"]:
        print("No valid settlements left to map.")
        return
    generate_background_map()
    generate_html_map()
    print("Files successfully generated.")

if __name__ == "__main__":
    generate_settlement_map()
