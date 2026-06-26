#!/usr/bin/env python3
import re
from pathlib import Path

"""Renames the units in export_units to what's in the parenthesis."""

INPUT_FILE = Path("export_units.txt")
OUTPUT_FILE = Path("export_units_ed.txt")
unit_key_re = re.compile(r"^\s*\{[^}]+\}\s*(.+?)\s*$")

def extract_name(line):
    match = unit_key_re.match(line)
    return match.group(1).rstrip() if match else None

def transform_line(line):
    name = extract_name(line)
    if name is None:
        return line, None
    paren_match = re.search(r"\(([^()]*)\)\s*$", name)
    if not paren_match:
        return line, name
    key_match = re.match(r"^(\s*)(\{[^}]+\})", line)
    if not key_match:
        return line, None
    indent, key = key_match.groups()
    new_name = paren_match.group(1)
    return f"{indent}{key}\t{new_name}\n", None

def process_lines(lines):
    output_lines = []
    missing_parentheses = []
    for line in lines:
        new_line, missing = transform_line(line)
        output_lines.append(new_line)
        if missing is not None:
            missing_parentheses.append(missing)
    return output_lines, missing_parentheses

def main():
    lines = INPUT_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    output_lines, missing_parentheses = process_lines(lines)
    OUTPUT_FILE.write_text("".join(output_lines), encoding="utf-8")
    if missing_parentheses:
        print("Units without parentheses:")
        for name in missing_parentheses:
            print(f"  {name}")

if __name__ == "__main__":
    main()
