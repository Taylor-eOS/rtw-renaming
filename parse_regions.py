from collections import defaultdict

INPUT_FILE = "descr_regions.txt"

groups = defaultdict(list)
missing_local = []
with open(INPUT_FILE, encoding="utf-8") as f:
    lines = [line.strip() for line in f]
block = []
for line in lines + [""]:
    if line:
        block.append(line)
    elif block:
        region = block[0]
        local_region = None
        for entry in block:
            for item in map(str.strip, entry.split(",")):
                if item.startswith("local_"):
                    local_region = item
                    break
            if local_region:
                break
        if local_region:
            groups[local_region].append(region)
        else:
            missing_local.append(region)
        block = []
for local_region in sorted(groups):
    print(f"{local_region}:")
    for region in sorted(groups[local_region]):
        print(f"    {region}")
    print()
if missing_local:
    print("NO LOCAL REGION:")
    for region in sorted(missing_local):
        print(f"    {region}")
