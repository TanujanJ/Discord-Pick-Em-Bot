# External imports
import asyncio
import discord
import aiohttp
from discord.ext import commands, tasks
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone

# Internal imports
from database import async_session_local
from models import User, Game, Prediction, League, UserLeagueScore
from config import settings
from admin import router
from list_view import GamesListView

# Obtain discord token
TOKEN = settings.DISCORD_TOKEN.get_secret_value()

# Intents filters what the bot can read so it does not get hit with unnecessary events 
# Default includes all the standard non-privileged intents
intents = discord.Intents.default()

# Message content and members are privileged intents and require a setting turned on in Discord Developer Portal
intents.message_content = True
intents.members = True

# Commands are used by prefixing the command with an exclamation mark
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def register(ctx):
    async with async_session_local() as session:
        # Obtain the user info and assign it to a user object
        user_id = ctx.author.id
        username = ctx.author.name
        user = User()
        user.id = user_id
        user.username = username

        # Try to register user to the bot and alert the user in the case of already being registered
        try:
            session.add(user)
            await session.commit()
            await ctx.send("You are now registered for the Pick 'Em Bot. \nUse !leagues to view available leagues to play with \nUse, !predict <game_id> \"<team_pick>\", to make a prediction.\nUse, !games <league_name>, to view upcoming games and their IDs.\nUse, !leaderboard <league_name>, to view the server-wide leaderboard.")
        except IntegrityError:
            await session.rollback()
            await ctx.send("You are already registered")

@bot.command()
async def predict(ctx, game_id: int, team_pick: str):
    async with async_session_local() as session:
        #Obtain the user and check if the user is registered, if not inform the user to register and exit
        user = await session.scalar(select(User).where(User.id == ctx.author.id))
        if user is None:
            await ctx.send("Use !register before making predictions")
            return

        #Obtain the game
        stmt = select(Game).where(Game.game_id == game_id)
        result = await session.execute(stmt)
        game = result.scalars().first()

        #Check if the game exists
        if game is None:
            await ctx.send("This game does not exist")
            return
        
        #Check if the deadline to predict has passed
        now = datetime.now(timezone.utc)
        if (game.start_time < now): 
            await ctx.send("This game has already started")
            return
        
        #Check if the predicted team is playing in the game
        if team_pick not in [game.away_team, game.home_team]:
            await ctx.send("That team is not an option")
            return

        #Create and assign values to the prediction object
        prediction = Prediction()
        prediction.user_id = ctx.author.id
        prediction.game_id = game_id 
        prediction.user_prediction = team_pick

        # Try to commit the prediction, if it is a duplicate prediction alert the user and revert changes
        try:
            session.add(prediction)
            await session.commit()
            await ctx.send("Prediction successful")
            
        except IntegrityError:
            await session.rollback()
            await ctx.send("Prediction failed")

@bot.command()
async def leaderboard (ctx, league_name: str):
    async with async_session_local() as session:
        # Obtain the league and alert the user if it does not exist
        league = await session.scalar(select(League).where(League.league_name == league_name))       
        if not league:
            await ctx.send("This league does not exist")
            return

        # Obtain server members
        server_members_ids = [member.id for member in ctx.guild.members]

        #Obtain top ten users in score
        stmt = select(UserLeagueScore).where(UserLeagueScore.league_id==league.league_id, UserLeagueScore.user_id.in_(server_members_ids)).options(joinedload(UserLeagueScore.user)).order_by(desc(UserLeagueScore.score)).limit(10)
        result = await session.execute(stmt)
        top_ten = result.scalars().all()

        #If no users exist exit the function
        if not top_ten:
            await ctx.send("No users found.")
            return
        
        # Print top ten users
        leaderboard_string = []
        for i, record in enumerate(top_ten, start=1):
            leaderboard_string.append(f"#{i}. {record.user.username} - {record.score} pts\n")

        await ctx.send("".join(leaderboard_string))

@bot.command()
async def games(ctx, league_name: str):
    async with async_session_local() as session:
        # Obtain the league and alert the user if it does not exist
        league = await session.scalar(select(League).where(League.league_name == league_name))       
        if not league:
            await ctx.send("This league does not exist")
            return

        # Obtain the closest 11 games by time
        # 11th game will not be shown, instead used to check if there are more games after the current list
        stmt = select(Game).where(Game.league_id == league.league_id, Game.start_time > datetime.now(timezone.utc), Game.game_result.is_(None)).order_by(Game.start_time.asc()).limit(11)
        result = await session.execute(stmt)
        upcoming_games = result.scalars().all()

        # Create the view object and set initial button modes
        view = GamesListView(ctx.author.id, league.league_id, 0, async_session_local)
        view.previous_button.disabled = True # Disable the previous button because it will show games 1-10 initially so there are no previous games        
        # Disable the next button if there is not an 11th game because there are no more games to scroll to
        if len(upcoming_games) < 11:
            view.next_button.disabled = True
        else:
            view.next_button.disabled = False

        upcoming_games_string = []
        for game in upcoming_games[:10]:
            # Format the games to show its ID, its teams, date, and start time into a list
            upcoming_games_string.append(f"ID: {game.game_id} | {game.away_team} @ {game.home_team} | Starts: {game.start_time.strftime('%Y-%m-%d %H:%M UTC')}\n")
        
        # Bring the games together from the list into one string
        games_formatted = "".join(upcoming_games_string)

        # If no games exist, return no upcoming games found and return
        if not upcoming_games:
            await ctx.send("No upcoming games found")
            return

        # Send game information to user and update it based on user interactions or timeout
        message = await ctx.send(games_formatted, view=view)
        view.message = message       

@bot.command()
async def leagues(ctx):
    async with async_session_local() as session:
        # Obtain all of the leagues
        stmt = select(League)
        result = await session.execute(stmt)
        leagues = result.scalars().all()

        # If no leagues exist alert the user and return
        if not leagues:
            await ctx.send("No leagues found")
            return

        # Format the leagues in a single string to be sent
        leagues_array = []
        for league in leagues:
            leagues_array.append(league.league_name)
        leagues_string = ", ".join(leagues_array)

        await ctx.send(leagues_string)

# Check for a new game schedule every 24 hours
@tasks.loop(hours=24)
async def fetch_schedule():
    # League APIs from ESPN used to obtain game information
    endpoints = {
        1: "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        2: "http://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        3: "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        4: "http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
    }

    # Sets up connection pool so that connections can be created and reused later on
    async with aiohttp.ClientSession() as http_session:
        async with async_session_local() as session:
            for league_id, url in endpoints.items():
                # Use a connection from the connection pool to the link so data can be taken
                async with http_session.get(url) as response:
                    json_data = await response.json()

                    # If is nothing is in the data move on to the next league url, and if that was the last one then end the loop
                    if "events" not in json_data:
                        continue

                    # Edit data to fit the Game model then create a game object
                    for game in json_data["events"]:
                        time = datetime.fromisoformat(game["date"].replace('Z', '+00:00')) # Convert the time type to datetime
                        teams = game["name"].split(" at ") # Format the team name display
                        new_game = Game(api_id=game["id"], start_time=time, away_team=teams[0], home_team=teams[1], league_id=league_id)
                        
                        # Try to add the game to the database and revert changes if the game already exists in the database
                        try:
                            session.add(new_game)
                            await session.commit()
                        except IntegrityError:
                            await session.rollback()

# FastAPI and discord.py both run on a asyncio loop, so to prevent interference and the bot crashing you must run them alongside eachother
# This is done by having both entities run under one main loop managed by Uvicorn
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(bot.start(TOKEN))
    fetch_schedule.start()
    yield 

    await bot.close()

app = FastAPI(lifespan=lifespan)
app.include_router(router)