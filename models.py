# External imports
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, DateTime, Boolean, ForeignKey, UniqueConstraint
from typing import Optional, List
from datetime import datetime

# Class to be inherited so SQLAlchemy can map the classes to database tables
class Base(DeclarativeBase): pass

# The user object holds a user's discord id and discord username
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True) # Must be mapped to BigInteger because discord id's are larger than the normal int range
    username: Mapped[str] = mapped_column(String)

    # The user object can also access the predictions the user has made which is a list of the prediction object
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="user")
    user_league_scores: Mapped[List["UserLeagueScore"]] = relationship("UserLeagueScore", back_populates="user")

# The league object holds a league's id and name
class League(Base):
    __tablename__ = "leagues"
    league_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    league_name: Mapped[str] = mapped_column(String, unique=True)

    # The league object can also access the games that are taking place in the league which is a list comprised of the game object
    games: Mapped[List["Game"]] = relationship("Game", back_populates="league")
    user_league_scores: Mapped[List["UserLeagueScore"]] = relationship("UserLeagueScore", back_populates="league")


# The game object holds a game's id, API id, away and home teams, result, and start time
class Game(Base):
    __tablename__ = "games"
    game_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    api_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    away_team: Mapped[str] = mapped_column(String)
    home_team: Mapped[str] = mapped_column(String)
    game_result: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # The object can also access the id of its league from the leagues table, as well as the league and predictions on the game 
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.league_id"))

    league: Mapped["League"] = relationship("League", back_populates="games")
    predictions: Mapped[List["Prediction"]] = relationship("Prediction", back_populates="game")

# The prediction object holds a prediction, the prediction id, and whether the prediction was right or not
class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_prediction: Mapped[str] = mapped_column(String)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # The object can also access the user, the game, and their respective ids
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.game_id"))

    user: Mapped["User"] = relationship("User", back_populates="predictions")
    game: Mapped["Game"] = relationship("Game", back_populates="predictions")

    __table_args__ = (UniqueConstraint("user_id", "game_id"),) # This ensures an individual user can only make one prediction on each game on a database level

class UserLeagueScore(Base):
    __tablename__ = "user_league_scores"
    score_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.league_id"))

    user: Mapped["User"] = relationship("User", back_populates="user_league_scores")
    league: Mapped["League"] = relationship("League", back_populates="user_league_scores")

    __table_args__ = (UniqueConstraint("user_id", "league_id"),)