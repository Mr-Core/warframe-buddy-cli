from base_parser import BaseDropParser


class MissionDropParser(BaseDropParser):
    """Inherited parser class for Mission drops"""
    def __init__(self, soup):
        super().__init__(soup)
        
        self.mission_drops = []
        self.filtered_mission_drops = []

        self.current_mission_mode = None
        self.current_planet_name = None
        self.current_mission_name = None
        self.current_mission_descriptor = None
        self.current_mission_rotation = None
        
    def parse(self):
        source_type, missions_table = self._parse_header('missionRewards')
        
        if not source_type or not missions_table:
            return [], None
        
        for row in missions_table.find_all('tr'):
            th_cells = row.find_all('th')
            td_cells = row.find_all('td')

            # -------------------------
            # CONTEXT ROWS (headers)
            # -------------------------
            if th_cells:
                text = th_cells[0].text.strip()
                lowered = text.lower()

                # ---- Rotation header ----
                if lowered.startswith('rotation'):
                    self.current_mission_rotation = self.normalize_text(text.split()[-1])
                    continue
                
                # ---- Variant missions ----
                if 'variant' in lowered:
                    if '/' in text:
                        planet_part = text.split('/', 1)[0]
                        self.current_planet_name = self.normalize_text(planet_part)
                    else:
                        self.current_planet_name = None
                    
                    self.current_mission_mode = 'CONCLAVE'
                    self.current_mission_name = None
                    self.current_mission_descriptor = self.normalize_text(text)
                    self.current_mission_rotation = None
                    continue
                
                # ---- Normal mission mode detection ----
                if 'conclave' in lowered:
                    self.current_mission_mode = 'CONCLAVE'
                elif 'recall' in lowered:
                    self.current_mission_mode = 'RECALL'
                elif 'event' in lowered:
                    self.current_mission_mode = 'EVENT'
                else:
                    self.current_mission_mode = 'PVE'
                
                # ---- Mission header parsing ----
                if '(' in text and ')' in text:
                    # Find the last '(' to handle nested parentheses if any
                    left, right = text.rsplit('(', 1)
                    
                    # Clean up - remove extra spaces
                    left = left.strip()
                    right = right.replace(')', '').strip()
                    
                    self.current_mission_descriptor = self.normalize_text(right)
                    
                    if '/' in left:
                        planet_part, node_part = left.split('/', 1)
                        self.current_planet_name = self.normalize_text(planet_part.strip())
                        
                        # Handle colons in mission names
                        if ':' in node_part:
                            mission_type, mission_details = node_part.split(':', 1)
                            self.current_mission_name = self.normalize_text(mission_type.strip())
                            
                            # Clean mission details (might have extra spaces)
                            mission_details = mission_details.strip()
                            
                            # Combine with descriptor if both exist
                            if mission_details and self.current_mission_descriptor:
                                self.current_mission_descriptor = self.normalize_text(
                                    f'{mission_details} {self.current_mission_descriptor}'
                                )
                            elif mission_details:
                                self.current_mission_descriptor = self.normalize_text(mission_details)
                            # If no mission_details, descriptor stays as is (e.g., "Normal")
                        else:
                            self.current_mission_name = self.normalize_text(node_part.strip())
                    else:
                        self.current_planet_name = None
                        self.current_mission_name = self.normalize_text(left)
                    
                    self.current_mission_rotation = None
                else:
                    # Handle headers without parentheses
                    if '/' in text:
                        planet_part, node_part = text.split('/', 1)
                        self.current_planet_name = self.normalize_text(planet_part)
                        self.current_mission_name = self.normalize_text(node_part)
                        self.current_mission_descriptor = None
                    else:
                        self.current_planet_name = None
                        self.current_mission_name = self.normalize_text(text)
                        self.current_mission_descriptor = None
            
            # -------------------------
            # DROP ROWS
            # -------------------------
            elif len(td_cells) == 2:
                item_name = td_cells[0].text
                item_name = self.normalize_text(item_name)

                chance_text = td_cells[1].text.strip()
                
                rarity, chance_number = self._parse_chance_text(chance_text)

                drop = {
                    'item': item_name,
                    'source_type': source_type,
                    'mission_mode': self.current_mission_mode,
                    'planet_name': self.current_planet_name,
                    'mission_name': self.current_mission_name,
                    'mission_descriptor': self.current_mission_descriptor,
                    'rarity': rarity,
                    'chance': chance_number
                }
                
                # Rotation is optional -> include only if present
                if self.current_mission_rotation is not None:
                    drop['rotation'] = self.current_mission_rotation
                
                self.mission_drops.append(drop)
        
        self.filtered_mission_drops = self.filter_active_content(self.mission_drops)

        report = self.verify_data(self.filtered_mission_drops)
        
        return self.filtered_mission_drops, report
