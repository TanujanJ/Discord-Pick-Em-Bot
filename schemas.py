# External imports 
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LeagueCreate(BaseModel):
    league_name: str

class LeagueResponse(BaseModel):
    league_id: int
    league_name: str

    model_config = {"from_attributes": True} # Allows data to be extracted from object attributes


class GameCreate(BaseModel):
    league_id: int
    away_team: str
    home_team: str
    start_time: datetime

class GameResponse(BaseModel):
    game_id: int
    league_id: int
    away_team: str
    home_team: str
    game_result: Optional[str] # Game result is not known immediately, so it is not given a value 
    start_time: datetime

    model_config = {"from_attributes": True}

class GameResultUpdate(BaseModel):
    game_result: str