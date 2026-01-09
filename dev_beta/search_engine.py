# search_engine.py
import json
from datetime import datetime
from collections import defaultdict
from config import INDEXED_DATA_FILE, PARSED_DATA_FILE

class WarframeSearchEngine:
    """Specialized search engine for Warframe drop data"""
    
    def __init__(self):
        self.search_indexes = {}
    
    # ==== INDEXING ====
    
    def create_indexes(self, all_drops):
        """Create optimized indexes"""
        print('Creating search indexes...')
        
        # Reset indexes
        self.search_indexes = {
            'item_sources': defaultdict(list),
            'item_missions': defaultdict(list),
            'item_relics': defaultdict(list),
            'item_sorties': defaultdict(list),
            'mission_planets': defaultdict(list),
            'relic_tiers': defaultdict(list),
            'item_lowercase': {},  # NEW: For case-insensitive lookup
        }
        
        # Build all indexes in one pass
        for drop in all_drops:
            item = drop['item']
            source_type = drop['source_type']
            
            # Store lowercase version for case-insensitive search
            item_lower = item.lower()
            if item_lower not in self.search_indexes['item_lowercase']:
                self.search_indexes['item_lowercase'][item_lower] = item
            
            # Original item indexing
            self.search_indexes['item_sources'][item].append(drop)
            
            if source_type == 'Missions':
                self.search_indexes['item_missions'][item].append(drop)
                
                planet = drop.get('planet_name')
                if planet:
                    key = f'{item}::{planet}'
                    self.search_indexes['mission_planets'][key].append(drop)
            
            elif source_type == 'Relics':
                self.search_indexes['item_relics'][item].append(drop)
                
                tier = drop.get('relic_tier')
                if tier:
                    key = f'{item}::{tier}'
                    self.search_indexes['relic_tiers'][key].append(drop)
            
            elif source_type == 'Sorties':
                self.search_indexes['item_sorties'][item].append(drop)
        
        print(f'✓ Indexed {len(all_drops)} drops')
        print(f'  - Unique items: {len(self.search_indexes['item_sources'])}')
    
    def save_indexes(self):
        """Save indexes to file"""
        serializable_indexes = {}
        for index_name, index_data in self.search_indexes.items():
            if isinstance(index_data, defaultdict):
                serializable_indexes[index_name] = dict(index_data)
            else:
                serializable_indexes[index_name] = index_data
        
        data = {
            'created_at': datetime.now().isoformat(),
            'indexes': serializable_indexes
        }
        
        with open(INDEXED_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f'✓ Saved indexes to {INDEXED_DATA_FILE}')
    
    def load_indexes(self):
        """Load indexes from file"""
        with open(INDEXED_DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # Convert back to defaultdict for lists, keep dict for others
        for index_name, index_data in data['indexes'].items():
            if index_name in ['item_sources', 'item_missions', 'item_relics', 
                            'item_sorties', 'mission_planets', 'relic_tiers']:
                self.search_indexes[index_name] = defaultdict(list, index_data)
            else:
                self.search_indexes[index_name] = index_data
        
        print(f'✓ Loaded indexes (created {data['created_at']})')
        print(f'  - Unique items: {len(self.search_indexes['item_sources'])}')
    
    # ==== SEARCH ====
    
    def search_item(self, item_name, source_type=None, **filters):
        """
        Search for exact item name
        For case-insensitive/partial search, use find_matching_items() first
        """
        if not self.search_indexes:
            raise ValueError('No indexes loaded.')
        
        # Get base results
        if source_type == 'missions':
            results = self.search_indexes['item_missions'].get(item_name, [])
            
            planet = filters.get('planet')
            if planet:
                key = f'{item_name}::{planet}'
                results = self.search_indexes['mission_planets'].get(key, [])
            
            mission_mode = filters.get('mission_mode')
            if mission_mode:
                results = [d for d in results 
                          if d.get('mission_mode') == mission_mode]
        
        elif source_type == 'relics':
            results = self.search_indexes['item_relics'].get(item_name, [])
            
            tier = filters.get('tier')
            if tier:
                key = f'{item_name}::{tier}'
                results = self.search_indexes['relic_tiers'].get(key, [])
            
            relic_name = filters.get('relic_name')
            if relic_name:
                results = [d for d in results 
                          if d.get('relic_name') == relic_name]
            
            refinement = filters.get('refinement')
            if refinement:
                results = [d for d in results 
                          if d.get('relic_refinement') == refinement]
        
        elif source_type == 'sorties':
            results = self.search_indexes['item_sorties'].get(item_name, [])
        
        else:  # Search everywhere
            results = self.search_indexes['item_sources'].get(item_name, [])
        
        # Apply chance filters
        min_chance = filters.get('min_chance')
        if min_chance is not None:
            results = [d for d in results 
                      if d.get('chance') is not None and d['chance'] >= min_chance]
        
        max_chance = filters.get('max_chance')
        if max_chance is not None:
            results = [d for d in results 
                      if d.get('chance') is not None and d['chance'] <= max_chance]
        
        # Sort by best chance
        results.sort(key=lambda x: x.get('chance', 0), reverse=True)
        
        return results
    
    def find_matching_items(self, search_term):
        """Find items matching search term (case-insensitive, partial match)"""
        search_lower = search_term.lower()
        matching = []
        
        # Check lowercase index first
        for item_lower, item_actual in self.search_indexes.get('item_lowercase', {}).items():
            if search_lower in item_lower:
                matching.append(item_actual)
        
        return matching
    
    def get_item_summary(self, item_name):
        """Get summary for exact item name"""
        summary = {
            'item': item_name,
            'total_sources': 0,
            'missions': [],
            'relics': [],
            'sorties': [],
            'best_chance': 0,
            'best_source': None
        }
        
        all_sources = self.search_indexes['item_sources'].get(item_name, [])
        if not all_sources:
            return summary
        
        summary['total_sources'] = len(all_sources)
        
        for drop in all_sources:
            if drop['source_type'] == 'Missions':
                summary['missions'].append({
                    'planet': drop.get('planet_name'),
                    'mission': drop.get('mission_name'),
                    'chance': drop.get('chance'),
                    'rarity': drop.get('rarity')
                })
            elif drop['source_type'] == 'Relics':
                summary['relics'].append({
                    'tier': drop.get('relic_tier'),
                    'name': drop.get('relic_name'),
                    'refinement': drop.get('relic_refinement'),
                    'chance': drop.get('chance'),
                    'rarity': drop.get('rarity')
                })
            elif drop['source_type'] == 'Sorties':
                summary['sorties'].append({
                    'chance': drop.get('chance'),
                    'rarity': drop.get('rarity')
                })
            
            if drop.get('chance', 0) > summary['best_chance']:
                summary['best_chance'] = drop.get('chance', 0)
                summary['best_source'] = drop
        
        summary_sorted = summary.copy()
        summary_sorted['missions'].sort(key=lambda x: x.get('chance', 0), reverse=True)
        summary_sorted['relics'].sort(key=lambda x: x.get('chance', 0), reverse=True)
        summary_sorted['sorties'].sort(key=lambda x: x.get('chance', 0), reverse=True)
        
        return summary_sorted
