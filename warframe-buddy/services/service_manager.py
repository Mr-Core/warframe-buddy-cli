# services/service_manager.py
import os
import sys
import time
import signal
import logging
import subprocess
import threading
from typing import Optional, Dict, Any
from pathlib import Path


class ServiceManager:
    """Production service manager for Warframe Buddy Discord Bot"""
    
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.pid_file = self.base_dir / 'warframe_buddy.pid'
        self.log_file = self.base_dir / 'logs' / 'bot_service.log'
        self.bot_process = None
        self.running = False
        self.config = self._load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger('ServiceManager')
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load service configuration"""
        default_config = {
            'bot_command': [sys.executable, '-m', 'interfaces.discord_bot'],
            'working_dir': str(self.base_dir),
            'environment': {
                'PYTHONPATH': str(self.base_dir),
                'PYTHONUNBUFFERED': '1',
            },
            'restart_on_crash': True,
            'restart_delay': 5,
            'max_restarts': 10,
            'health_check_interval': 60,
        }
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                print(f'Warning: Could not load config: {e}')
        
        return default_config
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.base_dir / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def start(self, foreground: bool = False):
        """Start the bot service"""
        if self.is_running():
            self.logger.error('Service is already running')
            return False
        
        self.logger.info('Starting Warframe Buddy Discord Bot service...')
        
        if foreground:
            return self._run_foreground()
        else:
            return self._run_background()
    
    def _run_foreground(self):
        """Run in foreground (for testing/development)"""
        try:
            self.running = True
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Run the bot directly
            self.logger.info('Running bot in foreground mode...')
            from interfaces.discord_bot import WarframeBuddyDiscordBot
            bot = WarframeBuddyDiscordBot()
            bot.run()
            
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to run bot: {e}')
            return False
    
    def _run_background(self):
        """Run as background daemon"""
        try:
            # Create PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # Fork to daemonize
            if os.fork():
                sys.exit(0)
            
            # Become session leader
            os.setsid()
            
            # Second fork
            if os.fork():
                sys.exit(0)
            
            # Change working directory
            os.chdir(self.config['working_dir'])
            
            # Close standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            with open('/dev/null', 'r') as devnull:
                os.dup2(devnull.fileno(), sys.stdin.fileno())
            with open('/dev/null', 'a+') as devnull:
                os.dup2(devnull.fileno(), sys.stdout.fileno())
                os.dup2(devnull.fileno(), sys.stderr.fileno())
            
            # Setup environment
            env = os.environ.copy()
            env.update(self.config['environment'])
            
            # Start bot process
            self.running = True
            restart_count = 0
            
            while self.running and restart_count < self.config['max_restarts']:
                try:
                    self.logger.info(f'Starting bot process (attempt {restart_count + 1})')
                    
                    self.bot_process = subprocess.Popen(
                        self.config['bot_command'],
                        cwd=self.config['working_dir'],
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Log bot output in separate thread
                    log_thread = threading.Thread(
                        target=self._log_process_output,
                        args=(self.bot_process,),
                        daemon=True
                    )
                    log_thread.start()
                    
                    # Monitor process
                    while self.running:
                        return_code = self.bot_process.poll()
                        if return_code is not None:
                            self.logger.warning(f'Bot process exited with code {return_code}')
                            
                            if self.config['restart_on_crash'] and self.running:
                                restart_count += 1
                                self.logger.info(f'Restarting in {self.config['restart_delay']} seconds...')
                                time.sleep(self.config['restart_delay'])
                                break
                            else:
                                self.running = False
                                break
                        
                        time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f'Bot process error: {e}')
                    if self.running and self.config['restart_on_crash']:
                        restart_count += 1
                        time.sleep(self.config['restart_delay'])
                    else:
                        break
            
            self.stop()
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to start background service: {e}')
            return False
    
    def _log_process_output(self, process):
        """Log bot process output"""
        for line in iter(process.stdout.readline, ''):
            if line:
                self.logger.info(f'[BOT] {line.strip()}')
    
    def stop(self):
        """Stop the bot service"""
        self.logger.info('Stopping Warframe Buddy service...')
        self.running = False
        
        if self.bot_process:
            try:
                self.logger.info('Sending SIGTERM to bot process...')
                self.bot_process.terminate()
                
                # Wait for graceful shutdown
                for _ in range(10):
                    if self.bot_process.poll() is not None:
                        break
                    time.sleep(1)
                
                # Force kill if still running
                if self.bot_process.poll() is None:
                    self.logger.warning('Force killing bot process...')
                    self.bot_process.kill()
                
                self.bot_process = None
                
            except Exception as e:
                self.logger.error(f'Error stopping process: {e}')
        
        # Remove PID file
        if self.pid_file.exists():
            self.pid_file.unlink()
        
        self.logger.info('Service stopped')
    
    def restart(self):
        """Restart the bot service"""
        self.logger.info('Restarting service...')
        self.stop()
        time.sleep(2)
        return self.start()
    
    def status(self):
        """Get service status"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is running
                try:
                    os.kill(pid, 0)
                    return {
                        'status': 'running',
                        'pid': pid,
                        'pid_file': str(self.pid_file),
                        'uptime': self._get_uptime(pid)
                    }
                except OSError:
                    return {'status': 'pid_file_exists_but_process_dead'}
            
            except Exception as e:
                return {'status': 'error', 'error': str(e)}
        
        return {'status': 'stopped'}
    
    def _get_uptime(self, pid: int) -> Optional[str]:
        """Get process uptime"""
        try:
            # Read process start time from /proc
            with open(f'/proc/{pid}/stat', 'r') as f:
                stats = f.read().split()
                start_time = int(stats[21])
            
            # Calculate uptime
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
            
            boot_time = time.time() - uptime_seconds
            process_start = boot_time + start_time / 100
            uptime = time.time() - process_start
            
            # Format uptime
            hours, remainder = divmod(int(uptime), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f'{hours}h {minutes}m'
            elif minutes > 0:
                return f'{minutes}m {seconds}s'
            else:
                return f'{seconds}s'
                
        except:
            return None
    
    def is_running(self) -> bool:
        """Check if service is running"""
        status = self.status()
        return status.get('status') == 'running'
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.logger.info(f'Received signal {signum}, shutting down...')
        self.stop()
        sys.exit(0)
    
    def logs(self, lines: int = 50, follow: bool = False):
        """Show service logs"""
        if not self.log_file.exists():
            print('No log file found')
            return
        
        try:
            if follow:
                # Tail -f like behavior
                import subprocess
                subprocess.run(['tail', '-f', str(self.log_file)])
            else:
                # Show last N lines
                with open(self.log_file, 'r') as f:
                    all_lines = f.readlines()
                    for line in all_lines[-lines:]:
                        print(line, end='')
        except Exception as e:
            print(f'Error reading logs: {e}')


# Command Line Interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Warframe Buddy Discord Bot Service Manager')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs', 'run'],
                       help='Action to perform')
    parser.add_argument('--foreground', '-f', action='store_true',
                       help='Run in foreground (for debugging)')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='Number of log lines to show (default: 50)')
    parser.add_argument('--follow', action='store_true',
                       help='Follow log output')
    
    args = parser.parse_args()
    
    manager = ServiceManager(args.config)
    
    if args.action == 'start':
        if args.foreground:
            manager.start(foreground=True)
        else:
            manager.start()
    
    elif args.action == 'stop':
        manager.stop()
    
    elif args.action == 'restart':
        manager.restart()
    
    elif args.action == 'status':
        status = manager.status()
        print(f'Status: {status['status']}')
        if 'pid' in status:
            print(f'PID: {status['pid']}')
        if 'uptime' in status:
            print(f'Uptime: {status['uptime']}')
        if 'error' in status:
            print(f'Error: {status['error']}')
    
    elif args.action == 'logs':
        manager.logs(lines=args.lines, follow=args.follow)
    
    elif args.action == 'run':
        # Direct run (for systemd service)
        manager.start(foreground=True)


if __name__ == '__main__':
    main()
