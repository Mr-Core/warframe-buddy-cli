import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INTERFACE = 'dbot'

def main():
    from utils.dependencies import check_dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if INTERFACE == 'cli':
        # Run cli
        from interfaces.cli import cli
        cli()
    
    elif INTERFACE == 'dbot':
        # Run Discord bot
        from interfaces.discord_bot import WarframeBuddyDiscordBot
        bot = WarframeBuddyDiscordBot()
        bot.run()


if __name__ == '__main__':
    main()
