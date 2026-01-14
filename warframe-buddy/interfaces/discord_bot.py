import sys, os
import discord
from discord.ext import commands
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_engine import WarframeSearchEngine
from config import COMMAND_PREFIX


class WarframeBuddyDiscordBot:
    """Discord bot interface for Warframe Buddy"""
    
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        
        self.bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
        self.search_engine = None
        self.setup_commands()
    
    def setup_commands(self):
        """Register all bot commands"""
        
        @self.bot.command(name='search', help='Search for item drop locations')
        async def search(ctx, *, item_name: str):
            """Search for an item"""
            if not item_name:
                await ctx.send(f'❌ Please specify an item: `{COMMAND_PREFIX}search "Forma Blueprint"`')
                return
            
            async with ctx.typing():
                if not self.search_engine:
                    await ctx.send(f'⚠️ Search engine not loaded. Use "{COMMAND_PREFIX}load first.')
                    return
                
                results = self.search_engine.search_item(item_name)

                if not results:
                    await ctx.send(f'❌ No drops found for "{item_name}"')
                    return
                
                # Limit to top 5 results for Discord message limits
                display_results = results[:5]

                response = f'🔍 **{item_name}** - Found {len(results)} drops(s)\n'
                response += '```\n'
                
                for i, drop in enumerate(display_results, 1):
                    chance = drop.get('chance', 0) * 100
                    source = drop['source_type']

                    if source == 'Missions':
                        loc = f'{drop.get('planet_name', '?')}/{drop.get('mission_name', '?')}/{drop.get('mission_descriptor', '?')}'
                    
                    elif source == 'Relics':
                        loc = f'{drop.get('relic_tier', '?')} {drop.get('relic_name', '?')} {drop.get('relic_refinement', '?')}'
                    
                    elif source == 'Bounties':
                        loc = f'{drop.get('planet_name', '?')}/{drop.get('mission_name', '?')}/{drop.get('mission_descriptor', '?')}'
                    
                    else:
                        loc = drop.get('mission_name', '?')
                    
                    response += f'{i}. {chance:.1f}% - {source}: {loc}\n'

                if len(results) > 5:
                    response += f'\n... and {len(results) - 5} more. Use "{COMMAND_PREFIX}best" for details.\n'
                
                response += '```'
                await ctx.send(response)

        @self.bot.command(name='best', help='Show best farming locations for an item')
        async def best(ctx, *, item_name: str):
            """Show best drop locations"""
            async with ctx.typing():
                if not self.search_engine:
                    await ctx.send(f'⚠️ Search engine not loaded. Use "{COMMAND_PREFIX}load first.')
                    return
                
                summary = self.search_engine.get_item_summary(item_name)

                if summary['total_sources'] == 0:
                    await ctx.send(f'❌ No drops found for **{item_name}**')
                    return
                
                best_source = summary['best_source']
                best_chance = summary['best_chance'] * 100
                
                response = f'**{item_name}** - Best farming spot:\n'
                response += f'**{best_chance:.1f}%** chance from '

                if best_source['source_type'] == 'Missions':
                    response += f'**{best_source.get('mission_name')}** on {best_source.get('planet_name')}'
                    if best_source.get('rotation'):
                        response += f'(Rotation {best_source.get('rotation')})'
                
                elif best_source['source_type'] == 'Relics':
                    response += f'**{best_source.get('relic_tier')} {best_source.get('relic_name')} {best_source.get('relic_refinement')}**'
                    
                elif best_source['source_type'] == 'Bounties':
                    response += f'**{best_source.get('mission_descriptor')}** on {best_source.get('planet_name')} / {best_source.get('mission_name')}'

                response += f'\n\n📊 Found {summary['total_sources']} total sources '
                response += f'({len(summary.get('missions', []))} missions, '
                response += f'{len(summary.get('relics', []))} relics, '
                response += f'{len(summary.get('bounties', []))} bounties)'

                await ctx.send(response)
        
        @self.bot.command(name='load', help='Load search indexes')
        async def load(ctx):
            """Load or create search indexes"""
            async with ctx.typing():
                try:
                    self.search_engine = WarframeSearchEngine()
                    self.search_engine.load_indexes()
                    await ctx.send('✅ Search indexes loaded successfully!')
                except FileNotFoundError:
                    await ctx.send('❌ No index file found! Run the CLI version first to create indexes.')
                except Exception as e:
                    await ctx.send(f'❌ Error loading indexes: {str(e)}')
            
        @self.bot.command(name='status', help='Check bot status')
        async def status(ctx):
            """Show bot status"""
            if self.search_engine:
                status_info = self.search_engine.get_index_status()
                
                response = f'✅ **Bot is running**\n'
                response += f'• Items indexed: {status_info['total_items']}\n'
                response += f'• Last rebuild: {status_info['last_rebuild'] or 'Unknown'}\n'
                response += f'• Loaded: {'Yes' if status_info['loaded'] else 'No'}'
            else:
                response = f'⚠️ **Search engine not loaded**\nUse "{COMMAND_PREFIX}load" to load indexes'
            
            await ctx.send(response)
        
        @self.bot.command(name='helpme', help='Show all commands')
        async def helpme(ctx):
            """Custom help command"""
            help_text = textwrap.dedent(f"""\
                **Warframe Buddy Bot Commands:**
                
                `{COMMAND_PREFIX}search <item>` - Search for item drop locations
                `{COMMAND_PREFIX}best <item>` - Show best farming spot for item
                `{COMMAND_PREFIX}load` - Load search indexes (required first)
                `{COMMAND_PREFIX}status` - Check bot status
                `{COMMAND_PREFIX}helpme` - Show this help
                
                **Example:** `{COMMAND_PREFIX}search Mesa Prime Blueprint`
            """)
            
            await ctx.send(help_text)
        
        @self.bot.command(name='hi')
        async def greeting(ctx):
            """Simple greeting to the user"""
            await ctx.send('Hello! 😊')
        
        @self.bot.event
        async def on_ready():
            """Called when bot connects"""
            print(f'✅ Discord bot logged in as {self.bot.user}')
            
            # Set helpful status
            await self.bot.change_presence(
                activity=discord.Game(name=f'{COMMAND_PREFIX}helpme')
            )
            
            print(f'✅ Bot is in {len(self.bot.guilds)} servers')
            print(f'✅ Status set to: "{COMMAND_PREFIX}helpme"')
            
            # Try to auto-load search engine
            try:
                self.search_engine = WarframeSearchEngine()
                self.search_engine.load_indexes()
                print('✅ Search indexes loaded automatically')
            except:
                print(f'⚠️  Could not auto-load indexes. Users need to run {COMMAND_PREFIX}load')
                
    def run(self):
        """Start the Discord bot"""
        from config import DISCORD_TOKEN
        
        if not DISCORD_TOKEN or DISCORD_TOKEN == 'DEV_MODE_NO_TOKEN':
            print('\n⚠ DISCORD_TOKEN not set!')
            print('  Rename ".env.example" to ".env" and add your token there.\n')
            sys.exit(1)
        
        print('Starting Discord bot...')
        self.bot.run(DISCORD_TOKEN)


if __name__ == '__main__':
    bot = WarframeBuddyDiscordBot()
    bot.run
