"""
Development-friendly service manager for Warframe Buddy Discord Bot
Run as: python -m services.service_manager [start|stop|restart|status]
"""
import os
import sys
import time
import subprocess
from pathlib import Path


class DevServiceManager:
    """Simple service manager for development on VPS"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.pid_file = self.base_dir / '.bot.pid'
        self.process = None
        self.running = False
        
        # Ensure we're in the right directory
        os.chdir(self.base_dir)
    
    def start(self):
        """Start the bot in background"""
        if self.is_running():
            print('⚠️  Bot is already running')
            return False
        
        print('🚀 Starting Warframe Buddy Discord Bot...')
        
        try:
            # Start bot process
            self.process = subprocess.Popen(
                [sys.executable, '-m', 'interfaces.discord_bot'],
                cwd=self.base_dir,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            
            # Start output reader thread
            import threading
            thread = threading.Thread(target=self._read_output, daemon=True)
            thread.start()
            
            print(f'✅ Bot started with PID: {self.process.pid}')
            print('📝 View logs: tail -f logs/bot.log')
            return True
            
        except Exception as e:
            print(f'❌ Failed to start bot: {e}')
            return False
    
    def _read_output(self):
        """Read and log bot output"""
        log_file = self.base_dir / 'logs' / 'bot.log'
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a') as log_f:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f'[{timestamp}] {line}'
                    log_f.write(log_entry)
                    log_f.flush()
    
    def stop(self, force=False):
        """Stop the bot"""
        if not self.is_running():
            print('⚠️  Bot is not running')
            return True
        
        print('🛑 Stopping bot...')
        
        try:
            # Try graceful shutdown
            if self.process:
                self.process.terminate()
                
                # Wait for graceful shutdown
                for i in range(10):
                    if self.process.poll() is not None:
                        break
                    time.sleep(1)
                    if i == 5:
                        print('⏳ Waiting for graceful shutdown...')
                
                # Force kill if needed
                if self.process.poll() is None and force:
                    print('⚠️  Force killing bot...')
                    self.process.kill()
                    self.process.wait()
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            self.process = None
            print('✅ Bot stopped')
            return True
            
        except Exception as e:
            print(f'❌ Error stopping bot: {e}')
            return False
    
    def restart(self):
        """Restart the bot"""
        print('🔁 Restarting bot...')
        self.stop()
        time.sleep(2)
        return self.start()
    
    def status(self):
        """Check bot status"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process exists
                try:
                    os.kill(pid, 0)  # Signal 0 checks process existence
                    
                    # Try to get process info
                    try:
                        with open(f'/proc/{pid}/stat', 'r') as stat_f:
                            stats = stat_f.read().split()
                            # Calculate uptime
                            import time
                            with open('/proc/uptime', 'r') as uptime_f:
                                uptime = float(uptime_f.read().split()[0])
                            start_time = int(stats[21]) / 100
                            process_uptime = uptime - start_time
                            
                            hours = int(process_uptime // 3600)
                            minutes = int((process_uptime % 3600) // 60)
                            
                            uptime_str = f'{hours}h {minutes}m' if hours > 0 else f'{minutes}m'
                            
                            return {
                                'running': True,
                                'pid': pid,
                                'uptime': uptime_str
                            }
                    except:
                        return {'running': True, 'pid': pid}
                        
                except OSError:
                    # PID file exists but process is dead
                    return {'running': False, 'stale_pid': True}
            
            except Exception as e:
                return {'running': False, 'error': str(e)}
        
        return {'running': False}
    
    def is_running(self):
        """Quick running check"""
        status = self.status()
        return status.get('running', False)
    
    def logs(self, lines=50, follow=False):
        """Show bot logs"""
        log_file = self.base_dir / 'logs' / 'bot.log'
        
        if not log_file.exists():
            print('No logs found yet')
            return
        
        try:
            if follow:
                # Tail -f behavior
                import subprocess
                subprocess.run(['tail', '-f', str(log_file)])
            else:
                # Show last N lines
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    for line in all_lines[-lines:]:
                        print(line, end='')
        except Exception as e:
            print(f'Error reading logs: {e}')

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Warframe Buddy Development Service Manager'
    )
    parser.add_argument('action', 
                       choices=['start', 'stop', 'restart', 'status', 'logs', 'run'],
                       help='Action to perform')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force stop (kill)')
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='Number of log lines to show')
    parser.add_argument('--follow', action='store_true',
                       help='Follow log output')
    
    args = parser.parse_args()
    
    manager = DevServiceManager()
    
    if args.action == 'start':
        manager.start()
    
    elif args.action == 'stop':
        manager.stop(force=args.force)
    
    elif args.action == 'restart':
        manager.restart()
    
    elif args.action == 'status':
        status = manager.status()
        if status.get('running'):
            print(f'✅ Bot is running (PID: {status['pid']})')
            if 'uptime' in status:
                print(f'   Uptime: {status['uptime']}')
        elif status.get('stale_pid'):
            print('⚠️  Stale PID file found (process not running)')
        else:
            print('❌ Bot is not running')
    
    elif args.action == 'logs':
        manager.logs(lines=args.lines, follow=args.follow)
    
    elif args.action == 'run':
        # Direct run (foreground)
        print('Running bot in foreground... (Ctrl+C to stop)')
        try:
            subprocess.run([sys.executable, '-m', 'interfaces.discord_bot'], 
                          cwd=manager.base_dir)
        except KeyboardInterrupt:
            print('\nBot stopped')

if __name__ == '__main__':
    main()
