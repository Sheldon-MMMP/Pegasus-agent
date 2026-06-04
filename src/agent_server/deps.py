from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from agent_server.db import get_db
DbSession = Annotated[Session, Depends(get_db)]