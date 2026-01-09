from base_parser import BaseDropParser


class RelicDropParser(BaseDropParser):
    """Inherited parser class for Relic drops"""
    def __init__(self, soup):
        super().__init__(soup)
        
        self.relic_drops = []
        
        self.current_relic_tier = None
        self.current_relic_name = None
        self.current_relic_refinement = None
    
    def parse(self):
        source_type, relics_table = self._parse_header('relicRewards')
        
        for row in relics_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                
                # Parse relic header format: "Tier RelicName Refinement"
                # Example: "Lith A1 Intact"
                parts = text.split()
                if len(parts) == 4:
                    self.current_relic_tier = self.normalize_text(parts[0])  # e.g., "Lith"
                    self.current_relic_name = self.normalize_text(parts[1])  # e.g., "A1"
                    # parts[2] = 'Relic' - skipped, not needed
                    self.current_relic_refinement = self.normalize_text(parts[3].replace('(', '').replace(')', ''))  # e.g., "Intact"
                elif len(parts) == 3:
                    continue
                else:
                    # Fallback: try to extract tier and name
                    self.current_relic_tier = None
                    self.current_relic_name = self.normalize_text(text)
                    self.current_relic_refinement = None
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 2:
                item_name = td_cells[0].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[1].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'rarity': rarity,
                    'chance': chance_number,
                    'relic_tier': self.current_relic_tier,
                    'relic_name': self.current_relic_name,
                    'relic_refinement': self.current_relic_refinement,
                }
                
                self.relic_drops.append(drop)
        
        report = self.verify_data(self.relic_drops)
        
        return self.relic_drops, report
