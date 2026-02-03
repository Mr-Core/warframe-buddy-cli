import sys
from config import DEVELOPMENT_MODE
from orchestrator import DropOrchestrator
from search_engine import WarframeSearchEngine
from utils.helpers import clear_screen


def cli():
    clear_screen()
    
    print('=' * 60)
    print('WARFRAME DROP SEARCH ENGINE')
    print('=' * 60)
    
    if DEVELOPMENT_MODE:
        print('\n[DEVELOPMENT MODE]')
        print('Will use cached HTML file if available.')
    else:
        print('\n[PRODUCTION MODE]')
        print('Will fetch new data from web.')
    
    print('\nAvailable modes:')
    print('1. Fresh start - Parse, index, save everything')
    print('2. Search only - Load indexes and search')
    print('3. Abort - Quit the program')
    
    mode = input('\nSelect mode: ').strip()
    
    error_trigger = False
    search_engine = None
    
    if mode == '1':
        # MODE 1: Fresh start
        clear_screen()
        
        print('\n' + '=' * 60)
        print('FRESH START MODE')
        print('=' * 60)
        
        if not DEVELOPMENT_MODE:
            # Production: Fetch new data
            from services.fetch_data import fetch_data
            
            print('\nFetching latest data...')
            fetch_success, fetch_error = fetch_data()
            
            if fetch_success:
                print('✓ Data fetched successfully')
            else:
                print('✗ Error fetching latest data.')
                if fetch_error:
                    print(f'  ↳ {fetch_error}')
                sys.exit(1)
        else:
            print('DEVELOPMENT MODE IS ACTIVE! Skipping fetching new data.')
        
        # Parse everything
        print('\nParsing data...')
        orchestrator = DropOrchestrator()
        all_drops, len_all_drops = orchestrator.parse_all()
        
        # Print parse details
        print(f"\nParsing completed:")
        print(f"   Missions: {len_all_drops['mission_drops']} drops")
        print(f"   Relics: {len_all_drops['relic_drops']} drops")
        print(f"   Sorties: {len_all_drops['sortie_drops']} drops")
        print(f"   Cetus bounties: {len_all_drops['cetus_bounty_drops']} drops")
        print(f"   Orb Vallis bounties: {len_all_drops['solaris_bounty_drops']} drops")
        print(f"   Cambion Drift bounties: {len_all_drops['deimos_bounty_drops']} drops")
        print(f"   Zariman bounties: {len_all_drops['zariman_bounty_drops']} drops")
        print(f"   Albrecht's Laboratories bounties: {len_all_drops['entrati_lab_bounty_drops']} drops")
        print(f"   Hex bounties: {len_all_drops['hex_bounty_drops']} drops")
        print(f"   Dynamic Location Rewards: {len_all_drops['transient_drops']} drops")
        print(f"\n   Total drops: {len_all_drops['total_drops']} drops")
         
        # Generate a validation report
        report = orchestrator.get_validation_report()
        
        # Show validation summary
        overall = report["overall"]

        print(f"\nVALIDATION SUMMARY:")
        print(f"   Total drops: {overall['total_drops']}")
        print(f"   Data integrity: {overall['data_integrity']:.1%}")
        print(f"   Errors: {overall['error_count']}")
        print(f"   Warnings: {overall['warning_count']}")

        # Check if validation report contains any errors
        if report['overall']['error_count'] > 0 or report['overall']['warning_count'] > 0:
            error_trigger = True
            print("   CRITICAL: Errors found in data!")
        
        if error_trigger:
            if not DEVELOPMENT_MODE:
                print(
                    '\n⚠  Data contains errors and is not safe to use! ⚠\n'
                    'Run the program in DEVELOPMENT MODE to diagnose the problems.\n'
                )
                sys.exit(1)
            else:
                # If data has errors and dev mode is on, show detailed validation
                orchestrator.print_validation_details()
                sys.exit(1)
        
        # Ask to save parsed data
        save_parsed = input('\nSave parsed data to file? (y/n): ').lower()
        
        if save_parsed == 'y':
            save_response = orchestrator.save_parsed_data()
            print(save_response)
        else:
            print('\nSkipping saving parsed data to file.')
        
        # Create search engine with fresh data
        print('\nCreating search indexes...')
        search_engine = WarframeSearchEngine()
        create_indexes_reponse = search_engine.create_indexes_from_drops(all_drops)
        
        print(f'✓ Indexed {len(all_drops)} drops')
        print(create_indexes_reponse)
        
        # Always save indexes in Mode 1
        save_indexes_response = search_engine.save_indexes()
        print(save_indexes_response)
        
        # Show index status
        status = search_engine.get_index_status()
        print(f'\nIndex Status:')
        print(f'  - Items indexed: {status['total_items']}')
        print(f'  - Rebuilt at: {status['last_rebuild'] or 'Just now'}')
        
        input('\nPress any key to continue...')
    
    elif mode == '2':
        # MODE 2: Search only
        clear_screen()
        
        print('\n' + '=' * 60)
        print('SEARCH ONLY MODE')
        print('=' * 60)
        
        print('\nLoading search indexes...')
        search_engine = WarframeSearchEngine()
        
        # Load existing indexes
        load_index_success, load_index_response = search_engine.load_indexes()
        
        if load_index_success:
            print(load_index_response)
            print('\n✓ Indexes loaded successfully')
            input('\nPress any key to continue...')
        else:
            print(load_index_response)
            sys.exit(1)
    
    elif mode == '3':
        clear_screen()
        print('\nGoodbye!')
        sys.exit(1)
    
    else:
        clear_screen()
        print('Invalid mode selected!\n\nExiting.')
        sys.exit(1)
    
    # Start interactive search
    interactive_search(search_engine)


def interactive_search(search_engine) -> None:
    """Interactive search interface"""
    while True:
        clear_screen()
    
        print('\n' + '=' * 60)
        print('INTERACTIVE SEARCH')
        print('=' * 60)
        
        print('\nOptions:')
        print('  1. Search item (case-insensitive, partial match)')
        print('  2. Get item summary')
        print('  3. Exit')
        
        choice = input('\nSelect (1-3): ').strip()
        
        if choice == '':
            print('\nInvalid selection!')
            input('\nPress any key to continue...')
            continue
        
        if choice == '3':
            clear_screen()
            
            print('\nGoodbye!')
            break
        
        selected_item = None
        
        item_name = input('\nEnter item name: ').strip()
        if not item_name:
            print('\nItem name required!')
            input('\nPress any key to continue...')
            continue
        
        if choice == '1':
            # Case-insensitive search with partial matching
            clear_screen()
            
            print('=' * 60)
            print('SEARCH ITEM QUERY')
            print('=' * 60)
            
            search_results = []
            item_lower = item_name.lower()
            
            # Get all items from index
            all_items = list(search_engine.search_indexes['item_sources'].keys())
            
            # Find matching items (case-insensitive, partial match)
            matching_items = [item for item in all_items 
                            if item_lower in item.lower()]
            
            if not matching_items:
                print(f'\nNo items found matching "{item_name}"')
                input('\nPress any key to continue...')
                continue
            
            # Show matching items for user to choose from
            if len(matching_items) > 1:
                print(f'\nFound {len(matching_items)} matching items:')
                for i, item in enumerate(matching_items, 1):
                    print(f'  {i}. {item}')
                
                selection = input('\nSelect item number (or press Enter for all): ').strip()
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(matching_items):
                        selected_item = matching_items[idx]
                        search_results = search_engine.search_item(selected_item)
                    else:
                        print('\nInvalid selection!')
                        input('\nPress any key to continue...')
                        continue
                else:
                    # Search all matching items
                    search_results = []
                    for item in matching_items:
                        search_results.extend(search_engine.search_item(item))
            else:
                # Only one match
                selected_item = matching_items[0]
                print(f'\nSearching for: {selected_item}\n')
                search_results = search_engine.search_item(selected_item)
            
            # Apply source type filter if needed
            if search_results:
                print('Filter by source type:')
                print('  - Missions')
                print('  - Relics')
                print('  - Sorties')
                print('  - Bounties')
                print('  - Dynamic (Dynamic Location Rewards)')
                source_type = input('\nEnter source type (or press Enter for all): ').strip().lower()
                
                if source_type:
                    # Map user input to actual source types
                    source_type_map = {
                        'missions': 'Missions',
                        'relics': 'Relics',
                        'sorties': 'Sorties',
                        'bounties': 'Bounties',
                        'dynamic': 'Dynamic Location Rewards',
                    }
                    
                    actual_source_type = source_type_map.get(source_type)
                    if actual_source_type:
                        search_results = [d for d in search_results 
                                        if d['source_type'] == actual_source_type]
                        filter_display = actual_source_type.replace(' Location Rewards', '')
                    else:
                        print(f'\nUnknown source type: {source_type}')
                        print('Showing all results.')
                        filter_display = 'All'
                        input('\nPress any key to continue...')
                else:
                    filter_display = 'All'
                
                # Show results
                if search_results:
                    display_results(search_results, selected_item, filter_display)
                else:
                    print('\nNo results found with selected filters.')
                    input('\nPress any key to continue...')
            else:
                print('\nNo results found.')
                input('\nPress any key to continue...')
        
        elif choice == '2':
            # Case-insensitive summary
            clear_screen()
            
            print('=' * 60)
            print('GET ITEM SUMMARY QUERY')
            print('=' * 60)
            
            all_items = list(search_engine.search_indexes['item_sources'].keys())
            item_lower = item_name.lower()
            
            matching_items = [item for item in all_items 
                            if item_lower in item.lower()]
            
            if not matching_items:
                print(f'No items found matching "{item_name}"')
                input('\nPress any key to continue...')
                continue
            
            if len(matching_items) > 1:
                print(f'\nFound {len(matching_items)} matching items:')
                for i, item in enumerate(matching_items, 1):
                    print(f'  {i}. {item}')
                
                selection = input('\nSelect item number: ').strip()
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(matching_items):
                        selected_item = matching_items[idx]
                        summary = search_engine.get_item_summary(selected_item)
                        display_summary(summary)
                    else:
                        print('\nInvalid selection!')
                        input('\nPress any key to continue...')
                else:
                    print('\nInvalid input!')
                    input('\nPress any key to continue...')
            else:
                summary = search_engine.get_item_summary(matching_items[0])
                display_summary(summary)


def display_results(results: list, item_name: str | None, filter: str) -> None:
    """Display search results nicely"""
    clear_screen()
    
    print('=' * 60)
    print('SEARCH ITEM RESULTS')
    print('=' * 60)
    
    if not results:
        print('No results found.')
        input('\nPress any key to continue...')
        return
    
    if item_name == '' or item_name == None:
        item_name = 'All'
    if filter == '':
        filter = 'All'
    
    print(f'\nDisplaying results for "{item_name}" with applied filter "{filter}"')
    
    print(f'\nFound {len(results)} result(s):')
    print('-' * 80)
    
    for i, drop in enumerate(results, 1):
        if i <= 20:
            chance = drop.get('chance', 0)
            rarity = drop.get('rarity', 'Unknown')
            
            if drop['source_type'] == 'Missions':
                source = f'Missions\n     Planet: {drop.get('planet_name', '?')}\n     Mission: {drop.get('mission_name', '?')}'
            
            elif drop['source_type'] == 'Relics':
                source = f'Relics\n     Tier: {drop.get('relic_tier', '?')}\n     Name: {drop.get('relic_name', '?')}'
            
            elif drop['source_type'] == 'Sorties':
                source = drop.get('mission_name', 'Sortie')
            
            elif drop['source_type'] == 'Bounties':
                source = f'Bounties\n     Planet: {drop.get('planet_name', '?')}\n     Mission: {drop.get('mission_name', '?')}'
            
            elif drop['source_type'] == 'Dynamic Location Rewards':
                source = f'Dynamic Location Rewards\n     Mission name: {drop.get('mission_name', '?')}'
            
            else:
                source = 'Unknown'
            
            print(f'{i:3}. {drop['item']}')
            print(f'     Source: {source}')
            
            # Additional info
            if drop['source_type'] == 'Missions' and drop.get('mission_type'):
                print(f'     Type: {drop['mission_type']}')
                if drop.get('rotation'):
                    print(f'     Rotation: {drop['rotation']}')
            
            if drop['source_type'] == 'Relics' and drop.get('relic_refinement'):
                print(f'     Refinement: {drop['relic_refinement']}')
            
            if drop['source_type'] == 'Bounties':
                print(f'     Bounty name: {drop['bounty_name']}')
                print(f'     Bounty level: {drop['bounty_level']}')
                if drop.get('rotation'):
                    print(f'     Rotation: {drop['rotation']}')
                print(f'     Stage: {drop['stage']}')
            
            if drop['source_type'] == 'Dynamic Location Rewards':
                if drop.get('rotation'):
                    print(f'     Rotation: {drop['rotation']}')
            
            print(f'     Chance: {chance:.1%} ({rarity})')
            
            print()
        else:
            print(f'\n... and {len(results) - 20} more results. Use "Get item summary" for best drop locations.')
            break
    
    print('-' * 80)
    print('End of search results.')
    
    input('\nPress any key to continue...')


def display_summary(summary: dict) -> None:
    """Display item summary"""
    clear_screen()
    
    print('=' * 60)
    print('SEARCH ITEM RESULTS')
    print('=' * 60)
    
    if summary['total_sources'] == 0:
        print('Item not found in database.')
        input('\nPress any key to continue...')
        return
    
    print(f'\nSummary report for "{summary['item']}"')
    print('-' * 80)
    print(f'\nTotal sources: {summary['total_sources']}')
    
    if summary['best_source']:
        best = summary['best_source']
        print(f'Best chance: {summary['best_chance']:.1%}')
        print(f'Best source: {best['source_type']}')
        
        if best['source_type'] == 'Missions':
            if 'rotation' in best:
                print(f'   Location: {best.get('planet_name')} / {best.get('mission_name')} / {best.get('mission_type')} - Rotation: {best.get('rotation')}')
            else:
                print(f'   Location: {best.get('planet_name')} / {best.get('mission_name')} / {best.get('mission_type')}')
        
        elif best['source_type'] == 'Relics':
            print(f'      Relic: {best.get('relic_tier')} {best.get('relic_name')} {best.get('relic_refinement')}')
        
        elif best['source_type'] == 'Bounties':
            if 'rotation' in best:
                print(f'   Location: {best.get('planet_name')} / {best.get('mission_name')} / {best.get('bounty_name')} / {best.get('bounty_level')} / Rotation {best.get('rotation')} / {best.get('stage')}')
            else:
                print(f'   Location: {best.get('planet_name')} / {best.get('mission_name')} / {best.get('bounty_name')} / {best.get('bounty_level')} / {best.get('stage')}')
    
    print('-' * 80)
    
    print('\nBreakdown legend:')
    print('  - Missions: Planet / Mission name / Mission type / Rotation -> Drop chance')
    print('  - Relics: Relic tier / Relic name / Relic refinement -> Drop chance')
    print('  - Bounties: Planet / Mission name / Bounty name / Bounty level / Rotation / Stage -> Drop chance')
    
    print('-' * 80)
    
    print('\nOther good drop locations:')
    
    # Breakdown
    if summary['missions']:
        print(f'\nMissions ({len(summary['missions'])} sources):')
        for mission in summary['missions'][:10]:
            if 'rotation' in mission:
                print(f'  • {mission['planet']} / {mission['mission']} / {mission['type']} / {mission['rotation']} -> {mission['chance']:.1%}')
            else:
                print(f'  • {mission['planet']} / {mission['mission']} / {mission['type']} -> {mission['chance']:.1%}')
        if len(summary['missions']) > 10:
            print(f'  ... and {len(summary['missions']) - 10} more')
    
    if summary['relics']:
        print(f'\nRelics ({len(summary['relics'])} sources):')
        for relic in summary['relics'][:10]:
            print(f'  • {relic['tier']} {relic['name']} {relic['refinement']} -> {relic['chance']:.1%}')
        if len(summary['relics']) > 10:
            print(f'  ... and {len(summary['relics']) - 10} more')
    
    if summary['sorties']:
        print(f'\nSorties ({len(summary['sorties'])} sources)')
        for sortie in summary['sorties'][:3]:
            print(f'  • Chance: {sortie['chance']:.1%}')
    
    if summary['bounties']:
        print(f'\nBounties ({len(summary['bounties'])} sources):')
        for bounty in summary['bounties'][:10]:
            if bounty.get('rotation'):
                print(f'  • {bounty['planet']} / {bounty['mission']} / {bounty['name']} / {bounty['level']} / Rotation {bounty['rotation']} / {bounty['stage']} -> {bounty['chance']:.1%}')
            else:
                print(f'  • {bounty['planet']} / {bounty['mission']} / {bounty['name']} / {bounty['level']} / {bounty['stage']} -> {bounty['chance']:.1%}')
        if len(summary['bounties']) > 10:
            print(f'  ... and {len(summary['bounties']) - 10} more')
    
    print()
    print('-' * 80)
    print('End of search results.')
    
    input('\nPress any key to continue...')
