import os
import json
from datetime import datetime
from collections import defaultdict
from config import INDEXED_DATA_FILE, PARSED_DATA_FILE, COMMON_SEARCH_DATA_FILE


class WarframeSearchEngine:
    """Production-ready search engine with rebuild capability"""

    def __init__(self):
        """Initialize empty - data loaded separately"""
        self.search_indexes = {}
        self.last_rebuild = None

    # ==== INDEX MANAGEMENT ====

    def create_indexes_from_drops(self, all_drops) -> str:
        """
        Create indexes from drop data (used by orchestrator after parsing)

        Args:
            all_drops: List of drop dictionaries from parser
        """
        # Reset indexes
        self.search_indexes = {
            "item_sources": defaultdict(list),
            "item_missions": defaultdict(list),
            "item_relics": defaultdict(list),
            "item_sorties": defaultdict(list),
            "item_bounties": defaultdict(list),
            "item_transient": defaultdict(list),
            "mission_planets": defaultdict(list),
            "relic_tiers": defaultdict(list),
            "bountie_planets": defaultdict(list),
            "item_lowercase": {},
            "metadata": {
                "total_drops": len(all_drops),
                "created_at": datetime.now().isoformat(),
                "source": "parsed_data",
            },
        }

        # Build all indexes in one pass
        for drop in all_drops:
            item = drop["item"]
            source_type = drop["source_type"]

            # Store lowercase version for case-insensitive search
            item_lower = item.lower()
            if item_lower not in self.search_indexes["item_lowercase"]:
                self.search_indexes["item_lowercase"][item_lower] = item

            # Original item indexing
            self.search_indexes["item_sources"][item].append(drop)

            if source_type == "Missions":
                self.search_indexes["item_missions"][item].append(drop)

                planet = drop.get("planet_name")
                if planet:
                    key = f"{item}::{planet}"
                    self.search_indexes["mission_planets"][key].append(drop)

            elif source_type == "Relics":
                self.search_indexes["item_relics"][item].append(drop)

                tier = drop.get("relic_tier")
                if tier:
                    key = f"{item}::{tier}"
                    self.search_indexes["relic_tiers"][key].append(drop)

            elif source_type == "Sorties":
                self.search_indexes["item_sorties"][item].append(drop)

            elif source_type == "Bounties":
                self.search_indexes["item_bounties"][item].append(drop)

            elif source_type == "Dynamic Location Rewards":
                self.search_indexes["item_transient"][item].append(drop)

        self.last_rebuild = datetime.now()

        return f"  - Unique items: {len(self.search_indexes['item_sources'])}"

    def rebuild_from_parsed_file(self):
        """
        Rebuild indexes from saved JSON file
        Used by service for daily updates
        """
        print("Rebuilding indexes from parsed data file...")

        try:
            with open(PARSED_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            drops = data["drops"]
            self.create_indexes_from_drops(drops)
            self.save_indexes()
            print("✓ Indexes rebuilt successfully")
            return True

        except FileNotFoundError:
            print(f"✗ Parsed data file not found: {PARSED_DATA_FILE}")
            return False

        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in parsed data: {e}")
            return False

        except KeyError:
            print("✗ Invalid parsed data format")
            return False

    def save_indexes(self) -> str:
        """Save current indexes to file"""
        if not self.search_indexes:
            return "✗ No indexes to save"

        serializable_indexes = {}
        for index_name, index_data in self.search_indexes.items():
            if isinstance(index_data, defaultdict):
                serializable_indexes[index_name] = dict(index_data)
            else:
                serializable_indexes[index_name] = index_data

        data = {
            "created_at": datetime.now().isoformat(),
            "last_rebuild": (
                self.last_rebuild.isoformat() if self.last_rebuild else None
            ),
            "indexes": serializable_indexes,
        }

        try:
            with open(INDEXED_DATA_FILE, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return f'✓ Saved indexes to "{INDEXED_DATA_FILE}"'
        except IOError as e:
            return f"✗ Failed to save indexes: {e}"

    def load_indexes(self) -> tuple[bool, str]:
        """Load indexes from file"""
        try:
            with open(INDEXED_DATA_FILE, "r") as f:
                data = json.load(f)

            # Convert back to defaultdict for lists, keep dict for others
            for index_name, index_data in data["indexes"].items():
                if index_name in [
                    "item_sources",
                    "item_missions",
                    "item_relics",
                    "item_sorties",
                    "mission_planets",
                    "relic_tiers",
                ]:
                    self.search_indexes[index_name] = defaultdict(list, index_data)
                else:
                    self.search_indexes[index_name] = index_data

            if "last_rebuild" in data and data["last_rebuild"]:
                self.last_rebuild = datetime.fromisoformat(data["last_rebuild"])

            response = f"✓ Loaded indexes (created {data['created_at']})"
            response += (
                f"\n  - Unique items: {len(self.search_indexes['item_sources'])}"
            )
            return True, response

        except FileNotFoundError:
            response = f"✗ No index file found!"
            response += "\nPlease run Mode 1 first to create indexes."
            return False, response

        except json.JSONDecodeError as e:
            response = f"✗ Invalid JSON in index file: {e}"
            return False, response

    def get_index_status(self) -> dict:
        """Get current index status"""
        if not self.search_indexes:
            return {
                "loaded": False,
                "total_items": 0,
                "last_rebuild": None,
                "index_types": [],
            }

        return {
            "loaded": True,
            "total_items": len(self.search_indexes.get("item_sources", {})),
            "last_rebuild": (
                self.last_rebuild.isoformat() if self.last_rebuild else None
            ),
            "index_types": list(self.search_indexes.keys()),
        }

    # ==== SEARCH METHODS ====

    def search_item(self, item_name: str, **filters: dict) -> list:
        """Search for exact item name"""
        if not self.search_indexes:
            raise ValueError("No indexes loaded.")

        self._most_common_search(item_name)

        results = self.search_indexes["item_sources"].get(item_name, [])

        # Apply chance filters
        min_chance = filters.get("min_chance")
        if min_chance is not None:
            results = [
                d
                for d in results
                if d.get("chance") is not None and d["chance"] >= min_chance
            ]

        max_chance = filters.get("max_chance")
        if max_chance is not None:
            results = [
                d
                for d in results
                if d.get("chance") is not None and d["chance"] <= max_chance
            ]

        # Sort by best chance
        results.sort(key=lambda x: x.get("chance", 0), reverse=True)

        return results

    def find_matching_items(self, search_term: str) -> list:
        """Find items matching search term (case-insensitive, partial match)"""
        search_lower = search_term.lower()
        matching = []

        # Check lowercase index first
        for item_lower, item_actual in self.search_indexes.get(
            "item_lowercase", {}
        ).items():
            if search_lower in item_lower:
                matching.append(item_actual)

        return matching

    def get_item_summary(self, item_name: str) -> dict:
        """Get summary for exact item name"""
        summary = {
            "item": item_name,
            "total_sources": 0,
            "missions": [],
            "relics": [],
            "sorties": [],
            "bounties": [],
            "best_chance": 0,
            "best_source": None,
        }

        self._most_common_search(item_name)

        all_sources = self.search_indexes["item_sources"].get(item_name, [])
        if not all_sources:
            return summary

        summary["total_sources"] = len(all_sources)

        for drop in all_sources:
            if drop["source_type"] == "Missions":
                if "rotation" in drop:
                    summary["missions"].append(
                        {
                            "planet": drop.get("planet_name"),
                            "mission": drop.get("mission_name"),
                            "type": drop.get("mission_type"),
                            "chance": drop.get("chance"),
                            "rarity": drop.get("rarity"),
                            "rotation": drop.get("rotation"),
                        }
                    )
                else:
                    summary["missions"].append(
                        {
                            "planet": drop.get("planet_name"),
                            "mission": drop.get("mission_name"),
                            "type": drop.get("mission_type"),
                            "chance": drop.get("chance"),
                            "rarity": drop.get("rarity"),
                        }
                    )
            elif drop["source_type"] == "Relics":
                summary["relics"].append(
                    {
                        "tier": drop.get("relic_tier"),
                        "name": drop.get("relic_name"),
                        "refinement": drop.get("relic_refinement"),
                        "chance": drop.get("chance"),
                        "rarity": drop.get("rarity"),
                    }
                )
            elif drop["source_type"] == "Sorties":
                summary["sorties"].append(
                    {"chance": drop.get("chance"), "rarity": drop.get("rarity")}
                )
            elif drop["source_type"] == "Bounties":
                if "rotation" in drop:
                    summary["bounties"].append(
                        {
                            "planet": drop.get("planet_name"),
                            "mission": drop.get("mission_name"),
                            "name": drop.get("bounty_name"),
                            "level": drop.get("bounty_level"),
                            "chance": drop.get("chance"),
                            "rarity": drop.get("rarity"),
                            "rotation": drop.get("rotation"),
                            "stage": drop.get("stage"),
                        }
                    )
                else:
                    summary["bounties"].append(
                        {
                            "planet": drop.get("planet_name"),
                            "mission": drop.get("mission_name"),
                            "name": drop.get("bounty_name"),
                            "level": drop.get("bounty_level"),
                            "chance": drop.get("chance"),
                            "rarity": drop.get("rarity"),
                            "stage": drop.get("stage"),
                        }
                    )

            if drop.get("chance", 0) > summary["best_chance"]:
                summary["best_chance"] = drop.get("chance", 0)
                summary["best_source"] = drop

        summary_sorted = summary.copy()
        summary_sorted["missions"].sort(key=lambda x: x.get("chance", 0), reverse=True)
        summary_sorted["relics"].sort(key=lambda x: x.get("chance", 0), reverse=True)
        summary_sorted["sorties"].sort(key=lambda x: x.get("chance", 0), reverse=True)
        summary_sorted["bounties"].sort(key=lambda x: x.get("chance", 0), reverse=True)

        return summary_sorted

    def _most_common_search(self, item_name: str) -> None:
        data = {}

        if os.path.isfile(COMMON_SEARCH_DATA_FILE):
            try:
                with open(COMMON_SEARCH_DATA_FILE, "r") as f:
                    data = json.load(f)

            except ValueError:
                data = {}

            except Exception as e:
                print(f"An error occurred: {e}")

        if item_name not in data:
            data[item_name] = 1
        else:
            data[item_name] += 1

        with open(COMMON_SEARCH_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
