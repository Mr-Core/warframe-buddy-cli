from parsers.base_parser import BaseDropParser


class TransientDropParser(BaseDropParser):  # Dynamic Location Rewards
    def __init__(self, soup):
        super().__init__(soup)

        self.transient_drops = []

        self.transient_mission_name = None
        self.transient_rotation = None

    def parse(self):
        source_type, transient_table = self._parse_header("transientRewards")

        if not transient_table:
            return [], None

        for row in transient_table.find_all("tr"):
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
                    self.transient_rotation = self.normalize_text(text.split()[-1])
                    continue

                self.transient_mission_name = self.normalize_text(text)

            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 2:
                item_name = td_cells[0].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[1].text.strip()

                rarity, chance_number = self._parse_chance_text(chance_text)

                if self.transient_rotation:
                    drop = {
                        "item": item_name,
                        "source_type": source_type,
                        "mission_name": self.transient_mission_name,
                        "rarity": rarity,
                        "chance": chance_number,
                        "rotation": self.transient_rotation,
                    }
                else:
                    drop = {
                        "item": item_name,
                        "source_type": source_type,
                        "mission_name": self.transient_mission_name,
                        "rarity": rarity,
                        "chance": chance_number,
                    }

                self.transient_drops.append(drop)

        report = self.verify_data(self.transient_drops)

        return self.transient_drops, report
