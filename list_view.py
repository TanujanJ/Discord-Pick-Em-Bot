# External imports
import discord
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import async_sessionmaker

# Internal imports
from models import Game
from sqlalchemy import select

class GamesListView(discord.ui.View):
    def __init__(self, author_id: int, league_id: int, offset: int, session_factory: async_sessionmaker):
        super().__init__(timeout=300) # Inherited from discord.ui.View, timeout is set to 5 minutes
        self.author_id = author_id
        self.league_id = league_id
        self.offset = offset
        self.session_factory = session_factory

    # Only the user who created the view can interact with it, otherwise the interaction will be rejected
    async def interaction_check(self, interaction: discord.Interaction):
        if (self.author_id != interaction.user.id):
            return False
        return True
    
    # Edit view based on interaction
    async def update_games(self, interaction: discord.Interaction):
        async with self.session_factory() as session:
            # Obtain the next 11 games
            stmt = select(Game).where(Game.league_id == self.league_id, Game.start_time > datetime.now(timezone.utc), Game.game_result.is_(None)).order_by(Game.start_time.asc()).offset(self.offset).limit(11)
            result = await session.execute(stmt)
            game_list = result.scalars().all()  
            
        # If on the first 10 games, 0 offset, disable the previous button
        if self.offset == 0:
            self.previous_button.disabled = True
        else:
            self.previous_button.disabled = False

        # Disable the next button if there is not an 11th game because there are no more games to scroll to
        if len(game_list) < 11:
            self.next_button.disabled = True
        else:
            self.next_button.disabled = False

        upcoming_games_array = []
        # Format upcoming games and put into a single string
        for game in game_list[:10]:
            upcoming_games_array.append(f"ID: {game.game_id} | {game.away_team} @ {game.home_team} | Starts: {game.start_time.strftime('%Y-%m-%d %H:%M UTC')}\n")        
        upcoming_games_string = "".join(upcoming_games_array)
        
        # Deliver view edits
        await interaction.response.edit_message(content=upcoming_games_string, view=self)

    # Creating Previous button        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.offset = max(0, self.offset - 10) # Subtract 10 from offset when Previous button is clicked, but ensure offset does not go below 0
        await self.update_games(interaction)

    # Creating Next button
    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.offset += 10 # Add 10 to offset when Next button is clicked
        await self.update_games(interaction)

    # Delete the view on timeout
    async def on_timeout(self):
        await self.message.delete()
