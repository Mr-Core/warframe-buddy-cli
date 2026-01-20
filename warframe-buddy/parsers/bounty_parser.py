import re

from parsers.base_parser import BaseDropParser


class CetusBountyDropParser(BaseDropParser):
    def __init__(self, soup):
        super().__init__(soup)
        
        self.cetus_bounty_drops = []
        
        self.cetus_bounty_name = None
        self.cetus_bounty_level = None
        self.cetus_bounty_rotation = None
        self.cetus_bounty_stage = None
    
    def parse(self):
        source_type, cetus_bounty_table = self._parse_header('cetusRewards')
        source_type = 'Bounties'
        
        if not cetus_bounty_table:
            return [], None

        for row in cetus_bounty_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                lowered = text.lower()
                
                # ---- Bounty name and level header ----
                if lowered.startswith('level'):
                    match = re.match(r'(Level\s+[\d\s\-]+)\s+(.*)', text)
                    
                    if match:
                        bounty_name = match.group(2).strip()
                        bounty_level = match.group(1).strip()
                        
                        self.cetus_bounty_name = self.normalize_text(bounty_name)
                        self.cetus_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.cetus_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.cetus_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'planet_name': 'Earth',
                    'mission_name': 'Cetus',
                    'bounty_name': self.cetus_bounty_name,
                    'bounty_level': self.cetus_bounty_level,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.cetus_bounty_rotation,
                    'stage': self.cetus_bounty_stage,
                }
                
                self.cetus_bounty_drops.append(drop)
        
        report = self.verify_data(self.cetus_bounty_drops)
        
        return self.cetus_bounty_drops, report

class OrbVallisBountyDropParser(BaseDropParser):
    def __init__(self, soup):
        super().__init__(soup)
        
        self.orb_vallis_bounty_drops = []
        
        self.orb_vallis_bounty_name = None
        self.orb_vallis_bounty_level = None
        self.orb_vallis_bounty_rotation = None
        self.orb_vallis_bounty_stage = None
    
    def parse(self):
        source_type, orb_vallis_bounty_table = self._parse_header('solarisRewards')
        source_type = 'Bounties'
        
        if not orb_vallis_bounty_table:
            return [], None

        for row in orb_vallis_bounty_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                lowered = text.lower()
                
                # ---- Bounty name and level header ----
                if lowered.startswith('level'):
                    match = re.match(r'(Level\s+[\d\s\-]+)\s+(.*)', text)
                    
                    if match:
                        bounty_name = match.group(2).strip()
                        bounty_level = match.group(1).strip()
                        
                        self.orb_vallis_bounty_name = self.normalize_text(bounty_name)
                        self.orb_vallis_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.orb_vallis_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.orb_vallis_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'planet_name': 'Venus',
                    'mission_name': 'Fortuna',
                    'bounty_name': self.orb_vallis_bounty_name,
                    'bounty_level': self.orb_vallis_bounty_level,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.orb_vallis_bounty_rotation,
                    'stage': self.orb_vallis_bounty_stage,
                }
                
                self.orb_vallis_bounty_drops.append(drop)
        
        report = self.verify_data(self.orb_vallis_bounty_drops)
        
        return self.orb_vallis_bounty_drops, report

class CambionDriftBountyDropParser(BaseDropParser):
    def __init__(self, soup):
        super().__init__(soup)
        
        self.cambion_drift_bounty_drops = []
        
        self.cambion_drift_bounty_name = None
        self.cambion_drift_bounty_level = None
        self.cambion_drift_bounty_rotation = None
        self.cambion_drift_bounty_stage = None
    
    def parse(self):
        source_type, cambion_drift_bounty_table = self._parse_header('deimosRewards')
        source_type = 'Bounties'
        
        if not cambion_drift_bounty_table:
            return [], None

        for row in cambion_drift_bounty_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                lowered = text.lower()
                
                # ---- Bounty name and level header ----
                if lowered.startswith('level'):
                    match = re.match(r'(Level\s+[\d\s\-]+)\s+(.*)', text)
                    
                    if match:
                        bounty_name = match.group(2).strip()
                        bounty_level = match.group(1).strip()
                        
                        self.cambion_drift_bounty_name = self.normalize_text(bounty_name)
                        self.cambion_drift_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.cambion_drift_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.cambion_drift_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'planet_name': 'Deimos',
                    'mission_name': 'Necralisk',
                    'bounty_name': self.cambion_drift_bounty_name,
                    'bounty_level': self.cambion_drift_bounty_level,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.cambion_drift_bounty_rotation,
                    'stage': self.cambion_drift_bounty_stage,
                }
                
                self.cambion_drift_bounty_drops.append(drop)
        
        report = self.verify_data(self.cambion_drift_bounty_drops)
        
        return self.cambion_drift_bounty_drops, report

class ZarimanBountyDropParser(BaseDropParser):
    """Inherited parser class for Zariman Bounty drops"""
    def __init__(self, soup):
        super().__init__(soup)
        
        self.zariman_bounty_drops = []
        
        self.zariman_bounty_name = None
        self.zariman_bounty_level = None
        self.zariman_bounty_rotation = None
        self.zariman_bounty_stage = None
    
    def parse(self):
        source_type, zariman_bounty_table = self._parse_header('zarimanRewards')
        source_type = 'Bounties'
        
        if not zariman_bounty_table:
            return [], None

        for row in zariman_bounty_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                lowered = text.lower()
                
                # ---- Bounty name and level header ----
                if lowered.startswith('level'):
                    match = re.match(r'(Level\s+[\d\s\-]+)\s+(.*)', text)
                    
                    if match:
                        bounty_name = match.group(2).strip()
                        bounty_level = match.group(1).strip()
                        
                        self.zariman_bounty_name = self.normalize_text(bounty_name)
                        self.zariman_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.zariman_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.zariman_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                if self.zariman_bounty_rotation:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Zariman',
                        'mission_name': 'Chrysalith',
                        'bounty_name': self.zariman_bounty_name,
                        'bounty_level': self.zariman_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'rotation': self.zariman_bounty_rotation,
                        'stage': self.zariman_bounty_stage,
                    }
                else:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Zariman',
                        'mission_name': 'Chrysalith',
                        'bounty_name': self.zariman_bounty_name,
                        'bounty_level': self.zariman_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'stage': self.zariman_bounty_stage,
                    }
                
                self.zariman_bounty_drops.append(drop)
        
        report = self.verify_data(self.zariman_bounty_drops)
        
        return self.zariman_bounty_drops, report
