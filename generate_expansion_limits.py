import sys
from areas import AREAS, BANNED_IN_AREAS

def generate_area_ban_script():
    output = []
    #output.append("monitor_event ScenarioTurnStart TrueCondition")
    for area, settlements in AREAS.items():
        banned_factions = BANNED_IN_AREAS.get(area, [])
        if not banned_factions:
            continue
        for settlement in settlements:
            output.append(f"    ; --- {settlement} ---")
            for faction in banned_factions:
                output.append(f"    if I_SettlementOwner {settlement} = {faction}")
                output.append(f"        console_command sudo capture_settlement {settlement} slave")
                output.append(f"        console_command create_unit {settlement} \"barb infantry slave\" 5 5 5 5")
                output.append("    end_if")
    #output.append("\nend_monitor")
    return "\n".join(output)

if __name__ == "__main__":
    with open("expansion_limits.txt", "w") as f:
        f.write(generate_area_ban_script())
    print("Done")

