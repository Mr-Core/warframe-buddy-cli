from base_parser import BaseDropParser


class SortieDropParser(BaseDropParser):
    """Inherited parser class for Sortie drops"""
    def __init__(self, soup):
        super().__init__(soup)
        
        self.sortie_drops = []
        
        self.current_mission_name = None

    def parse(self):
        source_type, sorties_table = self._parse_header('sortieRewards')

        for row in sorties_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                self.current_mission_name = self.normalize_text(text)
            
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
                    'mission_name': self.current_mission_name,
                    'rarity': rarity,
                    'chance': chance_number
                }
                
                self.sortie_drops.append(drop)
        
        report = self.verify_data(self.sortie_drops)
        
        return self.sortie_drops, report
