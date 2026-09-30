# External imports
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from typing import List
from sqlalchemy.orm import joinedload

# Internal imports 
from schemas import LeagueResponse, LeagueCreate, GameResponse, GameCreate, GameResultUpdate
from database import get_db, AsyncSession
from models import League, Game, Prediction, UserLeagueScore
from config import settings

# Securing admin login
api_key_header = APIKeyHeader(name = "X-Admin-Key")
def get_admin_key(api_key: str = Security(api_key_header)):
    if api_key != settings.ADMIN_API_KEY.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid Admin Key")
    return api_key

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_key)]) # Requires correct admin key to use router features

# Creates a new league and loads it onto the database
@router.post("/leagues", response_model=LeagueResponse)
async def post_league(league_data: LeagueCreate, db: AsyncSession = Depends(get_db)):
    new_league = League(league_name = league_data.league_name)

    db.add(new_league)
    await db.commit()
    await db.refresh(new_league)

    return new_league

# Retrieves all of the leagues from the database
@router.get("/leagues", response_model=List[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db)):
    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()

    return leagues

# Creates a game and uploads it to the database
@router.post("/games", response_model=GameResponse)
async def post_game(game_data: GameCreate, db: AsyncSession = Depends(get_db)):
    new_game = Game(away_team = game_data.away_team,
                    home_team = game_data.home_team,
                    start_time = game_data.start_time,
                    league_id = game_data.league_id)
    
    db.add(new_game)
    await db.commit()
    await db.refresh(new_game)

    return new_game

# Retrieves a game from the database, updates its game result, assesses whether the user was correct or not to change the score if it was correct, then send the data back to the database
@router.patch("/games/{game_id}/result", response_model=GameResponse)
async def game_result(game_data: GameResultUpdate, game_id: int, db: AsyncSession = Depends(get_db)):
    game = await db.scalar(select(Game).where(Game.game_id == game_id))

    if game is None:
        raise HTTPException(status_code=404, detail="Game does not exist")
    
    # Obtain all predictions on the given game
    stmt = (select(Prediction).where(Prediction.game_id == game_id).options(joinedload(Prediction.user)))
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    if game_data.game_result not in [game.home_team, game.away_team]:
        raise HTTPException(status_code=400, detail="Result must be one of the two teams playing")

    game.game_result = game_data.game_result

    # For each prediction check if they predicted correctly, if so add to their score
    for prediction in predictions:
        if game.game_result is not None:
            raise HTTPException(status_code=409, detail="Game result has already been recorded")
        
        if prediction.user_prediction == game.game_result:
            record = await db.scalar(select(UserLeagueScore).where(UserLeagueScore.user_id == prediction.user_id, UserLeagueScore.league_id == game.league_id))
            prediction.is_correct = True
            # If they have already recorded a score then simply add to it, if not then add the user's and league's information to the database using the UserLeagueScore model with a score of 1, accounting for their first point
            if record:
                record.score += 1
            else:
                db.add(UserLeagueScore(user_id=prediction.user_id, league_id=game.league_id, score=1))
        else:
            prediction.is_correct = False

    await db.commit()
    await db.refresh(game)

    return game


