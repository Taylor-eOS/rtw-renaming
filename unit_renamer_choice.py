#!/usr/bin/env python3
import re
import sys
import tty
import termios
from pathlib import Path

"""Renames the units in export_units to what's in the parenthesis."""

INPUT_FILE = Path("export_units.txt")
OUTPUT_FILE = Path("export_units_ed.txt")
unit_re = re.compile(r"^(\s*)(\{[^}]+\})\s*(.+?)\s*$")

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x03":
            raise KeyboardInterrupt
        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def split_name(name):
    match = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", name)
    if not match:
        return None, None
    return match.group(1).strip(), match.group(2).strip()

def choose_name(before, inside):
    print(f"1: {inside}")
    print(f"2: {before}")
    while True:
        key = get_key()
        if key == "1":
            return inside
        if key == "2":
            return before
        if key.lower() == "b":
            print(" -> back")
            return None

def main():
    lines = INPUT_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    output_lines = []
    processed_indices = []
    i = 0
    try:
        while i < len(lines):
            line = lines[i]
            match = unit_re.match(line)
            if not match:
                output_lines.append(line)
                processed_indices.append(i)
                i += 1
                continue
            indent, key, name = match.groups()
            before, inside = split_name(name)
            if inside is None:
                output_lines.append(f"{indent}{key}\t{name.strip()}")
                processed_indices.append(i)
                i += 1
                continue
            print()
            print(key)
            selected = choose_name(before, inside)
            if selected is None:
                if processed_indices:
                    i = processed_indices.pop()
                    output_lines.pop()
                continue
            output_lines.append(f"{indent}{key}\t{selected}\n")
            processed_indices.append(i)
            i += 1
        OUTPUT_FILE.write_text("".join(output_lines), encoding="utf-8")
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)

if __name__ == "__main__":
    main()
