import os
import re
import sys

def load_regions_dictionary(descr_regions_path):
    region_to_settlement = {}
    if not os.path.exists(descr_regions_path):
        print(f"Error: {descr_regions_path} not found.")
        sys.exit(1)
    with open(descr_regions_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip() and not line.strip().startswith(';')]
        if len(lines) >= 2:
            region_name = lines[0]
            settlement_name = lines[1]
            region_to_settlement[region_name] = settlement_name
    return region_to_settlement

def load_input_areas(regions_list_path):
    if not os.path.exists(regions_list_path):
        print(f"Error: {regions_list_path} not found.")
        sys.exit(1)
    with open(regions_list_path, "r", encoding="utf-8") as f:
        content = f.read()
    areas = {}
    pattern = r'"([^"]+)":\s*\[(.*?)\]'
    matches = re.findall(pattern, content, re.DOTALL)
    for area_name, regions_str in matches:
        regions = [r.strip().strip('"') for r in regions_str.split(',') if r.strip()]
        areas[area_name] = regions
    return areas

def convert_regions_to_settlements():
    descr_regions_path = "descr_regions.txt"
    regions_list_path = "regions_list.txt"
    output_path = "settlements_list.txt"
    region_map = load_regions_dictionary(descr_regions_path)
    input_areas = load_input_areas(regions_list_path)
    output_lines = []
    missing_regions = []
    for area_name, regions in input_areas.items():
        settlements = []
        for region in regions:
            if region in region_map:
                settlements.append(f'"{region_map[region]}"')
            else:
                missing_regions.append((area_name, region))
        settlements_str = ", ".join(settlements)
        output_lines.append(f'    "{area_name}": [{settlements_str}],')
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    print(f"Conversion complete. Output written to {output_path}")
    if missing_regions:
        print("\n[WARNING] The following regions were not found in descr_regions.txt:")
        for area, reg in missing_regions:
            print(f"  - In area '{area}': '{reg}'")
    else:
        print("\nAll regions successfully matched to their respective settlements.")

if __name__ == "__main__":
    convert_regions_to_settlements()
