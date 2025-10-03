"""
Celery Beat scheduler configuration for periodic background tasks

This module configures the periodic scheduling of all background tasks
for the Galactic Empire game.
"""

from celery.schedules import crontab
from app.core.celery import celery_app

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Main game tick - runs every 10 seconds
    'game-tick': {
        'task': 'app.tasks.game_tasks.game_tick',
        'schedule': 10.0,  # 10 seconds
    },
    
    # Ship position updates - runs every 5 seconds
    'ship-positions': {
        'task': 'app.tasks.ship_tasks.update_ship_positions',
        'schedule': 5.0,  # 5 seconds
    },
    
    # Ship combat processing - runs every 3 seconds
    'ship-combat': {
        'task': 'app.tasks.ship_tasks.process_ship_combat',
        'schedule': 3.0,  # 3 seconds
    },
    
    # Ship system updates - runs every 5 seconds
    'ship-systems': {
        'task': 'app.tasks.ship_tasks.update_ship_systems',
        'schedule': 5.0,  # 5 seconds
    },
    
    # Planet production - runs every 30 seconds
    'planet-production': {
        'task': 'app.tasks.planet_tasks.update_planet_production',
        'schedule': 30.0,  # 30 seconds
    },
    
    # Planet taxes - runs every 60 seconds
    'planet-taxes': {
        'task': 'app.tasks.planet_tasks.process_planet_taxes',
        'schedule': 60.0,  # 60 seconds
    },
    
    # Planet population - runs every 120 seconds
    'planet-population': {
        'task': 'app.tasks.planet_tasks.update_planet_population',
        'schedule': 120.0,  # 2 minutes
    },
    
    # Planet economy - runs every 60 seconds
    'planet-economy': {
        'task': 'app.tasks.planet_tasks.process_planet_economy',
        'schedule': 60.0,  # 60 seconds
    },
    
    # Cleanup expired items - runs every hour
    'cleanup-expired': {
        'task': 'app.tasks.game_tasks.cleanup_expired_items',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Update leaderboards - runs every 5 minutes
    'update-leaderboards': {
        'task': 'app.tasks.game_tasks.update_leaderboards',
        'schedule': 300.0,  # 5 minutes
    },
    
    # Process game events - runs every 30 seconds
    'game-events': {
        'task': 'app.tasks.game_tasks.process_game_events',
        'schedule': 30.0,  # 30 seconds
    },
    
    # Broadcast game state - runs every 2 seconds
    'broadcast-game-state': {
        'task': 'app.tasks.game_engine_tasks.broadcast_game_state',
        'schedule': 2.0,  # 2 seconds
    },
    
    # Process real-time events - runs every 1 second
    'real-time-events': {
        'task': 'app.tasks.game_engine_tasks.process_real_time_events',
        'schedule': 1.0,  # 1 second
    },
    
    # Sync game engine state - runs every 30 seconds
    'sync-game-engine': {
        'task': 'app.tasks.game_engine_tasks.sync_game_engine_state',
        'schedule': 30.0,  # 30 seconds
    },
    
    # Cleanup abandoned planets - runs daily at midnight
    'cleanup-abandoned-planets': {
        'task': 'app.tasks.planet_tasks.cleanup_abandoned_planets',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    
    # Cleanup game engine cache - runs every 10 minutes
    'cleanup-game-engine-cache': {
        'task': 'app.tasks.game_engine_tasks.cleanup_game_engine_cache',
        'schedule': 600.0,  # 10 minutes
    },
}

# Set timezone for scheduled tasks
celery_app.conf.timezone = 'UTC'

# Task routing for different priorities
celery_app.conf.task_routes = {
    # High priority real-time tasks
    'app.tasks.game_engine_tasks.process_real_time_events': {'priority': 10},
    'app.tasks.game_engine_tasks.broadcast_game_state': {'priority': 9},
    
    # Medium priority game logic tasks
    'app.tasks.ship_tasks.update_ship_positions': {'priority': 8},
    'app.tasks.ship_tasks.process_ship_combat': {'priority': 8},
    'app.tasks.ship_tasks.update_ship_systems': {'priority': 7},
    'app.tasks.game_tasks.game_tick': {'priority': 7},
    
    # Lower priority maintenance tasks
    'app.tasks.planet_tasks.update_planet_production': {'priority': 5},
    'app.tasks.planet_tasks.process_planet_taxes': {'priority': 5},
    'app.tasks.planet_tasks.update_planet_population': {'priority': 4},
    'app.tasks.planet_tasks.process_planet_economy': {'priority': 4},
    
    # Background maintenance tasks
    'app.tasks.game_tasks.cleanup_expired_items': {'priority': 3},
    'app.tasks.game_tasks.update_leaderboards': {'priority': 3},
    'app.tasks.game_tasks.process_game_events': {'priority': 3},
    'app.tasks.game_engine_tasks.sync_game_engine_state': {'priority': 2},
    'app.tasks.game_engine_tasks.cleanup_game_engine_cache': {'priority': 2},
    'app.tasks.planet_tasks.cleanup_abandoned_planets': {'priority': 1},
}

# Worker configuration
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
celery_app.conf.worker_max_tasks_per_child = 1000

# Result backend configuration
celery_app.conf.result_expires = 3600  # Results expire after 1 hour
celery_app.conf.result_persistent = True

# Task execution configuration
celery_app.conf.task_always_eager = False  # Set to True for testing
celery_app.conf.task_eager_propagates = True
celery_app.conf.task_ignore_result = False

# Logging configuration
celery_app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
celery_app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Error handling
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_default_retry_delay = 60  # Retry after 60 seconds
celery_app.conf.task_max_retries = 3
