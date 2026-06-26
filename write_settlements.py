import sys

"""Writes the second line from descr_regions (settlement names) into a new file."""

INPUT_FILE = "descr_regions.txt"

def extract_settlements(input_path, output_path):
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: The file {input_path} does not exist.")
        sys.exit(1)
    settlements = []
    block_line_count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            block_line_count = 0
            continue
        block_line_count += 1
        if block_line_count == 2:
            settlements.append(stripped)
    with open(output_path, "w", encoding="utf-8") as f:
        for settlement in settlements:
            f.write(settlement + "\n")
    print("Done")

if __name__ == "__main__":
    extract_settlements(INPUT_FILE, "settlements.txt")
