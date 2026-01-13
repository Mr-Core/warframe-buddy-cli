import importlib
import subprocess
import sys


REQUIRED = {
    'beautifulsoup4': 'bs4',
    'requests': 'requests',
    'schedule': 'schedule',
}

def check_dependencies():
    """Check and install missing dependencies"""
    missing = []
    
    for pkg, import_name in REQUIRED.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} is missing")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        install = input("Install missing packages? (y/n): ").lower()
        
        if install == 'y':
            for pkg in missing:
                print(f"Installing {pkg}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                    print(f"✓ {pkg} installed")
                except subprocess.CalledProcessError:
                    print(f"✗ Failed to install {pkg}")
                    return False
            input('\nPress any key to continue...')
            return True
        else:
            print("Please install manually: pip install -r requirements.txt")
            return False
    
    return True
