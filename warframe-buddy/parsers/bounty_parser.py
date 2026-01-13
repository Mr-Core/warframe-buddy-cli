from parsers.base_parser import BaseDropParser


class CetusBountyDropParser(BaseDropParser):
    def __init__(self, soup):
        super().__init__(soup)
        
        self.cetus_bounty_drops = []
        self.current_mission_descriptor = None
        self.current_mission_rotation = None

    # Stopped here...
    # TODO 1. Remove Cetus and push Zariman to GitHub
    # TODO 2. Finish Cetus parsing logic
    
    def parse(self):
        source_type, cetus_bounty_table = self._parse_header('cetusRewards')
        source_type = 'Bounties'

        for row in cetus_bounty_table.find_all('tr'):
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
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'planet_name': 'Earth',
                    'mission_name': 'Cetus',
                    'mission_descriptor': self.current_mission_descriptor,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.current_mission_rotation
                }
                
                self.cetus_bounty_drops_bounty_drops.append(drop)
        
        report = self.verify_data(self.cetus_bounty_drops)
        
        return self.cetus_bounty_drops, report


class ZarimanBountyDropParser(BaseDropParser):
    """Inherited parser class for Zariman Bounty drops"""
    def __init__(self, soup):
        super().__init__(soup)
        
        self.zariman_bounty_drops = []
        self.current_mission_descriptor = None

    def parse(self):
        source_type, zariman_bounty_table = self._parse_header('zarimanRewards')
        source_type = 'Bounties'

        for row in zariman_bounty_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                if 'zariman' in text.lower():
                    self.current_mission_descriptor = self.normalize_text(text)
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 2:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'planet_name': 'Zariman Ten Zero',
                    'mission_name': 'Zariman',
                    'mission_descriptor': self.current_mission_descriptor,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': 'Final stage'
                }
                
                self.zariman_bounty_drops.append(drop)
        
        report = self.verify_data(self.zariman_bounty_drops)
        
        return self.zariman_bounty_drops, report
