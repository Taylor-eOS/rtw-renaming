#!/usr/bin/env python3
import re
import sys
import tty
import termios
from pathlib import Path

INPUT_FILE = Path("input.txt")
OUTPUT_FILE = Path("output.txt")
unit_re = re.compile(r"^(\s*)(\{[^}]+\})\s*(.+?)\s*$")

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
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

def process_line(line):
    match = unit_re.match(line)
    if not match:
        return line
    indent, key, name = match.groups()
    before, inside = split_name(name)
    if inside is None:
        selected = name.strip()
    else:
        print()
        print(key)
        selected = choose_name(before, inside)
    return f"{indent}{key}\t{selected}"

def main():
    lines = INPUT_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    output_lines = [process_line(line) for line in lines]
    OUTPUT_FILE.write_text("".join(output_lines), encoding="utf-8")

if __name__ == "__main__":
    main()
