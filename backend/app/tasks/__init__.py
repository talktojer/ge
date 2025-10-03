# Background tasks
from ..core.celery import celery_app

# Import all task modules
from . import ship_tasks
from . import planet_tasks  
from . import game_tasks
from . import game_engine_tasks

__all__ = [
    "celery_app",
    "ship_tasks",
    "planet_tasks", 
    "game_tasks",
    "game_engine_tasks"
]
