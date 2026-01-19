import sys, os
import discord
from discord.ext import commands
import asyncio
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
        
    async def fuzzy_select_item(self, ctx, search_query: str) -> str | None:
        """
        Handle fuzzy item selection with interactive menu
        Returns: selected_item_name or None if canceled
        """
        if not self.search_engine:
            await ctx.send(f'⚠️ Search engine not loaded. Use `{COMMAND_PREFIX}load` first.')
            return None
        
        # Get all items from index
        all_items = list(self.search_engine.search_indexes['item_sources'].keys())
        search_lower = search_query.lower()
        
        # Find partial matches
        matching_items = [
            item for item in all_items
            if search_lower in item.lower()
        ]
        
        if not matching_items:
            await ctx.send(f'❌ No items found matching **"{search_query}"**')
            return None
        
        # Single match - return immediately
        if len(matching_items) == 1:
            return matching_items[0]
        
        # Multiple matches - show interactive menu
        display_items = matching_items[:15]  # Discord message limit
        
        selection_text = f'🔍 Found **{len(matching_items)}** matching items:\n'
        for i, item in enumerate(display_items, 1):
            selection_text += f'{i}. {item}\n'
        
        if len(matching_items) > 15:
            selection_text += f'\n... and {len(matching_items) - 15} more.'
        
        selection_text += f'\n\nReply with a number (1-{len(display_items)})'

        await ctx.send(selection_text)

        # Wait for user's choice
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)

            if msg.content.isdigit():
                idx = int(msg.content) - 1
                if 0 <= idx < len(display_items):
                    return display_items[idx]
                else:
                    await ctx.send('❌ Invalid selection!')
                    return None
            else:
                await ctx.send('❌ Please reply with a number.')
                return None
        
        except asyncio.TimeoutError:
            await ctx.send('⏰ Selection timed out!')
            return None
    
    async def display_interactive_search(self, ctx, item_name: str, results: list):
        """Interactive tabbed search display with in-message updates"""
        
        # Group and sort results
        grouped = self._group_results_by_source(results)
        
        # Determine initial tab (show the source type with most results)
        initial_tab = max(grouped.keys(), key=lambda k: len(grouped[k]), default=None)
        if not initial_tab:
            await ctx.send(f"❌ No drops found for **{item_name}**")
            return
        
        current_tab = initial_tab
        current_page = 0
        items_per_page = 5
        
        # Create initial message
        embed = self._create_tab_embed(item_name, grouped, current_tab, current_page, items_per_page)
        message = await ctx.send(embed=embed)
        
        if len(grouped) == 1:
            source_type = list(grouped.keys())[0]
            if len(grouped[source_type]) <= 5:  # If 5 or fewer results
                # Clear reactions to end search query
                await message.clear_reactions()
                return
        
        # Add reactions for navigation
        tab_emojis = {"🇲": "Missions", "🇷": "Relics", "🇸": "Sorties", "🇧": "Bounties"}
        nav_emojis = ["◀️", "▶️", "❌"]
        
        # Only add emojis for tabs that have results
        for emoji, tab_name in tab_emojis.items():
            if tab_name in grouped and grouped[tab_name]:
                await message.add_reaction(emoji)
        
        # Add navigation emojis
        for emoji in nav_emojis:
            await message.add_reaction(emoji)
        
        # Interaction loop
        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    'reaction_add', 
                    timeout=120.0,
                    check=lambda r, u: (
                        u == ctx.author and 
                        r.message.id == message.id and
                        str(r.emoji) in list(tab_emojis.keys()) + nav_emojis
                    )
                )
                
                emoji = str(reaction.emoji)
                
                # Handle tab switching
                if emoji in tab_emojis:
                    new_tab = tab_emojis[emoji]
                    if new_tab in grouped and grouped[new_tab]:
                        current_tab = new_tab
                        current_page = 0  # Reset to first page when switching tabs
                
                # Handle pagination
                elif emoji == "▶️":
                    max_pages = (len(grouped[current_tab]) + items_per_page - 1) // items_per_page
                    if current_page < max_pages - 1:
                        current_page += 1
                
                elif emoji == "◀️":
                    if current_page > 0:
                        current_page -= 1
                
                # Handle close
                elif emoji == "❌":
                    await message.clear_reactions()
                    return
                
                # Update message
                embed = self._create_tab_embed(item_name, grouped, current_tab, current_page, items_per_page)
                await message.edit(embed=embed)
                await message.remove_reaction(emoji, user)
                
            except asyncio.TimeoutError:
                # Remove reactions after timeout
                try:
                    await message.clear_reactions()
                except:
                    pass
                break

    def _group_results_by_source(self, results: list) -> dict:
        """Group results by source type and sort by chance"""
        grouped = {}
        for drop in results:
            source = drop['source_type']
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(drop)
        
        # Sort each group by chance (descending)
        for source in grouped:
            grouped[source].sort(key=lambda x: x.get('chance', 0), reverse=True)
        
        return grouped
    
    def _create_tab_embed(self, item_name: str, grouped: dict, current_tab: str, page: int, per_page: int) -> discord.Embed:
        """Create embed for current tab and page using new format"""
        
        if current_tab not in grouped or not grouped[current_tab]:
            return discord.Embed(
                title=f"🔍 {item_name}",
                description=f"No {current_tab.lower()} drops found",
                color=discord.Color.red()
            )
        
        items = grouped[current_tab]
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]
        total_pages = (len(items) + per_page - 1) // per_page
        
        # Calculate total results across all sources
        total_all_results = sum(len(grouped[source]) for source in grouped)
        
        # Build filter options text
        filter_options = []
        for emoji, tab_name in {"🇲": "Missions", "🇷": "Relics", "🇸": "Sorties", "🇧": "Bounties"}.items():
            if tab_name in grouped and grouped[tab_name]:
                if tab_name == current_tab:
                    filter_options.append(f"**{emoji} {tab_name}**")
                else:
                    filter_options.append(f"{emoji} {tab_name}")
        
        # Create embed
        embed = discord.Embed(
            title=f"🔍 Displaying results for \"{item_name}\"",
            color=discord.Color.blue()
        )
        
        # Add description with counts AND filter options
        description = f"Total found result(s): **{total_all_results}**\n\n"
        
        # Add filter indicator
        filter_emoji = {"Missions": "🇲", "Relics": "🇷", "Sorties": "🇸", "Bounties": "🇧"}.get(current_tab, "🔍")
        description += f"Filter applied: {filter_emoji} **{current_tab}**\n"
        description += f"Total results with filter applied: **{len(items)}**\n\n"
        
        description += f"**Page {page + 1} of {total_pages}**\n\n"
        
        embed.description = description
        
        # Add results field with your format
        results_text = "```\n"
        results_text += "─" * 40 + "\n"
        
        for i, drop in enumerate(page_items, start=start_idx + 1):
            # Source line
            results_text += f"{i:2}. Source: {drop['source_type']}\n"
            
            # Format based on source type
            if current_tab == "Missions":
                results_text += f"    Planet: {drop.get('planet_name', '?')}\n"
                results_text += f"    Mission: {drop.get('mission_name', '?')}\n"
                
                mission_type = drop.get('mission_type')
                if mission_type:
                    results_text += f"    Type: {mission_type}\n"
                
                rotation = drop.get('rotation')
                if rotation:
                    results_text += f"    Rotation: {rotation}\n"
            
            elif current_tab == "Relics":
                results_text += f"    Tier: {drop.get('relic_tier', '?')}\n"
                results_text += f"    Name: {drop.get('relic_name', '?')}\n"
                
                refinement = drop.get('relic_refinement')
                if refinement:
                    results_text += f"    Refinement: {refinement}\n"
            
            elif current_tab == "Bounties":
                results_text += f"    Planet: {drop.get('planet_name', '?')}\n"
                results_text += f"    Location: {drop.get('mission_name', '?')}\n"
                
                bounty_type = drop.get('mission_type')
                if bounty_type:
                    results_text += f"    Bounty: {bounty_type}\n"
                
                rotation = drop.get('rotation')
                if rotation:
                    results_text += f"    Rotation: {rotation}\n"
            
            else:  # Sorties
                mission_name = drop.get('mission_name', 'Sortie Reward')
                results_text += f"    Mission: {mission_name}\n"
            
            # Chance and rarity
            chance = drop.get('chance', 0) * 100
            rarity = drop.get('rarity', 'Unknown')
            results_text += f"    Chance: {chance:.1f}% ({rarity})\n"
            
            # Separator between items
            if i < end_idx and i < len(items):
                results_text += "\n"
        
        results_text += "─" * 40 + "\n"
        
        # Add "and X more" footer if applicable
        remaining = len(items) - end_idx
        if remaining > 0:
            results_text += f"\n... and {remaining} more results.\n"
        
        results_text += f"\nPage {page + 1} of {total_pages}\n"
        results_text += "```"
        
        source_type = list(grouped.keys())[0]
        if len(grouped) == 1 and len(grouped[source_type]) <= 5:  # If 5 or fewer results
            footer_text = '\nEnd of search.'
        else:
            footer_text = "\nFilter: " + " | ".join(filter_options)
            footer_text += "\n\nNavigation: ◀️ ▶️ Turn pages • ❌ End search"
            
        results_text += footer_text
        
        embed.add_field(name="Results", value=results_text, inline=False)
        
        return embed
    
    def setup_commands(self):
        """Register all bot commands"""
        
        @self.bot.command(name='search', help='Search for item drop locations')
        async def search(ctx, *, search_query: str = None):
            """Search for an item"""
            if not search_query:
                await ctx.send(f'❌ Please specify: `{COMMAND_PREFIX}search "forma"`')
                return
            
            async with ctx.typing():
                selected_item = await self.fuzzy_select_item(ctx, search_query)
                if not selected_item:
                    return
                
                results = self.search_engine.search_item(selected_item)
                
                if not results:
                    await ctx.send(f'❌ No drops found for **"{selected_item}"**')
                    return
                
                # Show interactive display
                await self.display_interactive_search(ctx, selected_item, results)

        @self.bot.command(name='best', help='Show best farming locations for an item')
        async def best(ctx, *, search_query: str = None):
            """Show best drop locations"""
            # Currently useless, ?search shows all necessary info 
            # TODO Refactor to real-time strategic guidance
            
            if not search_query:
                await ctx.send(f'❌ Please specify an item: `{COMMAND_PREFIX}best "forma"`')
                return
            
            async with ctx.typing():
                # Use fuzzy selector to get item name
                selected_item = await self.fuzzy_select_item(ctx, search_query)
                if not selected_item:
                    return  # Error already handled
                
                summary = self.search_engine.get_item_summary(selected_item)

                if summary['total_sources'] == 0:
                    await ctx.send(f'❌ No drops found for **{selected_item}**')
                    return
                
                best_source = summary['best_source']
                best_chance = summary['best_chance'] * 100
                
                response = f'**{selected_item}** - Best farming spot:\n'
                response += f'**{best_chance:.1f}%** chance from '

                if best_source['source_type'] == 'Missions':
                    response += f'**{best_source.get('mission_name')}** on {best_source.get('planet_name')}'
                    if best_source.get('rotation'):
                        response += f'(Rotation {best_source.get('rotation')})'
                
                elif best_source['source_type'] == 'Relics':
                    response += f'**{best_source.get('relic_tier')} {best_source.get('relic_name')} {best_source.get('relic_refinement')}**'
                
                elif best_source['source_type'] == 'Sorties':
                    response += f'**Sortie**'
                    
                elif best_source['source_type'] == 'Bounties':
                    response += f'**{best_source.get('mission_type')}** on {best_source.get('planet_name')} / {best_source.get('mission_name')}'

                response += f'\n\n📊 Found {summary['total_sources']} total sources '
                response += f'({len(summary.get('missions', []))} missions, '
                response += f'{len(summary.get('relics', []))} relics, '
                response += f'{len(summary.get('sorties', []))} sortie, '
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
