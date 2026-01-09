import requests
from bs4 import BeautifulSoup
from collections import Counter


# Fetch fresh html file from the web
def fetch_data():
    url = "https://warframe-web-assets.nyc3.cdn.digitaloceanspaces.com/uploads/cms/hnfvc0o3jnfvc873njb03enrf56.html"
    response = requests.get(url)
    response.encoding = "utf-8"
    
    soup = BeautifulSoup(response.text, "html.parser")

    with open('Warframe_PC_Drops.html', 'w', encoding='utf-8') as file:
        file.write(soup.prettify())


# Open local HTML file
with open("Warframe_PC_Drops.html", encoding="utf-8") as file_handle:
    soup = BeautifulSoup(file_handle, "html.parser")


def normalize_text(data):
    """
    Normalize raw text input into either:
    - None
    or
    - Clean, meaningful string
    """
    
    # 1. Type safety
    if data is None:
        return None

    if not isinstance(data, str):
        return None
    
    # 2. Trim whitespace
    data = data.strip()
    
    # 3. Collapse semantic empties:
    if not data:
        return None
    
    SEMANTIC_EMPTY = {
        "-", "—", "–",
        "n/a", "na", "none",
        "null", "unknown"
    }
    
    if data.lower() in SEMANTIC_EMPTY:
        return None
    
    # 4. Fix common encoding issues (best-effort)
    try:
        data = data.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass # if it fails, keep original text
    
    # 5. Final trim (encoding fixes can add whitepace)
    data = data.strip()
    
    return data if data else None


def parse_mission_section(soup) -> list[dict]:
    missions_drops = []

    missions_header = soup.find("h3", id="missionRewards")
    source_type = missions_header.text.replace(":", "")
    source_type = normalize_text(source_type)

    missions_table = missions_header.find_next_sibling("table")

    # ---- STATE (context) ----
    current_planet_name = None
    current_mission_name = None
    current_mission_descriptor = None
    current_rotation = None

    for row in missions_table.find_all("tr"):
        th_cells = row.find_all("th")
        td_cells = row.find_all("td")

        # -------------------------
        # CONTEXT ROWS (headers)
        # -------------------------
        if th_cells:
            text = th_cells[0].text.strip()
            lowered = text.lower()

            # ---- Rotation header ----
            if lowered.startswith("rotation"):
                current_rotation = normalize_text(text.split()[-1])
                continue

            # ---- Variant missions ----
            if "variant" in lowered:
                if "/" in text:
                    planet_part = text.split("/", 1)[0]
                    current_planet_name = normalize_text(planet_part)
                else:
                    current_planet_name = None

                current_mission_name = None
                current_mission_descriptor = normalize_text(text)
                current_mission_mode = "CONCLAVE"
                current_rotation = None
                continue

            # ---- Normal mission mode detection ----
            if "conclave" in lowered:
                current_mission_mode = "CONCLAVE"
            elif "recall" in lowered or "event" in lowered:
                current_mission_mode = "EVENT"
            else:
                current_mission_mode = "PVE"

            # ---- Mission header parsing ----
            if "(" in text and ")" in text:
                left, right = text.split("(", 1)
                current_mission_descriptor = normalize_text(right.replace(")", ""))

                if "/" in left:
                    planet_part, node_part = left.split("/", 1)
                    current_planet_name = normalize_text(planet_part)
                    current_mission_name = normalize_text(node_part)
                else:
                    current_planet_name = None
                    current_mission_name = normalize_text(left)

                current_rotation = None

        # -------------------------
        # DROP ROWS
        # -------------------------
        elif len(td_cells) == 2:
            item_name = td_cells[0].text
            item_name = normalize_text(item_name)
            
            chance_text = td_cells[1].text.strip()
            
            rarity = chance_text
            chance_number = None

            if "(" in chance_text and ")" in chance_text:
                rarity = chance_text.split("(")[0]
                rarity = normalize_text(rarity)
                
                percent_str = (
                    chance_text.split("(", 1)[1]
                    .replace(")", "")
                    .replace("%", "")
                    .strip()
                )
                try:
                    chance_number = float(percent_str) / 100
                except ValueError:
                    pass
            
            drop = {
                "item": item_name,
                "source_type": source_type,
                "mission_mode": current_mission_mode,  # pyright: ignore[reportPossiblyUnboundVariable]
                "planet_name": current_planet_name,
                "mission_name": current_mission_name,
                "mission_descriptor": current_mission_descriptor,
                "rarity": rarity,
                "chance": chance_number,
            }

            # Rotation is optional → include only if present
            if current_rotation is not None:
                drop["rotation"] = current_rotation

            missions_drops.append(drop)

    print("Filtering inactive content for Missions...")
    filtered_missions_drop = filter_active_content(missions_drops)
    print("Filtering completed!\n")

    print("Verifing data for Missions: ")
    report = verify_data(filtered_missions_drop)
    if report is None:
        print("No data to verify.")
    else:
        print_verify_report(report)
    
    return filtered_missions_drop


def parse_relic_section(soup) -> list[dict]:
    relics_drops = []

    relics_header = soup.find("h3", id="relicRewards")
    source_type = relics_header.text.replace(":", "")
    source_type = normalize_text(source_type)

    relics_table = relics_header.find_next_sibling("table")
    
    # ---- STATE (context) ----
    current_relic_tier = None
    current_relic_name = None
    current_relic_refinement = None
    
    for row in relics_table.find_all("tr"):
        th_cells = row.find_all("th")
        td_cells = row.find_all("td")

        # ---- CONTEXT ROWS ----
        if th_cells:
            text = th_cells[0].text.strip()
            
            mission_mode = None
            
            if "conclave" in text.lower():
                mission_mode = "CONCLAVE"
            elif "recall" in text.lower():
                mission_mode = "EVENT"
            else:
                mission_mode = "PVE"
            
            current_mission_mode = mission_mode
            
            current_relic_tier = text.split(" ")[0]
            current_relic_tier = normalize_text(current_relic_tier)
            
            current_relic_name = text.split("(")[0].replace("Relic", "")
            current_relic_name = normalize_text(current_relic_name)
            
            current_relic_refinement = text.split("(")[1].replace(")", "")
            current_relic_refinement = normalize_text(current_relic_refinement)
            
        
        # ---- DROP ROWS ----
        elif len(td_cells) == 2:
            item_name = td_cells[0].text
            item_name = normalize_text(item_name)
            
            chance_text = td_cells[1].text.strip()
            
            rarity = chance_text
            chance_number = None
            
            if "(" in chance_text and ")" in chance_text:
                rarity = chance_text.split("(")[0]
                rarity = normalize_text(rarity)
                
                percent_str = (
                    chance_text.split("(")[1]
                    .split(")")[0]
                    .replace("%", "")
                    .strip()
                )
                try:
                    chance_number = float(percent_str) / 100
                except ValueError:
                    pass
            
            relics_drops.append({
                "item": item_name,
                "source_type": source_type,
                "mission_mode": current_mission_mode,  # pyright: ignore[reportPossiblyUnboundVariable]
                "relic_tier": current_relic_tier,
                "relic_name": current_relic_name,
                "relic_refinement": current_relic_refinement,
                "rarity": rarity,
                "chance": chance_number
            })
    
    print("\nFiltering inactive content for Relics...")
    filtered_relics_drops = filter_active_content(relics_drops)
    print("Filtering completed!\n")
    
    print("Verifing data for Relics: ")
    report = verify_data(filtered_relics_drops)
    if report is None:
        print("No data to verify.")
    else:
        print_verify_report(report)
    
    return filtered_relics_drops


def filter_active_content(drops):
    return [
        drop for drop in drops
        if drop.get("mission_mode") != "EVENT"
    ]


def verify_data(drops: list[dict]):
    report = {
    "summary": {},
    "counters": {},
    "errors": [],
    "warnings": [],
    "is_valid": False
    }
    
    counters = {}
    errors = []
    warnings = []
    
    unique_items = set()
    error_rows = set()
    
    for index, drop in enumerate(drops):
        # Summary
        if drop["item"] not in unique_items and drop["item"] is not None:
            unique_items.add(drop["item"])
        
        # Counters
        if drop["item"] is None:
            counters["missing_item"] = counters.get("missing_item", 0) + 1
            # Hard error, create errors report
            error = {
                "index": index,
                "item": None,
                "reason": "Missing item name"
            }
            errors.append(error)
        
        if drop["source_type"] is None:
            counters["missing_source_type"] = counters.get("missing_source_type", 0) + 1
            # Hard error, create errors report
            error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing source type"
            }
            errors.append(error)
        
        if drop["mission_mode"] is None:
            counters["missing_mission_mode"] = counters.get("missing_mission_mode", 0) + 1
            # Hard error create errors report
            error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing mission mode"
            }
            errors.append(error)
        
        if drop["rarity"] is None:
            counters["missing_chance_rarity"] = counters.get("missing_chance_rarity", 0) + 1
            # Soft problem, create warnings report
            warning = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing chance rarity"
            }
            warnings.append(warning)
        
        if drop["chance"] is None:
            counters["chance_missing"] = counters.get("chance_missing", 0) + 1
            # Hard error, create errors report
            error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing chance number"
            }
            errors.append(error)
        else:
            if drop["chance"] < 0 or drop["chance"] > 1:
                counters["chance_out_of_range"] = counters.get("chance_out_of_range", 0) + 1
                # Hard error, create errors report
                error = {
                    "index": index,
                    "item": drop["item"],
                    "reason": "Chance number is out of range"
                }
                errors.append(error)
        
        if drop["source_type"] == "Missions":
            if drop["planet_name"] is None:
                counters["missing_planet_name"] = counters.get("missing_planet_name", 0) + 1
                # Hard error, create errors report
                error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing planet name"
                }
                errors.append(error)
            
            if drop["mission_name"] is None:
                if drop["mission_descriptor"] and "variant" in drop["mission_descriptor"].lower():
                    pass
                else:
                    counters["missing_mission_name"] = counters.get("missing_mission_name", 0) + 1
                    # Hard error, create errors report
                    error = {
                    "index": index,
                    "item": drop["item"],
                    "mission_mode": drop["mission_mode"],
                    "planet_name": drop["planet_name"],
                    "mission_descriptor": drop["mission_descriptor"],
                    "reason": "Missing mission name"
                    }
                    errors.append(error)

            if drop["mission_descriptor"] is None:
                counters["missing_mission_descriptor"] = counters.get("missing_mission_descriptor", 0) + 1
                # Hard error, create errors report
                error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing mission descriptor"
                }
                errors.append(error)
            
            if "rotation" in drop:
                if drop["rotation"] not in ("A", "B", "C", "D"):
                    counters["missing_rotation"] = counters.get("missing_rotation", 0) + 1
                    # Hard error, create errors report
                    error = {
                    "index": index,
                    "item": drop["item"],
                    "reason": "Missing mission rotation",
                    "mission_descriptor": drop["mission_descriptor"]
                    }
                    errors.append(error)
        
        if drop["source_type"] == "Relics":
            if drop["relic_tier"] is None:
                counters["missing_relic_tier"] = counters.get("missing_relic_tier", 0) + 1
                # Hard error, create errors report
                error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing relic tier"
                }
                errors.append(error)
            
            if drop["relic_name"] is None:
                counters["missing_relic_name"] = counters.get("missing_relic_name", 0) + 1
                # Hard error, create errors report
                error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing relic name"
                }
                errors.append(error)
            
            if drop["relic_refinement"] is None:
                counters["missing_relic_refinement"] = counters.get("missing_relic_refinement", 0) + 1
                # Hard error, create errors report
                error = {
                "index": index,
                "item": drop["item"],
                "reason": "Missing relic refinement"
                }
                errors.append(error)
    
    for error in errors:
        error_rows.add(error["index"])
    
    if len(drops) == 0:
        return None
    
    # Summary
    summary = {}
    summary["total_rows"] = len(drops)
    summary["valid_rows"] = len(drops) - len(error_rows)
    summary["unique_items"] = len(unique_items)
    
    report["summary"] = summary
    report["counters"] = counters
    report["errors"] = errors
    report["warnings"] = warnings
    
    if len(errors) == 0:
        report["is_valid"] = True
    else:
        for error in errors:
            print(error)
    
    # for key, value in report.items():
    #     print(key, value)
        
    return report


def print_verify_report(report):
    if not report["is_valid"]:
        print("Data is not safe to index or serve!")
        reasons = Counter(e["reason"] for e in report["errors"])
        print(reasons)
        return  # pyright: ignore[reportReturnType]
    
    summary = report["summary"]
    print(
        f"- Valid rows: {summary['valid_rows']}/{summary['total_rows']}\n"
        f"- Data integrity: {summary['valid_rows'] / summary['total_rows']:.1%}\n"
        f"- Warnings: {len(report["warnings"])}"
    )
    if len(report["warnings"]) > 0:
        reasons = Counter(e["reason"] for e in report["warnings"])
        print(reasons)
    print()
    
    return


def index_by_name(drops: list[dict]):
    indexed_items = {}
    
    for drop in drops:
        item_name = drop["item"]
        
        if item_name not in indexed_items:
            indexed_items[item_name] = []
        
        indexed_items[item_name].append(drop)
    
    return indexed_items


def search_item(indexed_items: dict, query: str):
    normalized_query = query.strip().lower()
    
    for item_name, drops in indexed_items.items():
        if item_name.lower() == normalized_query:
            return drops
    
    return None


# ---- Run & sanity check ----
mission_drops = parse_mission_section(soup)
relic_drops = parse_relic_section(soup)


# Indexing & Search check
indexed = index_by_name(mission_drops + relic_drops)

query = "Xiphos Fuselage Blueprint"

results = search_item(indexed, query)

if not results:
    print("Item not found. RNG truly hates you...")
else:
    for result in results:
        print(result)

###

# Data check
# for d in mission_drops[:1]:
#     print(d) 

# print()

# for d in relic_drops[:1]:
#     print(d)

# for d in mission_drops[:-5]:
#     print({
#     "planet": d["planet_name"],
#     "mission": d["mission_name"],
#     "descriptor": d["mission_descriptor"],
#     "rotation": d.get("rotation")
# })
