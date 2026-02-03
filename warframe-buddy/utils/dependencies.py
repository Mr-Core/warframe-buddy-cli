import importlib
import subprocess
import sys

# Key: What Python tries to import (import X)
# Value: What pip installs (pip install Y)
REQUIRED = {
    # import_name: pip_package_name
    "bs4": "beautifulsoup4",
    "requests": "requests",
    "schedule": "schedule",
    "discord": "discord.py",
    "dotenv": "python-dotenv",
}


def check_dependencies():
    """Check and install missing dependencies"""
    missing = []

    for import_name, pkg_name in REQUIRED.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pkg_name)
            print(f"✗ {pkg_name} is missing")

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        install = input("Install missing packages? (y/n): ").lower()

        if install == "y":
            for pkg in missing:
                print(f"\nInstalling {pkg}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                    print(f"\n✓ {pkg} installed")
                except subprocess.CalledProcessError:
                    print(f"✗ Failed to install {pkg}")
                    return False
            input("\nPress any key to continue...")
            return True
        else:
            print("Please install manually: pip install -r requirements.txt")
            return False

    return True
