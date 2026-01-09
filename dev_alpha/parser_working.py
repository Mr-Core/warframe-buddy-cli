import requests
from collections import Counter
from bs4 import BeautifulSoup
from base_parser import BaseDropParser


def fetch_data():
    url = "https://warframe-web-assets.nyc3.cdn.digitaloceanspaces.com/uploads/cms/hnfvc0o3jnfvc873njb03enrf56.html"
    response = requests.get(url)
    response.encoding = "utf-8"
    
    soup = BeautifulSoup(response.text, "html.parser")

    with open('Warframe_PC_Drops.html', 'w', encoding='utf-8') as file:
        file.write(soup.prettify())


def load_html(file_path):
    """Load HTML file using BeautifulSoup"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return BeautifulSoup(f.read(), 'html.parser')


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
        pass  # if it fails, keep original text
    
    # 5. Final trim (encoding fixes can add whitespace)
    data = data.strip()
    
    return data if data else None


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
            if drop["mission_mode"] is None:
                counters["missing_mission_mode"] = counters.get("missing_mission_mode", 0) + 1
                # Hard error create errors report
                error = {
                    "index": index,
                    "item": drop["item"],
                    "reason": "Missing mission mode"
                }
                errors.append(error)
            
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
    
    return report


def print_verify_report(report):
    if not report["is_valid"]:
        print("Data is not safe to index or serve!")
        reasons = Counter(e["reason"] for e in report["errors"])
        print(reasons)
        return
    
    summary = report["summary"]
    print(
        f"- Valid rows: {summary['valid_rows']}/{summary['total_rows']}\n"
        f"- Data integrity: {summary['valid_rows'] / summary['total_rows']:.1%}\n"
        f"- Warnings: {len(report['warnings'])}"
    )
    if len(report["warnings"]) > 0:
        reasons = Counter(e["reason"] for e in report["warnings"])
        print(reasons)
    print()
    
    return


class WarframeDropParser(BaseDropParser):
    def __init__(self, html_file_path):
        soup = load_html(html_file_path)
        super().__init__(soup)
        
        self.mission_drops = []
        self.relic_drops = []

        self.current_mission_mode = None
        self.current_planet_name = None
        self.current_mission_name = None
        self.current_mission_descriptor = None
        self.current_rotation = None
        
        self.current_relic_tier = None
        self.current_relic_name = None
        self.current_relic_refinement = None
        
    def parse_all(self):
        """Main entry point"""
        self.parse_missions()
        self.parse_relics()
        return self.get_all_drops()
    
    def get_all_drops(self):
        """Return all parsed drops"""
        return self.mission_drops + self.relic_drops
    
    def parse_missions(self):
        """Parse mission section"""
        missions_header = self.soup.find("h3", id="missionRewards")
        if not missions_header:
            print("Warning: No mission rewards section found")
            return []
            
        source_type = missions_header.text.replace(":", "")
        source_type = normalize_text(source_type)

        missions_table = missions_header.find_next_sibling("table")
        if not missions_table:
            print("Warning: No mission table found")
            return []

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
                    self.current_rotation = normalize_text(text.split()[-1])
                    continue

                # ---- Variant missions ----
                if "variant" in lowered:
                    if "/" in text:
                        planet_part = text.split("/", 1)[0]
                        self.current_planet_name = normalize_text(planet_part)
                    else:
                        self.current_planet_name = None

                    self.current_mission_name = None
                    self.current_mission_descriptor = normalize_text(text)
                    self.current_mission_mode = "CONCLAVE"
                    self.current_rotation = None
                    continue

                # ---- Normal mission mode detection ----
                if "conclave" in lowered:
                    self.current_mission_mode = "CONCLAVE"
                elif "recall" in lowered or "event" in lowered:
                    self.current_mission_mode = "EVENT"
                else:
                    self.current_mission_mode = "PVE"

                # ---- Mission header parsing ----
                if "(" in text and ")" in text:
                    left, right = text.split("(", 1)
                    self.current_mission_descriptor = normalize_text(right.replace(")", ""))

                    if "/" in left:
                        planet_part, node_part = left.split("/", 1)
                        self.current_planet_name = normalize_text(planet_part)
                        self.current_mission_name = normalize_text(node_part)
                    else:
                        self.current_planet_name = None
                        self.current_mission_name = normalize_text(left)

                    self.current_rotation = None
                else:
                    # Handle headers without parentheses
                    if "/" in text:
                        planet_part, node_part = text.split("/", 1)
                        self.current_planet_name = normalize_text(planet_part)
                        self.current_mission_name = normalize_text(node_part)
                        self.current_mission_descriptor = None
                    else:
                        self.current_planet_name = None
                        self.current_mission_name = normalize_text(text)
                        self.current_mission_descriptor = None

            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) == 2:
                item_name = td_cells[0].text
                item_name = normalize_text(item_name)
                
                chance_text = td_cells[1].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)
                
                drop = {
                    "item": item_name,
                    "source_type": source_type,
                    "mission_mode": self.current_mission_mode,
                    "planet_name": self.current_planet_name,
                    "mission_name": self.current_mission_name,
                    "mission_descriptor": self.current_mission_descriptor,
                    "rarity": rarity,
                    "chance": chance_number,
                }

                # Rotation is optional → include only if present
                if self.current_rotation is not None:
                    drop["rotation"] = self.current_rotation

                self.mission_drops.append(drop)

        print("Filtering inactive content for Missions...")
        filtered_missions_drop = filter_active_content(self.mission_drops)
        print(f"Filtered from {len(self.mission_drops)} to {len(filtered_missions_drop)} drops.\n")

        print("Verifying data for Missions: ")
        report = verify_data(filtered_missions_drop)
        if report is None:
            print("No data to verify.")
        else:
            print_verify_report(report)
        
        return filtered_missions_drop
    
    def parse_relics(self):
        """Parse relics section"""
        relics_header = self.soup.find("h3", id="relicRewards")
        if not relics_header:
            print("Warning: No relic rewards section found")
            return []
            
        source_type = relics_header.text.replace(":", "")
        source_type = normalize_text(source_type)

        relics_table = relics_header.find_next_sibling("table")
        if not relics_table:
            print("Warning: No relic table found")
            return []

        for row in relics_table.find_all("tr"):
            th_cells = row.find_all("th")
            td_cells = row.find_all("td")

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                
                # Parse relic header format: "Tier RelicName Refinement"
                # Example: "Lith A1 Intact"
                parts = text.split()
                if len(parts) >= 3:
                    self.current_relic_tier = normalize_text(parts[0])  # e.g., "Lith"
                    self.current_relic_name = normalize_text(parts[1])  # e.g., "A1"
                    self.current_relic_refinement = normalize_text(" ".join(parts[2:]))  # e.g., "Intact"
                else:
                    # Fallback: try to extract tier and name
                    self.current_relic_tier = None
                    self.current_relic_name = normalize_text(text)
                    self.current_relic_refinement = None

            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 2:
                item_name = td_cells[0].text
                item_name = normalize_text(item_name)
                
                chance_text = td_cells[1].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)
                
                drop = {
                    "item": item_name,
                    "source_type": source_type,
                    "mission_mode": None,  # Relics don't have mission mode
                    "planet_name": None,
                    "mission_name": None,
                    "mission_descriptor": None,
                    "rarity": rarity,
                    "chance": chance_number,
                    "relic_tier": self.current_relic_tier,
                    "relic_name": self.current_relic_name,
                    "relic_refinement": self.current_relic_refinement,
                }

                self.relic_drops.append(drop)

        print("Verifying data for Relics: ")
        report = verify_data(self.relic_drops)
        if report is None:
            print("No data to verify.")
        else:
            print_verify_report(report)
        
        return self.relic_drops


if __name__ == "__main__":
    fetch_new_data = "n"
    if fetch_new_data == "y":
        fetch_data()
        print("\nNew data successfully fetched.")
    else:
        print("\nSkipped fetching new data.")

    parser = WarframeDropParser("Warframe_PC_Drops.html")
    
    print("\nParsing missions...")
    mission_drops = parser.parse_missions()
    
    print("\nParsing relics...")
    relic_drops = parser.parse_relics()
    
    print(f"Total drops parsed: {len(mission_drops) + len(relic_drops)}")
    print(f"- Missions: {len(mission_drops)}")
    print(f"- Relics: {len(relic_drops)}")
    
    parser.drops = mission_drops + relic_drops
    parser.save_to_file("all_drops.json", True)
