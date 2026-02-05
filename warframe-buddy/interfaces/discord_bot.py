import sys, os
from venv import logger  # TODO Implement properly
import discord
from discord.ext import commands
from typing import Optional
import asyncio
import textwrap
from datetime import datetime, timezone, timedelta
from typing import List, Dict  # Required for Linux deployment

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from search_engine import WarframeSearchEngine
from config import COMMAND_PREFIX
from services.warframe_api import WarframeAPI


class WarframeBuddyDiscordBot:
    """Discord bot interface for Warframe Buddy"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        self.bot = commands.Bot(
            command_prefix=COMMAND_PREFIX, intents=intents, case_insensitive=True
        )

        self.search_engine: Optional[WarframeSearchEngine] = None

        self.setup_error_handling()
        self.setup_commands()

        self.warframe_api = WarframeAPI()

    # ==== BASE SETUP ====

    def setup_error_handling(self):
        """Set up error handlers for commands"""

        def get_command_suggestions(
            attempted_cmd, available_commands, max_suggestions=3
        ):
            """Get similar command suggestions using fuzzy matching"""
            import difflib

            # First check if it's a simple typo (missing/extra letter)
            suggestions = difflib.get_close_matches(
                attempted_cmd, available_commands, n=max_suggestions, cutoff=0.4
            )

            # Also check for partial matches
            if not suggestions:
                partial_matches = [
                    cmd
                    for cmd in available_commands
                    if attempted_cmd in cmd or cmd in attempted_cmd
                ]
                suggestions = partial_matches[:max_suggestions]

            return suggestions

        @self.bot.event
        async def on_command_error(ctx, error):
            """Handle command errors"""
            if isinstance(error, commands.CommandNotFound):
                message_content = ctx.message.content
                prefix = COMMAND_PREFIX

                if message_content.startswith(prefix):
                    # Extract attempted command
                    parts = message_content[len(prefix) :].strip().split(maxsplit=1)
                    attempted_cmd = parts[0].lower() if parts else ""

                    if attempted_cmd:  # Make sure there's actually a command attempted
                        available_commands = [cmd.name for cmd in self.bot.commands]
                        suggestions = get_command_suggestions(
                            attempted_cmd, available_commands
                        )

                        # Create helpful error message
                        embed = discord.Embed(
                            title=f"❌ Unknown Command: `{prefix}{attempted_cmd}`",
                            color=discord.Color.red(),
                        )

                        if suggestions:
                            suggestions_text = "\n".join(
                                [f"• `{prefix}{cmd}`" for cmd in suggestions]
                            )
                            embed.add_field(
                                name="Did you mean one of these?",
                                value=suggestions_text,
                                inline=False,
                            )

                        embed.add_field(
                            name="All Commands",
                            value=f"Type `{prefix}help` to see all available commands.",
                            inline=False,
                        )

                        # Common typos mapping
                        common_typos = {
                            "serach": "search",
                            "seach": "search",
                            "searh": "search",
                            "stat": "status",
                            "hel": "help",
                            "help": "help",
                            "loa": "load",
                            "ld": "load",
                        }

                        if attempted_cmd in common_typos:
                            embed.add_field(
                                name="Common typo detected!",
                                value=f"Did you mean `{prefix}{common_typos[attempted_cmd]}`?",
                                inline=False,
                            )

                        await ctx.send(embed=embed)

                return

            # Handle other errors...
            elif isinstance(error, commands.MissingRequiredArgument):
                embed = discord.Embed(
                    title="❌ Missing Argument",
                    description=f"Missing required argument for `{ctx.command}`.",
                    color=discord.Color.orange(),
                )

                # Get command signature
                params = list(ctx.command.params.values())[1:]  # Skip ctx parameter
                if params:
                    param_list = []
                    for param in params:
                        if param.default == param.empty:
                            param_list.append(f"<{param.name}>")  # Required
                        else:
                            param_list.append(f"[{param.name}]")  # Optional

                    embed.add_field(
                        name="Usage",
                        value=f"`{COMMAND_PREFIX}{ctx.command} {' '.join(param_list)}`",
                        inline=False,
                    )

                embed.add_field(
                    name="Example",
                    value=f'`{COMMAND_PREFIX}{ctx.command} "item name"`',
                    inline=False,
                )

                await ctx.send(embed=embed)
                return

            # Log other errors
            print(f"[ERROR] Command error: {type(error).__name__}: {error}")

    def setup_commands(self):
        """Register all bot commands"""
        self.bot.remove_command("help")

        @self.bot.command(name="search", help="Search for item drop locations")
        async def search(ctx, *, search_query: str | None = None):
            """Search for an item"""
            if not self.search_engine:
                await ctx.send(
                    f"⚠️ Search engine not loaded. Use `{COMMAND_PREFIX}load` first."
                )
                return

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

        @self.bot.command(
            name="best", help="Show best farming locations with real-time strategy"
        )
        async def best(ctx, *, search_query: str | None = None):
            """Show best drop locations with current opportunities"""
            if not search_query:
                await ctx.send(
                    f'❌ Please specify an item: `{COMMAND_PREFIX}best "forma"`'
                )
                return

            async with ctx.typing():
                # 1. Get item info (existing logic)
                selected_item = await self.fuzzy_select_item(ctx, search_query)
                if not selected_item:
                    return

                if not self.search_engine:
                    await ctx.send(
                        f"⚠️ Search engine not loaded. Use `{COMMAND_PREFIX}load` first."
                    )
                    return

                summary = self.search_engine.get_item_summary(selected_item)

                if summary["total_sources"] == 0:
                    await ctx.send(f"❌ No drops found for **{selected_item}**")
                    return

                # 2. Get real-time game state
                game_state = await self._get_game_state()

                # Get relic tiers BOTH from all results AND from best_source
                relic_tiers = self._get_relic_tiers_for_item(selected_item)

                # Also extract tier directly from best_source if it's a relic
                best_source = summary["best_source"]
                if best_source["source_type"] == "Relics":
                    best_tier = best_source.get("relic_tier", "")
                    if best_tier and " " in best_tier:
                        best_tier = best_tier.split()[0]

                    if best_tier and best_tier not in relic_tiers:
                        relic_tiers.append(best_tier)

                # 4. Build enhanced response
                response = self._build_best_response(
                    item_name=selected_item,
                    best_source=summary["best_source"],
                    best_chance=summary["best_chance"] * 100,  # Convert to percentage
                    game_state=game_state,
                    relic_tiers=relic_tiers,
                )

                # 5. Send response
                await ctx.send(response)

        @self.bot.command(name="load", help="Load search indexes")
        async def load(ctx):
            """Load or create search indexes"""
            async with ctx.typing():
                try:
                    self.search_engine = WarframeSearchEngine()
                    self.search_engine.load_indexes()
                    await ctx.send("✅ Search indexes loaded successfully!")
                except FileNotFoundError:
                    await ctx.send(
                        "❌ No index file found! Run the CLI version first to create indexes."
                    )
                except Exception as e:
                    await ctx.send(f"❌ Error loading indexes: {str(e)}")

        @self.bot.command(name="status", help="Check bot status")
        async def status(ctx):
            """Show bot status"""
            if self.search_engine:
                status_info = self.search_engine.get_index_status()

                response = f"✅ **Bot is running**\n"
                response += f"• Items indexed: {status_info['total_items']}\n"
                response += (
                    f"• Last rebuild: {status_info['last_rebuild'] or 'Unknown'}\n"
                )
                response += f"• Loaded: {'Yes' if status_info['loaded'] else 'No'}"
            else:
                response = f'⚠️ **Search engine not loaded**\nUse "{COMMAND_PREFIX}load" to load indexes'

            await ctx.send(response)

        @self.bot.command(name="help", help="Show all commands")
        async def custom_help(ctx):
            """Custom help command"""
            help_text = textwrap.dedent(
                f"""\
                **Warframe Buddy Bot Commands:**
                
                `{COMMAND_PREFIX}search <item>` - Search for item drop locations
                `{COMMAND_PREFIX}best <item>` - Show best farming spot for item
                `{COMMAND_PREFIX}load` - Load search indexes (required first)
                `{COMMAND_PREFIX}status` - Check bot status
                `{COMMAND_PREFIX}helpme` - Show this help
                
                **Example:** `{COMMAND_PREFIX}search Mesa Prime Blueprint`
            """
            )

            await ctx.send(help_text)

        @self.bot.command(name="hi")
        async def greeting(ctx):
            """Simple greeting to the user"""
            await ctx.send("Hello! 😊")

        @self.bot.command(name="rebuild")
        async def rebuild(ctx):
            from services.fetch_data import fetch_data
            from orchestrator import DropOrchestrator

            await ctx.send("Fetching latest data...")
            fetch_success, fetch_error = fetch_data()

            if fetch_success:
                await ctx.send("✓ Data fetched successfully")
            else:
                await ctx.send("✗ Error fetching latest data.")
                if fetch_error:
                    await ctx.send(f"  ↳ {fetch_error}")
                return

            orchestrator = DropOrchestrator()

            # Parse everything
            await ctx.send("Parsing data...")
            orchestrator = DropOrchestrator()
            all_drops, len_all_drops = orchestrator.parse_all()

            # Print parse details
            await ctx.send(
                "Parsing completed:\n"
                f"   Missions: {len_all_drops['mission_drops']} drops\n"
                f"   Relics: {len_all_drops['relic_drops']} drops\n"
                f"   Sorties: {len_all_drops['sortie_drops']} drops\n"
                f"   Cetus bounties: {len_all_drops['cetus_bounty_drops']} drops\n"
                f"   Orb Vallis bounties: {len_all_drops['solaris_bounty_drops']} drops\n"
                f"   Cambion Drift bounties: {len_all_drops['deimos_bounty_drops']} drops\n"
                f"   Zariman bounties: {len_all_drops['zariman_bounty_drops']} drops\n"
                f"   Albrecht's Laboratories bounties: {len_all_drops['entrati_lab_bounty_drops']} drops\n"
                f"   Hex bounties: {len_all_drops['hex_bounty_drops']} drops\n"
                f"   Dynamic Location Rewards: {len_all_drops['transient_drops']} drops\n"
                f"   Total drops: {len_all_drops['total_drops']} drops"
            )

            # Generate a validation report
            report = orchestrator.get_validation_report()

            # Show validation summary
            overall = report["overall"]

            await ctx.send(
                f"VALIDATION SUMMARY:\n"
                f"   Total drops: {overall['total_drops']}\n"
                f"   Data integrity: {overall['data_integrity']:.1%}\n"
                f"   Errors: {overall['error_count']}\n"
                f"   Warnings: {overall['warning_count']}"
            )

            # Check if validation report contains any errors
            if (
                report["overall"]["error_count"] > 0
                or report["overall"]["warning_count"] > 0
            ):
                error_trigger = True
                await ctx.send("   CRITICAL: Errors found in data!")

            if error_trigger:
                await ctx.send(
                    "⚠  Data contains errors and is not safe to use! ⚠\n"
                    "Run the program in DEVELOPMENT MODE to diagnose the problems.\n"
                )
                return

            # Save parsed data to file
            await ctx.send("Saving parsed data to file...")
            save_response = orchestrator.save_parsed_data()
            await ctx.send(save_response)

            # Create search engine with fresh data
            await ctx.send("Creating search indexes...")
            search_engine = WarframeSearchEngine()
            create_indexes_reponse = search_engine.create_indexes_from_drops(all_drops)

            await ctx.send(
                f"✓ Indexed {len(all_drops)} drops\n" f"{create_indexes_reponse}"
            )

            # Always save indexes in Mode 1
            save_indexes_response = search_engine.save_indexes()
            await ctx.send(save_indexes_response)

            # Show index status
            status = search_engine.get_index_status()

            await ctx.send(
                f"Index Status:\n"
                f"  - Items indexed: {status['total_items']}\n"
                f"  - Rebuilt at: {status['last_rebuild'] or 'Just now'}"
            )

        @self.bot.command(name="debug")
        async def debug(ctx):
            await self.debug_fissures(ctx)

        @self.bot.event
        async def on_ready():
            """Called when bot connects"""
            print(f"✅ Discord bot logged in as {self.bot.user}")

            # Set helpful status
            await self.bot.change_presence(
                activity=discord.Game(name=f"{COMMAND_PREFIX}help")
            )

            print(f"✅ Bot is in {len(self.bot.guilds)} servers")
            print(f'✅ Status set to: "{COMMAND_PREFIX}help"')

            # Try to auto-load search engine
            try:
                self.search_engine = WarframeSearchEngine()
                self.search_engine.load_indexes()
                print("✅ Search indexes loaded automatically")
            except:
                print(
                    f"⚠️  Could not auto-load indexes. Users need to run {COMMAND_PREFIX}rebuild"
                )

    # ==== SHARED FUNCTIONS ====

    async def fuzzy_select_item(self, ctx, search_query: str) -> str | None:
        """
        Handle fuzzy item selection with interactive menu
        Returns: selected_item_name or None if canceled
        """
        if not self.search_engine:
            await ctx.send(
                f"⚠️ Search engine not loaded. Use `{COMMAND_PREFIX}load` first."
            )
            return None

        # Get all items from index
        all_items = list(self.search_engine.search_indexes["item_sources"].keys())
        search_lower = search_query.lower()

        # Find partial matches
        matching_items = [item for item in all_items if search_lower in item.lower()]

        if not matching_items:
            await ctx.send(f'❌ No items found matching **"{search_query}"**')
            return None

        # Single match - return immediately
        if len(matching_items) == 1:
            return matching_items[0]

        # Multiple matches - show interactive menu
        display_items = matching_items[:15]  # Discord message limit

        selection_text = f"🔍 Found **{len(matching_items)}** matching items:\n"
        for i, item in enumerate(display_items, 1):
            selection_text += f"{i}. {item}\n"

        if len(matching_items) > 15:
            selection_text += f"\n... and {len(matching_items) - 15} more."

        selection_text += f"\n\nReply with a number (1-{len(display_items)})"

        await ctx.send(selection_text)

        # Wait for user's choice
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)

            if msg.content.isdigit():
                idx = int(msg.content) - 1
                if 0 <= idx < len(display_items):
                    return display_items[idx]
                else:
                    await ctx.send("❌ Invalid selection!")
                    return None
            else:
                await ctx.send("❌ Please reply with a number.")
                return None

        except asyncio.TimeoutError:
            await ctx.send("⏰ Selection timed out!")
            return None

    # ==== ?search ====

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
        items_per_page = 6

        # Create initial message
        embed = self._create_tab_embed(
            item_name, grouped, current_tab, current_page, items_per_page
        )
        message = await ctx.send(embed=embed)
        await message.edit(embed=embed)

        if len(grouped) == 1:
            source_type = list(grouped.keys())[0]
            if len(grouped[source_type]) <= 5:  # If 5 or fewer results
                # Clear reactions to end search query
                await message.clear_reactions()
                return

        # Add reactions for navigation
        tab_emojis = {
            "🇲": "Missions",
            "🇷": "Relics",
            "🇸": "Sorties",
            "🇧": "Bounties",
            "🇩": "Dynamic",
        }
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
                    "reaction_add",
                    timeout=120.0,
                    check=lambda r, u: (
                        u == ctx.author
                        and r.message.id == message.id
                        and str(r.emoji) in list(tab_emojis.keys()) + nav_emojis
                    ),
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
                    max_pages = (
                        len(grouped[current_tab]) + items_per_page - 1
                    ) // items_per_page
                    if current_page < max_pages - 1:
                        current_page += 1

                elif emoji == "◀️":
                    if current_page > 0:
                        current_page -= 1

                # Handle close
                elif emoji == "❌":
                    embed = self._create_tab_embed(
                        item_name, grouped, current_tab, current_page, items_per_page
                    )
                    embed = self._update_embed_for_end(embed, "End of search")
                    await message.edit(embed=embed)

                    await message.clear_reactions()
                    return

                # Update message
                embed = self._create_tab_embed(
                    item_name, grouped, current_tab, current_page, items_per_page
                )
                await message.edit(embed=embed)

                await message.remove_reaction(emoji, user)

            except asyncio.TimeoutError:
                # Remove reactions after timeout
                embed = self._create_tab_embed(
                    item_name, grouped, current_tab, current_page, items_per_page
                )
                embed = self._update_embed_for_end(embed, "Search timed out")
                await message.edit(embed=embed)

                try:
                    await message.clear_reactions()
                except:
                    pass
                break

    def _group_results_by_source(self, results: list) -> dict:
        """Group results by source type and sort by chance"""
        grouped = {}

        # Map long source names to display names
        source_display_map = {
            "Dynamic Location Rewards": "Dynamic",
            "Missions": "Missions",
            "Relics": "Relics",
            "Sorties": "Sorties",
            "Bounties": "Bounties",
        }

        for drop in results:
            source = drop["source_type"]

            # Convert to display name
            display_source = source_display_map.get(source, source)

            if display_source not in grouped:
                grouped[display_source] = []
            grouped[display_source].append(drop)

        # Sort each group by chance (descending)
        for source in grouped:
            grouped[source].sort(key=lambda x: x.get("chance", 0), reverse=True)

        return grouped

    def _create_tab_embed(
        self, item_name: str, grouped: dict, current_tab: str, page: int, per_page: int
    ) -> discord.Embed:
        """Create embed for current tab and page using new format"""

        if current_tab not in grouped or not grouped[current_tab]:
            return discord.Embed(
                title=f"🔍 {item_name}",
                description=f"No {current_tab.lower()} drops found",
                color=discord.Color.red(),
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
        for emoji, tab_name in {
            "🇲": "Missions",
            "🇷": "Relics",
            "🇸": "Sorties",
            "🇧": "Bounties",
            "🇩": "Dynamic",
        }.items():
            if tab_name in grouped and grouped[tab_name]:
                if tab_name == current_tab:
                    filter_options.append(f"**{emoji} {tab_name}**")
                else:
                    filter_options.append(f"{emoji} {tab_name}")

        # Create embed
        embed = discord.Embed(
            title=f'🔍 Displaying results for "{item_name}"', color=discord.Color.blue()
        )

        # Add description with counts AND filter options
        description = f"Total found result(s): **{total_all_results}**\n\n"

        # Add filter indicator
        filter_emoji = {
            "Missions": "🇲",
            "Relics": "🇷",
            "Sorties": "🇸",
            "Bounties": "🇧",
            "Dynamic": "🇩",
        }.get(current_tab, "🔍")
        description += f"Filter applied: {filter_emoji} **{current_tab}**\n"
        description += f"Total results with filter applied: **{len(items)}**\n"

        embed.description = description

        # Add results field
        results_text = "```\n"

        source_print = current_tab
        if source_print == "Dynamic":
            source_print = "Dynamic Location Rewards"
        results_text += f"Source: {source_print}\n"

        results_text += "─" * 40 + "\n\n"

        for i, drop in enumerate(page_items, start=start_idx + 1):
            # Source line
            results_text += f"{i:2}. "

            # Format based on source type
            if current_tab == "Missions":
                results_text += f"Planet: {drop.get('planet_name', '?')}\n"
                results_text += f"    Mission: {drop.get('mission_name', '?')}\n"

                mission_type = drop.get("mission_type")
                if mission_type:
                    results_text += f"    Type: {mission_type}\n"

                rotation = drop.get("rotation")
                if rotation:
                    results_text += f"    Rotation: {rotation}\n"

            elif current_tab == "Relics":
                results_text += (
                    f"Relic: {drop.get('relic_tier', '?')} {drop.get('relic_name', )}\n"
                )
                results_text += f"    Refinement: {drop.get('relic_refinement')}\n"

            elif current_tab == "Bounties":
                results_text += f"Planet: {drop.get('planet_name', '?')}\n"
                results_text += f"    Location: {drop.get('mission_name', '?')}\n"

                bounty_type = drop.get("mission_type")
                if bounty_type:
                    results_text += f"    Bounty: {bounty_type}\n"

                rotation = drop.get("rotation")
                if rotation:
                    results_text += f"    Rotation: {rotation}\n"

                stage = drop.get("stage")
                if stage:
                    results_text += f"    Stage: {stage}\n"

            elif current_tab == "Dynamic":
                results_text += f"Mission name: {drop.get('mission_name', '?')}\n"

                rotation = drop.get("rotation")
                if rotation:
                    results_text += f"    Rotation: {rotation}\n"

            else:  # Sorties
                mission_name = drop.get("mission_name", "Sortie Reward")
                results_text += f"Mission: {mission_name}\n"

            # Chance and rarity
            chance = drop.get("chance", 0) * 100
            rarity = drop.get("rarity", "Unknown")
            results_text += f"    Chance: {chance:.1f}% ({rarity})\n"

            # Separator between items
            if i < end_idx and i < len(items):
                results_text += "\n"

        results_text += "\n"
        results_text += "─" * 40 + "\n"

        # Add "and X more" footer if applicable
        remaining = len(items) - end_idx
        if remaining > 0:
            results_text += f"\n... and {remaining} more results.\n"

        results_text += f"\nPage {page + 1} of {total_pages}\n"
        results_text += "```"

        source_type = list(grouped.keys())[0]
        if (
            len(grouped) == 1 and len(grouped[source_type]) <= 5
        ):  # If 5 or fewer results
            footer_text = "\nEnd of search."
        else:
            footer_text = "\nFilter: " + " • ".join(filter_options)
            footer_text += "\n\nNavigation: ◀️ ▶️ Turn pages • ❌ End search"

        results_text += footer_text

        embed.add_field(name="Results", value=results_text, inline=False)

        return embed

    def _update_embed_for_end(
        self, embed: discord.Embed, reason: str = "End of search"
    ) -> discord.Embed:
        """Update embed to show search has ended"""
        if len(embed.fields) > 0:
            field = embed.fields[0]
            current_value = field.value
            if current_value is None:
                current_value = ""

            # Replace navigation text
            nav_texts = [
                "Navigation: ◀️ ▶️ Turn pages • ❌ End search",
                "◀️ ▶️ Turn pages • ❌ End search",
                "Filter: ",  # This marks the start of the navigation section
            ]

            for nav_text in nav_texts:
                if nav_text in current_value:
                    # Find where the navigation section starts
                    nav_index = current_value.find(nav_text)
                    if nav_index != -1:
                        # Keep everything before the navigation, add end message
                        new_value = current_value[:nav_index].rstrip() + f"\n\n{reason}"
                        break
            else:
                # If no navigation found (single page), look for "End of search." at bottom
                if "End of search." in current_value:
                    # Replace the existing "End of search." with reason
                    new_value = current_value.replace("End of search.", reason)
                else:
                    # If no navigation found, just append
                    new_value = current_value + f"\n\n{reason}"

            embed.set_field_at(0, name=field.name, value=new_value, inline=field.inline)

        return embed

    # ==== ?best ====

    def _analyze_fissures_for_item(
        self, fissures: List[Dict], item_relics: List[str]
    ) -> Dict:
        """Find active fissures relevant to an item's relic tiers"""
        relevant_fissures = []

        # Normalize relic tiers to lowercase
        normalized_relics = [tier.lower() for tier in item_relics]

        for fissure in fissures:
            fissure_tier = fissure.get("tier", "").lower()

            # Check if this fissure tier matches any relic tier
            if fissure_tier in normalized_relics:
                # Check if fissure is still active (not expired)
                time_left = self._time_remaining(fissure.get("expiry", ""))
                if time_left > 0:  # ONLY include active fissures
                    relevant_fissures.append(
                        {**fissure, "_time_left": time_left}  # Store calculated time
                    )

        # Sort by time remaining (soonest first)
        relevant_fissures.sort(key=lambda f: f["_time_left"])

        return {
            "count": len(relevant_fissures),
            "fissures": relevant_fissures[:6],  # Increased to 6 for better display
            "expiring_soon": [
                f for f in relevant_fissures if f["_time_left"] < 600
            ],  # 10 min
        }

    def _get_next_fissure_rotation(self) -> str:
        """Predict when new fissures will appear"""
        from datetime import datetime, timedelta

        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )

        minutes_to_next = int((next_hour - now).total_seconds() / 60)

        if minutes_to_next < 10:
            return "within 10 minutes"
        elif minutes_to_next < 30:
            return f"in {minutes_to_next} minutes"
        else:
            # Warframe fissures refresh hourly
            next_time = next_hour.strftime("%H:%M")
            return f"at {next_time}"

    def _time_remaining(self, expiry_str: str) -> int:
        """Calculate seconds until expiry - with better error handling"""
        try:
            # Clean up the date string
            if "Z" in expiry_str:
                expiry_str = expiry_str.replace("Z", "+00:00")

            # Parse the date
            expiry = datetime.fromisoformat(expiry_str)

            # Make sure we're not dealing with a date way in the future (API issue)
            now = datetime.now(timezone.utc)

            # If expiry is more than 48 hours in the future, it's probably wrong data
            max_reasonable = now + timedelta(hours=48)
            if expiry > max_reasonable:
                print(f"[WARN] Suspicious future date: {expiry} (now: {now})")
                # Assume it's a 1-hour fissure instead
                return 3600  # Default to 1 hour remaining

            # If expiry is in the past (negative), return 0
            if expiry < now:
                return 0

            # Calculate actual difference
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)

            delta = expiry - now
            return max(0, int(delta.total_seconds()))

        except Exception as e:
            print(f"[ERROR] Date parsing failed: {e}, input: {expiry_str}")
            # Default to a reasonable fissure duration
            return 1800  # 30 minutes as fallback

    def _format_time(self, seconds: int) -> str:
        """Format seconds to human-readable time - IMPROVED"""
        if seconds <= 0:
            return "0s"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            if secs > 0 and minutes < 5:  # Show seconds for short times
                return f"{minutes}m {secs}s"
            return f"{minutes}m"
        else:
            return f"{secs}s"

    def _is_item_in_sortie(self, item_name: str, sortie_data: Dict) -> bool:
        """Check if item is in sortie reward pool"""
        reward_pool = sortie_data.get("rewardPool", [])
        # Simple contains check - you might need to normalize item names
        return any(item_name.lower() in reward.lower() for reward in reward_pool)

    def _get_relic_tiers_for_item(self, item_name: str) -> List[str]:
        """Extract relic tiers for an item - FIXED VERSION"""
        if self.search_engine is None:
            return []

        results = self.search_engine.search_item(item_name)
        relic_tiers = set()

        for drop in results:
            if drop.get("source_type") == "Relics":
                # Try to get tier from various possible fields
                tier = (
                    drop.get("relic_tier")
                    or drop.get("tier")
                    or drop.get("relic_name", "").split()[0]
                    if " " in drop.get("relic_name", "")
                    else ""
                )

                if tier:
                    # Normalize: "Axi", "axi", "AXI" -> "axi"
                    relic_tiers.add(tier.lower())

        return list(relic_tiers)

    async def _get_game_state(self) -> Dict:
        """Fetch all relevant game state data"""
        try:
            fissures, sortie, nightwave = await asyncio.gather(
                self.warframe_api.get_fissures(),
                self.warframe_api.get_sortie(),
                self.warframe_api.get_nightwave(),
            )

            return {
                "fissures": fissures or [],
                "sortie": sortie or {},
                "nightwave": nightwave or {},
            }
        except Exception as e:
            logger.error(f"Failed to fetch game state: {e}")  # TODO Implement logging properly
            return {}

    def _build_best_response(
        self,
        item_name: str,
        best_source: Dict,
        best_chance: float,
        game_state: Dict,
        relic_tiers: List[str],
    ) -> str:
        """Build the enhanced ?best response - IMPROVED DISPLAY"""

        # 1. Best source header
        response = f"**{item_name}**\n\n"
        response += f"**BEST SINGLE SOURCE:** {best_chance:.1f}% chance\n"

        # Format source details
        source_text = self._format_source(best_source)
        response += f"{source_text}\n\n"

        # 2. Current opportunities section
        fissure_info = self._analyze_fissures_for_item(
            game_state.get("fissures", []), relic_tiers
        )

        if fissure_info["count"] == 0:
            next_rotation = self._get_next_fissure_rotation()
            response += f"**Next rotation:** {next_rotation}\n"

        if fissure_info["count"] > 0:
            response += f"**ACTIVE FISSURES:** {fissure_info['count']} available\n"

            # Group by mission type and show most relevant
            mission_types = {}

            for fissure in fissure_info["fissures"]:
                mission_type = fissure.get("missionType", "Mission")
                if mission_type not in mission_types:
                    mission_types[mission_type] = []

                node = fissure.get("node", "Unknown")
                time_left = fissure["_time_left"]

                # Extract planet name
                planet = "Unknown"
                if "(" in node and ")" in node:
                    planet = node.split("(")[1].split(")")[0]

                mission_types[mission_type].append(
                    {
                        "planet": planet,
                        "time": time_left,
                        "formatted": self._format_time(time_left),
                    }
                )

            # Show mission types in order: Fast → Medium → Slow
            fast_types = ["Capture", "Exterminate", "Rescue", "Sabotage"]
            medium_types = ["Mobile Defense", "Spy", "Hijack"]
            slow_types = ["Defense", "Survival", "Interception", "Excavation"]

            displayed = 0
            max_to_show = 3  # Show max 3 mission types

            # Show fast missions first
            for mission_type in fast_types:
                if mission_type in mission_types and displayed < max_to_show:
                    missions = mission_types[mission_type]
                    response += f"**{mission_type}:** "
                    planets = [m["planet"] for m in missions[:2]]
                    response += ", ".join(planets)
                    if len(missions) > 2:
                        response += f" (+{len(missions)-2})"
                    # Show time for soonest one
                    soonest = min(missions, key=lambda m: m["time"])
                    response += f" ({soonest['formatted']})\n"
                    displayed += 1

            # Show medium if we haven't shown enough
            if displayed < max_to_show:
                for mission_type in medium_types:
                    if mission_type in mission_types and displayed < max_to_show:
                        missions = mission_types[mission_type]
                        response += f"**{mission_type}:** "
                        planets = [m["planet"] for m in missions[:2]]
                        response += ", ".join(planets)
                        if len(missions) > 2:
                            response += f" (+{len(missions)-2})"
                        soonest = min(missions, key=lambda m: m["time"])
                        response += f" ({soonest['formatted']})\n"
                        displayed += 1

            # Show slow if we haven't shown enough
            if displayed < max_to_show:
                for mission_type in slow_types:
                    if mission_type in mission_types and displayed < max_to_show:
                        missions = mission_types[mission_type]
                        response += f"**{mission_type}:** "
                        planets = [m["planet"] for m in missions[:2]]
                        response += ", ".join(planets)
                        if len(missions) > 2:
                            response += f" (+{len(missions)-2})"
                        soonest = min(missions, key=lambda m: m["time"])
                        response += f" ({soonest['formatted']})\n"
                        displayed += 1

            # Show expiry warning if any are ending soon
            if fissure_info["expiring_soon"]:
                soonest = min(
                    fissure_info["expiring_soon"], key=lambda f: f["_time_left"]
                )
                response += f"**Ending soon:** {self._format_time(soonest['_time_left'])} left\n"

        else:
            # No active fissures - check if any will spawn soon
            response += "**No active fissures** for this tier right now\n"
            response += "Check back in 30-60 minutes for new rotations\n"

        # 3. Sortie check
        sortie = game_state.get("sortie", {})
        if self._is_item_in_sortie(item_name, sortie):
            response += f"\n**TODAY'S SORTIE:** {sortie.get('boss', 'Sortie')}\n"
            response += "   Contains this item! (28% chance)\n"

        response += "\n"

        # 4. Strategy - IMPROVED CALCULATIONS
        response += "**STRATEGY:**\n"

        if best_chance > 0:
            # Better probability calculations
            import math

            chance_decimal = best_chance / 100.0

            # Runs for 50% confidence
            runs_50 = (
                math.ceil(math.log(0.5) / math.log(1 - chance_decimal))
                if chance_decimal < 1
                else 1
            )
            # Runs for 90% confidence
            runs_90 = (
                math.ceil(math.log(0.1) / math.log(1 - chance_decimal))
                if chance_decimal < 1
                else 1
            )

            if best_chance < 2.0:
                response += f"**Very Rare:** {best_chance:.1f}% chance\n"
                response += f"• {runs_50} runs for 50% chance\n"
                response += f"• {runs_90}+ runs for reliable drop\n"
            elif best_chance < 10.0:
                response += f"**Uncommon:** {best_chance:.1f}% chance\n"
                response += f"• {runs_50} runs: 50% chance\n"
                response += f"• {runs_90} runs: 90% chance\n"
            else:
                response += f"**Common:** {best_chance:.1f}% chance\n"
                response += f"• {runs_50} runs: 50% chance\n"
                response += f"• {runs_90} runs: 90% chance\n"

        # 5. Actionable tips
        response += "\n**ACTION PLAN:**\n"

        if fissure_info["count"] > 0:
            # Count fast missions
            fast_count = sum(
                1
                for f in fissure_info["fissures"]
                if f.get("missionType")
                in ["Capture", "Exterminate", "Rescue", "Sabotage"]
            )

            if fast_count > 0:
                response += f"1. Run {fast_count} fast fissures first\n"
                response += "2. Refine relics to Radiant\n"
                response += "3. Bring a squad for 4x chances\n"
            else:
                response += "1. Pick shortest available mission\n"
                response += "2. Consider relic refinement\n"
                response += "3. Farm in squad if possible\n"
        else:
            response += "1. Wait for new fissure rotation\n"
            response += "2. Farm void traces in meantime\n"
            response += "3. Check other drop sources\n"

        # Add relic-specific tips
        if best_source.get("source_type") == "Relics":
            refinement = best_source.get("relic_refinement", "Intact")
            if refinement == "Intact":
                response += "\n**Upgrade:** Refine to Radiant for **{:.1f}% → {:.1f}%** chance".format(
                    best_chance, min(100, best_chance * 2)
                )

        return response

    def _format_source(self, source: Dict) -> str:
        """Format a source for display - more detailed"""
        source_type = source.get("source_type", "Unknown")

        if source_type == "Missions":
            details = f"**{source.get('planet_name', '?')}** - "
            details += f"*{source.get('mission_name', '?')}*\n"
            details += f"   Type: {source.get('mission_type', '?')}"
            rotation = source.get("rotation")
            if rotation:
                details += f" • Rotation: {rotation}"
            return details

        elif source_type == "Relics":
            details = (
                f"**{source.get('relic_tier', '?')} {source.get('relic_name', '?')}**\n"
            )
            refinement = source.get("relic_refinement", "Intact")
            if refinement != "Intact":
                details += f"   Refinement: {refinement}"
            else:
                details += f"   (Can refine to Radiant for better chance)"
            return details

        elif source_type == "Bounties":
            details = f"**{source.get('planet_name', '?')}** - "
            details += f"*{source.get('mission_name', '?')}*\n"
            bounty_type = source.get("mission_type")
            if bounty_type:
                details += f"   Bounty: {bounty_type}"
            return details

        else:  # Sorties
            return "**Sortie Mission Reward**\n   (Daily completion, 28% chance)"

    # ==== DEBUG ====

    async def debug_fissures(self, ctx):
        """Debug command to check fissure data with system time comparison"""
        fissures = await self.warframe_api.get_fissures()

        if not fissures:
            await ctx.send("❌ No fissure data received")
            return

        # Get current time
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()

        embed = discord.Embed(
            title="🔧 System & Fissure Debug",
            color=discord.Color.gold(),
            description=f"**System UTC:** {now_utc}\n**System Local:** {now_local}",
        )

        # Check first 3 fissures
        for i, fissure in enumerate(fissures[:3], 1):
            tier = fissure.get("tier", "N/A")
            node = fissure.get("node", "N/A")
            mission = fissure.get("missionType", "N/A")
            expiry_raw = fissure.get("expiry", "N/A")

            # Parse the date
            try:
                if "Z" in expiry_raw:
                    expiry_str = expiry_raw.replace("Z", "+00:00")
                    expiry = datetime.fromisoformat(expiry_str)

                    # Calculate difference
                    if expiry.tzinfo is None:
                        expiry = expiry.replace(tzinfo=timezone.utc)

                    diff = expiry - now_utc
                    days_diff = diff.days
                    seconds_diff = diff.total_seconds()

                    status = "✅ FUTURE" if seconds_diff > 0 else "❌ PAST"

                    field_value = (
                        f"**Tier:** {tier}\n"
                        f"**Node:** {node}\n"
                        f"**Mission:** {mission}\n"
                        f"**API Expiry:** {expiry_raw}\n"
                        f"**Parsed:** {expiry}\n"
                        f"**Status:** {status}\n"
                        f"**Days Diff:** {days_diff} days\n"
                        f"**Seconds:** {int(seconds_diff)}s\n"
                        f"**Our calc:** {self._time_remaining(expiry_raw)}s"
                    )
                else:
                    field_value = f"**ERROR:** Invalid date format: {expiry_raw}"

            except Exception as e:
                field_value = f"**ERROR:** {str(e)}\n**Raw:** {expiry_raw}"

            embed.add_field(
                name=f"Fissure {i} ({tier})", value=field_value, inline=False
            )

        await ctx.send(embed=embed)

    def run(self):
        """Start the Discord bot"""
        from config import DISCORD_TOKEN

        if not DISCORD_TOKEN or DISCORD_TOKEN == "DEV_MODE_NO_TOKEN":
            print("\n⚠ DISCORD_TOKEN not set!")
            print('  Rename ".env.example" to ".env" and add your token there.\n')
            sys.exit(1)

        print("Starting Discord bot...")
        self.bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    bot = WarframeBuddyDiscordBot()
    bot.run
