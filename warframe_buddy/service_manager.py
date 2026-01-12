import schedule
import time
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add the current directory to Python path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from search_engine import WarframeSearchEngine
from orchestrator import DropOrchestrator
from fetch_data import fetch_data
from config import (
    DEVELOPMENT_MODE,
    HTML_FILE,
    PARSED_DATA_FILE,
    INDEXED_DATA_FILE,
    DAILY_UPDATE_TIME,
    HEALTH_CHECK_TIME,
)


class WarframeDataService:
    """Main service manager for production deployment"""

    def __init__(self):
        self.search_engine = WarframeSearchEngine()
        self.is_running = False

    def start(self):
        """Start the service"""
        print('=' * 60)
        print('WARFRAME DATA SERVICE - Starting...')
        print('=' * 60)

        # Load or create initial indexes
        self._initialize_indexes()

        # Start scheduled updates (if not in development mode)
        if not DEVELOPMENT_MODE:
            self._setup_scheduler()
            print('✓ Daily scheduler enabled')

        # Mark service as running
        self.is_running = True
        status = self.get_status()
        print('\n' + '=' * 60)
        print('SERVICE STATUS:')
        print('=' * 60)
        print(f'  Running: {'Yes' if status['running'] else 'No'}')
        print(f'  Index loaded: {'Yes' if status['index_loaded'] else 'No'}')
        print(f'  Total items: {status['total_items']}')
        print(f'  Last rebuild: {status['last_rebuild'] or 'Never'}')
        print(f'  Development mode: {status['development_mode']}')
        print('=' * 60)

        if status['index_loaded']:
            print('\n✓ Service is ready! You can now:')
            print('  - Add Flask web server')
            print('  - Add Telegram bot')
            print('  - Start handling requests')
        else:
            print('\n⚠  Service started but indexes not loaded.')
            print('  Run a manual update or check data files.')

        # Placeholder to start:
        # - Flask web server
        # - Telegram bot
        # But for now, just keep running
        self._keep_alive()

    def _initialize_indexes(self):
        """Load existing indexes or create new ones"""
        print('\nInitializing search indexes...')

        # Check if data files exist
        has_index_file = os.path.exists(INDEXED_DATA_FILE)
        has_parsed_file = os.path.exists(PARSED_DATA_FILE)
        has_html_file = os.path.exists(HTML_FILE)

        print(f'  Index file: {'Found' if has_index_file else 'Missing'}')
        print(f'  Parsed data: {'Found' if has_parsed_file else 'Missing'}')
        print(f'  HTML data: {'Found' if has_html_file else 'Missing'}')

        # Strategy 1: Try to load existing indexes
        if has_index_file:
            print('\nAttempting to load existing indexes...')
            if self.search_engine.load_indexes():
                print('✓ Loaded existing indexes')
                return

        # Strategy 2: Try to rebuild from parsed data
        if has_parsed_file:
            print('\nNo indexes found, attempting to rebuild from parsed data...')
            if self.search_engine.rebuild_from_parsed_file():
                print('✓ Rebuilt indexes from parsed data')
                return

        # Strategy 3: Try to parse existing HTML
        if has_html_file:
            print('\nNo parsed data found, parsing existing HTML...')
            self._perform_full_update(force_fetch=False)
            return

        # Strategy 4: Full fetch and parse (last resort)
        print('\nNo data files found, performing full initialization...')
        self._perform_full_update(force_fetch=True)

    def _perform_full_update(self, force_fetch=True):
        """Do a complete data update"""
        print('\n' + '=' * 40)
        print('PERFORMING FULL DATA UPDATE')
        print('=' * 40)

        # Fetch new data if needed
        if force_fetch and not DEVELOPMENT_MODE:
            print('\n1. Fetching new data...')
            try:
                fetch_data()
                print('✓ Data fetched successfully')
            except Exception as e:
                print(f'✗ Failed to fetch data: {e}')
                if os.path.exists(HTML_FILE):
                    print('Using existing HTML file...')
                else:
                    print('No data available. Service cannot start.')
                    return False

        # Parse the data
        print('\n2. Parsing data...')
        try:
            orchestrator = DropOrchestrator()
            all_drops = orchestrator.parse_all()
            print('✓ Data parsed successfully')

            # Show validation
            orchestrator.print_validation_summary()

        except Exception as e:
            print(f'✗ Failed to parse data: {e}')
            return False

        # Save parsed data (for future rebuilds)
        print('\n3. Saving parsed data...')
        try:
            orchestrator.save_parsed_data()
            print('✓ Parsed data saved')
        except Exception as e:
            print(f'✗ Failed to save parsed data: {e}')

        # Create indexes
        print('\n4. Creating indexes...')
        try:
            self.search_engine.create_indexes_from_drops(all_drops)
            self.search_engine.save_indexes()
            print('✓ Indexes created and saved')
            return True

        except Exception as e:
            print(f'✗ Failed to create indexes: {e}')
            return False

    def _setup_scheduler(self):
        """Setup daily update scheduler"""
        # Schedule daily update at 3 AM
        schedule.every().day.at(DAILY_UPDATE_TIME).do(self._daily_update)

        # Also schedule a weekly health check
        schedule.every().sunday.at(HEALTH_CHECK_TIME).do(self._health_check)

        print(f'✓ Scheduler enabled')
        print(f'  - Daily updates: {DAILY_UPDATE_TIME}')
        print(f'  - Health checks: Sunday {HEALTH_CHECK_TIME}')

    def _daily_update(self):
        """Perform daily data update"""
        print(
            f'\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily update started'
        )

        try:
            success = self._perform_full_update(force_fetch=True)
            if success:
                print(
                    f'[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Daily update completed'
                )
            else:
                print(
                    f'[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Daily update failed'
                )

        except Exception as e:
            print(
                f'[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Daily update error: {e}'
            )

    def _health_check(self):
        """Weekly health check"""
        print(f'\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Health check')

        status = self.get_status()
        print(f'  Index loaded: {status['index_loaded']}')
        print(f'  Total items: {status['total_items']}')
        print(f'  Last rebuild: {status['last_rebuild']}')

        # Check data freshness
        if os.path.exists(HTML_FILE):
            file_age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(HTML_FILE)
            )
            print(f'  Data age: {file_age.days} days, {file_age.seconds//3600} hours')

            if file_age > timedelta(days=7):
                print('  ⚠  Data is older than 7 days')

    def _should_update_data(self):
        """Check if data is older than 24 hours"""
        if not os.path.exists(HTML_FILE):
            return True

        file_time = datetime.fromtimestamp(os.path.getmtime(HTML_FILE))
        return datetime.now() - file_time > timedelta(hours=24)

    def _keep_alive(self):
        """Keep service running with simple input handling"""
        print('\n' + '=' * 60)
        print('SERVICE RUNNING')
        print('=' * 60)
        print('Commands:')
        print('  s - Show service status')
        print('  u - Manually trigger update')
        print('  q - Stop the service')
        print('=' * 60)
        print('\nEnter command (s/u/q): ', end='', flush=True)

        try:
            while self.is_running:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Simple non-blocking input check
                try:
                    import msvcrt  # Windows
                    if msvcrt.kbhit():
                        command = msvcrt.getch().decode('utf-8').lower()
                        print(command)  # Echo the character
                        
                        if command == 's':
                            self._show_status()
                            print('\nEnter command (s/u/q): ', end='', flush=True)
                        elif command == 'u':
                            print('\nManual update triggered...')
                            self._daily_update()
                            print('\nEnter command (s/u/q): ', end='', flush=True)
                        elif command == 'q':
                            print('\nShutting down...')
                            self.stop()
                            break
                            
                except ImportError:
                    try:
                        import sys
                        import select
                        
                        # Unix/Linux/Mac
                        if select.select([sys.stdin], [], [], 0)[0]:
                            command = sys.stdin.read(1).lower()
                            
                            if command == 's':
                                self._show_status()
                                print('\nEnter command (s/u/q): ', end='', flush=True)
                            elif command == 'u':
                                print('\nManual update triggered...')
                                self._daily_update()
                                print('\nEnter command (s/u/q): ', end='', flush=True)
                            elif command == 'q':
                                print('\nShutting down...')
                                self.stop()
                                break
                    except:
                        # Fallback: just sleep if input methods fail
                        pass
                
                time.sleep(0.1)  # Small sleep to prevent CPU overuse

        except KeyboardInterrupt:
            print('\n\nShutdown requested via Ctrl+C...')
            self.stop()

    def _show_status(self):
        """Show current status"""
        status = self.get_status()
        print('\n' + '=' * 40)
        print('CURRENT STATUS')
        print('=' * 40)
        print(f'Service running: {'Yes' if status['running'] else 'No'}')
        print(f'Index loaded: {'Yes' if status['index_loaded'] else 'No'}')
        print(f'Total items: {status['total_items']}')
        print(f'Last rebuild: {status['last_rebuild'] or 'Never'}')
        print(f'Development mode: {status['development_mode']}')
        print('=' * 40)

    def stop(self):
        """Stop the service"""
        self.is_running = False
        print('\nService stopped.')

    def get_status(self):
        """Get service status"""
        index_status = self.search_engine.get_index_status()

        return {
            'running': self.is_running,
            'index_loaded': index_status['loaded'],
            'total_items': index_status['total_items'],
            'last_rebuild': index_status['last_rebuild'],
            'development_mode': DEVELOPMENT_MODE,
        }


# Simple command-line interface
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Warframe Data Service')
    parser.add_argument(
        '--no-schedule', action='store_true', help='Run without scheduled updates'
    )
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Force a full data update on startup',
    )

    args = parser.parse_args()

    # Create and start service
    service = WarframeDataService()

    # Handle arguments
    if args.force_update:
        print('\nForce update requested...')
        service._perform_full_update(force_fetch=True)

    if args.no_schedule:
        print('\nRunning without scheduler (development mode)')
        service.DEVELOPMENT_MODE = True

    service.start()
