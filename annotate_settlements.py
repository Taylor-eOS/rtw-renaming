import os

"""Updates the regions list with coordinates."""

descr_regions_path = "descr_regions.txt"
txt_filename = "settlement_coordinates.txt"

def load_regions_dictionary(descr_regions_path):
    rgb_to_names = {}
    if not os.path.exists(descr_regions_path):
        print(f"Error: {descr_regions_path} not found.")
        return rgb_to_names
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
                region_name = valid_lines[i - 4]
                settlement_name = valid_lines[i - 3]
                rgb = (int(parts[0]), int(parts[1]), int(parts[2]))
                rgb_to_names[rgb] = (region_name, settlement_name)
    return rgb_to_names

def update_coordinates_file(txt_filename, rgb_to_names):
    if not os.path.exists(txt_filename):
        print(f"Error: {txt_filename} not found.")
        return
    updated_lines = []
    with open(txt_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5:
            x, y, r, g, b = parts[:5]
            try:
                rgb = (int(r), int(g), int(b))
                if rgb in rgb_to_names:
                    region, settlement = rgb_to_names[rgb]
                    updated_lines.append(f"{x} {y} {r} {g} {b} {region} {settlement}\n")
                else:
                    print(f"Warning: RGB {rgb} at X: {x}, Y: {y} not found in regions dictionary.")
                    updated_lines.append(f"{x} {y} {r} {g} {b} Unknown_Region Unknown_Settlement\n")
            except ValueError:
                print(f"Error: Invalid RGB values found in line: {line.strip()}")
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

def main():
    rgb_to_names = load_regions_dictionary(descr_regions_path)
    if not rgb_to_names:
        print("Regions dictionary data is unavailable. Aborting update.")
        return
    update_coordinates_file(txt_filename, rgb_to_names)
    print("Coordinates file successfully updated.")

if __name__ == "__main__":
    main()
