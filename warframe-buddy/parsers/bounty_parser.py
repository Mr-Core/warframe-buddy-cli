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


class SolarisBountyDropParser(BaseDropParser):  # Orb Vallis
    def __init__(self, soup):
        super().__init__(soup)
        
        self.solaris_bounty_drops = []
        
        self.solaris_bounty_name = None
        self.solaris_bounty_level = None
        self.solaris_bounty_rotation = None
        self.solaris_bounty_stage = None
    
    def parse(self):
        source_type, solaris_bounty_table = self._parse_header('solarisRewards')
        source_type = 'Bounties'
        
        if not solaris_bounty_table:
            return [], None

        for row in solaris_bounty_table.find_all('tr'):
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
                        
                        self.solaris_bounty_name = self.normalize_text(bounty_name)
                        self.solaris_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.solaris_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.solaris_bounty_stage = self.normalize_text(text)
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
                    'bounty_name': self.solaris_bounty_name,
                    'bounty_level': self.solaris_bounty_level,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.solaris_bounty_rotation,
                    'stage': self.solaris_bounty_stage,
                }
                
                self.solaris_bounty_drops.append(drop)
        
        report = self.verify_data(self.solaris_bounty_drops)
        
        return self.solaris_bounty_drops, report


class DeimosBountyDropParser(BaseDropParser):  # Cambion Drift
    def __init__(self, soup):
        super().__init__(soup)
        
        self.deimos_bounty_drops = []
        
        self.deimos_bounty_name = None
        self.deimos_bounty_level = None
        self.deimos_bounty_rotation = None
        self.deimos_bounty_stage = None
    
    def parse(self):
        source_type, deimos_bounty_table = self._parse_header('deimosRewards')
        source_type = 'Bounties'
        
        if not deimos_bounty_table:
            return [], None

        for row in deimos_bounty_table.find_all('tr'):
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
                        
                        self.deimos_bounty_name = self.normalize_text(bounty_name)
                        self.deimos_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.deimos_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.deimos_bounty_stage = self.normalize_text(text)
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
                    'bounty_name': self.deimos_bounty_name,
                    'bounty_level': self.deimos_bounty_level,
                    'rarity': rarity,
                    'chance': chance_number,
                    'rotation': self.deimos_bounty_rotation,
                    'stage': self.deimos_bounty_stage,
                }
                
                self.deimos_bounty_drops.append(drop)
        
        report = self.verify_data(self.deimos_bounty_drops)
        
        return self.deimos_bounty_drops, report


class ZarimanBountyDropParser(BaseDropParser):
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


class EntratiLabDropParser(BaseDropParser):  # Albrecht's Laboratories
    def __init__(self, soup):
        super().__init__(soup)
        
        self.entrati_lab_bounty_drops = []
        
        self.entrati_lab_bounty_name = None
        self.entrati_lab_bounty_level = None
        self.entrati_lab_bounty_rotation = None
        self.entrati_lab_bounty_stage = None
    
    def parse(self):
        source_type, entrati_lab_bounty_table = self._parse_header('entratiLabRewards')
        source_type = 'Bounties'
        
        if not entrati_lab_bounty_table:
            return [], None

        for row in entrati_lab_bounty_table.find_all('tr'):
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
                        
                        self.entrati_lab_bounty_name = self.normalize_text(bounty_name)
                        self.entrati_lab_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.entrati_lab_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.entrati_lab_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                if self.entrati_lab_bounty_rotation:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Deimos',
                        'mission_name': 'Sanctum Anatomica',
                        'bounty_name': self.entrati_lab_bounty_name,
                        'bounty_level': self.entrati_lab_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'rotation': self.entrati_lab_bounty_rotation,
                        'stage': self.entrati_lab_bounty_stage,
                    }
                else:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Deimos',
                        'mission_name': 'Sanctum Anatomica',
                        'bounty_name': self.entrati_lab_bounty_name,
                        'bounty_level': self.entrati_lab_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'stage': self.entrati_lab_bounty_stage,
                    }
                
                self.entrati_lab_bounty_drops.append(drop)
        
        report = self.verify_data(self.entrati_lab_bounty_drops)
        
        return self.entrati_lab_bounty_drops, report


class HexBountyDropParser(BaseDropParser):
    def __init__(self, soup):
        super().__init__(soup)
        
        self.hex_bounty_drops = []
        
        self.hex_bounty_name = None
        self.hex_bounty_level = None
        self.hex_bounty_rotation = None
        self.hex_bounty_stage = None
    
    def parse(self):
        source_type, hex_bounty_table = self._parse_header('hexRewards')
        source_type = 'Bounties'
        
        if not hex_bounty_table:
            return [], None

        for row in hex_bounty_table.find_all('tr'):
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
                        
                        self.hex_bounty_name = self.normalize_text(bounty_name)
                        self.hex_bounty_level = self.normalize_text(bounty_level)
                    
                    continue
                
                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.hex_bounty_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Stage header ----
                if lowered.startswith('stage') or lowered.startswith('final'):
                    self.hex_bounty_stage = self.normalize_text(text)
                    continue
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) >= 3:
                item_name = td_cells[1].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[2].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                if self.hex_bounty_rotation:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Höllvania',  # TODO needs checking in game
                        'mission_name': 'Höllvania Central Mall',  # TODO needs checking in game
                        'bounty_name': self.hex_bounty_name,
                        'bounty_level': self.hex_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'rotation': self.hex_bounty_rotation,
                        'stage': self.hex_bounty_stage,
                    }
                else:
                    drop = {
                        'item': item_name,
                        'source_type': source_type,
                        'planet_name': 'Höllvania',  # TODO needs checking in game
                        'mission_name': 'Höllvania Central Mall',  # TODO needs checking in game
                        'bounty_name': self.hex_bounty_name,
                        'bounty_level': self.hex_bounty_level,
                        'rarity': rarity,
                        'chance': chance_number,
                        'stage': self.hex_bounty_stage,
                    }
                
                self.hex_bounty_drops.append(drop)
        
        report = self.verify_data(self.hex_bounty_drops)
        
        return self.hex_bounty_drops, report
