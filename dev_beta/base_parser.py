class BaseDropParser:
    """Foundation for all parsers"""
    def __init__(self, soup):
        self.soup = soup
        self.drops = []
    
    # === Shared Utilities ===
    def normalize_text(self, text):
        """Helper function used to normalize text during parsing.\n
        Normalize raw text input into either:
        - None
        or
        - Clean, meaningful string
        """
        
        # 1. Type safety
        if text is None:
            return None

        if not isinstance(text, str):
            return None
        
        # 2. Trim whitespace
        text = text.strip()
        
        # 3. Collapse semantic empties:
        if not text:
            return None
        
        SEMANTIC_EMPTY = {'-', '—', '–','n/a', 'na', 'none','null', 'unknown'}
        
        if text.lower() in SEMANTIC_EMPTY:
            return None
        
        # 4. Fix common encoding issues (best-effort)
        try:
            text = text.encode('latin1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass  # if it fails, keep original text
        
        # 5. Final trim (encoding fixes can add whitespace)
        text = text.strip()
        
        return text if text else None
    
    def filter_active_content(self, drops):
        """Filter out inactive mission modes (events, recalls, etc.)"""
        inactive_modes = {'EVENT', 'RECALL'}
        return [
            drop for drop in drops
            if drop.get('mission_mode') not in inactive_modes
        ]
        
    def verify_data(self, drops: list[dict]):
        report = {
            'summary': {},
            'counters': {},
            'errors': [],
            'warnings': [],
            'is_valid': False
        }
        
        counters = {}
        errors = []
        warnings = []
        
        unique_items = set()
        error_rows = set()
        
        for index, drop in enumerate(drops):
            # Summary
            if drop['item'] not in unique_items and drop['item'] is not None:
                unique_items.add(drop['item'])
            
            # Counters
            if drop['item'] is None:
                counters['missing_item'] = counters.get('missing_item', 0) + 1
                # Hard error, create errors report
                error = {
                    'index': index,
                    'item': None,
                    'reason': 'Missing item name'
                }
                errors.append(error)
            
            if drop['source_type'] is None:
                counters['missing_source_type'] = counters.get('missing_source_type', 0) + 1
                # Hard error, create errors report
                error = {
                    'index': index,
                    'item': drop['item'],
                    'reason': 'Missing source type'
                }
                errors.append(error)
            
            if drop['rarity'] is None:
                counters['missing_chance_rarity'] = counters.get('missing_chance_rarity', 0) + 1
                # Soft problem, create warnings report
                warning = {
                    'index': index,
                    'item': drop['item'],
                    'reason': 'Missing chance rarity'
                }
                warnings.append(warning)
            
            if drop['chance'] is None:
                counters['chance_missing'] = counters.get('chance_missing', 0) + 1
                # Hard error, create errors report
                error = {
                    'index': index,
                    'item': drop['item'],
                    'reason': 'Missing chance number'
                }
                errors.append(error)
            else:
                if drop['chance'] < 0 or drop['chance'] > 1:
                    counters['chance_out_of_range'] = counters.get('chance_out_of_range', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Chance number is out of range'
                    }
                    errors.append(error)
            
            if drop['source_type'] == 'Missions':
                if drop['mission_mode'] is None:
                    counters['missing_mission_mode'] = counters.get('missing_mission_mode', 0) + 1
                    # Hard error create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing mission mode'
                    }
                    errors.append(error)
                
                if drop['planet_name'] is None:
                    counters['missing_planet_name'] = counters.get('missing_planet_name', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing planet name'
                    }
                    errors.append(error)
                
                if drop['mission_name'] is None:
                    if drop['mission_descriptor'] and 'variant' in drop['mission_descriptor'].lower():
                        pass
                    else:
                        counters['missing_mission_name'] = counters.get('missing_mission_name', 0) + 1
                        # Hard error, create errors report
                        error = {
                            'index': index,
                            'item': drop['item'],
                            'mission_mode': drop['mission_mode'],
                            'planet_name': drop['planet_name'],
                            'mission_descriptor': drop['mission_descriptor'],
                            'reason': 'Missing mission name'
                        }
                        errors.append(error)

                if drop['mission_descriptor'] is None:
                    counters['missing_mission_descriptor'] = counters.get('missing_mission_descriptor', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing mission descriptor'
                    }
                    errors.append(error)
                
                if 'rotation' in drop:
                    if drop['rotation'] not in ('A', 'B', 'C', 'D'):
                        counters['missing_rotation'] = counters.get('missing_rotation', 0) + 1
                        # Hard error, create errors report
                        error = {
                            'index': index,
                            'item': drop['item'],
                            'reason': 'Missing mission rotation',
                            'mission_descriptor': drop['mission_descriptor']
                        }
                        errors.append(error)
            
            if drop['source_type'] == 'Relics':
                if drop['relic_tier'] is None:
                    counters['missing_relic_tier'] = counters.get('missing_relic_tier', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing relic tier'
                    }
                    errors.append(error)
                
                if drop['relic_name'] is None:
                    counters['missing_relic_name'] = counters.get('missing_relic_name', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing relic name'
                    }
                    errors.append(error)
                
                if drop['relic_refinement'] is None:
                    counters['missing_relic_refinement'] = counters.get('missing_relic_refinement', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'reason': 'Missing relic refinement'
                    }
                    errors.append(error)
                    
            if drop['source_type'] == 'Sorties':
                if drop['mission_name'] is None or drop['mission_name'] != 'Sortie':
                    counters['missing_sortie_mission_name'] = counters.get('missing_sortie_mission_name', 0) + 1
                    # Hard error, create errors report
                    error = {
                        'index': index,
                        'item': drop['item'],
                        'source_type': drop['source_type'],
                        'reason': 'Missing sortie mission name'
                    }
                    errors.append(error)
        
        for error in errors:
            error_rows.add(error['index'])
        
        if len(drops) == 0:
            return None
        
        # Summary
        summary = {}
        summary['total_rows'] = len(drops)
        summary['valid_rows'] = len(drops) - len(error_rows)
        summary['unique_items'] = len(unique_items)
        
        report['summary'] = summary
        report['counters'] = counters
        report['errors'] = errors
        report['warnings'] = warnings
        
        report['is_valid'] = len(errors) == 0
        
        return report
    
    def _parse_chance_text(self, chance_text):
        """Shared chance parsing"""
        # Look at both mission and relic parsing - find common pattern
        # Extract it here
        rarity = chance_text
        chance_number = None
        
        if '(' in chance_text and ')' in chance_text:
            rarity = chance_text.split('(')[0]
            rarity = self.normalize_text(rarity)
            
            percent_str = (
                chance_text.split('(', 1)[1]
                .replace(')', '')
                .replace('%', '')
                .strip()
            )
            try:
                chance_number = float(percent_str) / 100
            except ValueError:
                pass
        else:
            rarity = self.normalize_text(chance_text)
        
        return rarity, chance_number
    
    def _parse_header(self, header_id):
        header = self.soup.find('h3', id=header_id)
        if not header:
            print('Warning: No relic rewards section found')
            return []
        
        source_type = header.text.replace(':', '')
        source_type = self.normalize_text(source_type)

        table = header.find_next_sibling('table')
        if not table:
            print('Warning: No relic table found')
            return []
        
        return source_type, table
