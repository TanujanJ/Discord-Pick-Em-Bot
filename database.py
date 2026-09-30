# External imports
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Internal imports
from config import settings

# The engine manages database pooling so connections can be reused, session requests go through the engine to work with the database driver 
engine = create_async_engine(settings.DATABASE_URL, echo = True, pool_pre_ping = True)

# The session manages all of the objects' interactions with the database 
async_session_local = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Provides a database session and closes it when finished
async def get_db():
    async with async_session_local() as session:
        yield session
