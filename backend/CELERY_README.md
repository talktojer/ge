# Galactic Empire - Background Task System

This document describes the complete background task processing system implemented for the Galactic Empire game, based on the original C code's real-time tick processing.

## Overview

The background task system uses Celery to process game logic asynchronously, replicating the original game's real-time tick system (`warrti`, `warrti2`, `warrti3`, `plarti`, `autorti`).

## Architecture

### Core Components

1. **Ship Tasks** (`ship_tasks.py`)
   - Ship movement and navigation
   - Combat processing
   - System updates (energy, shields, etc.)

2. **Planet Tasks** (`planet_tasks.py`)
   - Production and resource generation
   - Tax collection and economy
   - Population growth
   - Environmental changes

3. **Game Tasks** (`game_tasks.py`)
   - Main game tick processing
   - AI behavior (Cyborgs and Droids)
   - Cleanup and maintenance
   - Leaderboard updates

4. **Game Engine Tasks** (`game_engine_tasks.py`)
   - Real-time WebSocket updates
   - Game state synchronization
   - Cache management

## Task Scheduling

### High Priority (Real-time)
- **Real-time events**: Every 1 second
- **Game state broadcast**: Every 2 seconds
- **Ship position updates**: Every 5 seconds
- **Ship combat processing**: Every 3 seconds

### Medium Priority (Game Logic)
- **Main game tick**: Every 10 seconds
- **Ship system updates**: Every 5 seconds
- **Planet production**: Every 30 seconds
- **Planet taxes**: Every 60 seconds

### Low Priority (Maintenance)
- **Planet population**: Every 2 minutes
- **Leaderboard updates**: Every 5 minutes
- **Cleanup tasks**: Every hour
- **Abandoned planet cleanup**: Daily

## Implementation Details

### Ship Movement System
```python
# Based on original WARSHP structure
def _process_ship_movement(db: Session, ship: Ship) -> None:
    # Calculate acceleration/deceleration
    # Update heading changes
    # Apply movement vector
    # Handle galaxy wrapping
```

### Combat System
```python
# Replicates original combat functions
def _process_ship_combat(db: Session, ships: List[Ship]) -> None:
    # Mine encounters
    # Ship-to-ship combat
    # AI behavior
    # Weapon cooldowns
```

### Planet Economy
```python
# Based on original GALPLNT structure
def _process_planet_production(db: Session, planet: Planet) -> None:
    # Calculate production modifiers
    # Apply environment/resource effects
    # Update item quantities
    # Handle population growth
```

### AI Systems
```python
# Cyborg AI (aggressive, tactical)
def _process_cyborg_behavior(db: Session, cyborg_ship: Ship) -> None:
    # Target assessment
    # Advanced tactics
    # Strategic mine laying

# Droid AI (methodical, predictable)
def _process_droid_behavior(db: Session, droid_ship: Ship) -> None:
    # Pattern-based behavior
    # Patrol/defend/hunt/rest cycles
    # Self-repair abilities
```

## Running the System

### Development
```bash
# Start Celery worker and beat scheduler
python start_celery.py

# Or run individually:
celery -A app.core.celery:celery_app worker --loglevel=info
celery -A app.core.celery:celery_app beat --loglevel=info
```

### Production (Docker)
```bash
# Start complete system with Celery
docker-compose -f docker-compose.celery.yml up -d

# Monitor with Flower
open http://localhost:5555
```

### Docker Services
- **celery-worker**: Processes background tasks
- **celery-beat**: Schedules periodic tasks
- **flower**: Web-based monitoring interface
- **redis**: Message broker and result backend
- **db**: PostgreSQL database

## Monitoring

### Flower Interface
- URL: http://localhost:5555
- Monitor active tasks
- View task history
- Inspect worker status
- Real-time task execution

### Logs
```bash
# View worker logs
docker-compose -f docker-compose.celery.yml logs celery-worker

# View beat scheduler logs
docker-compose -f docker-compose.celery.yml logs celery-beat

# View all logs
docker-compose -f docker-compose.celery.yml logs
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/db
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0
```

### Task Priorities
- **10**: Real-time events, WebSocket broadcasts
- **8-9**: Ship movement, combat processing
- **5-7**: Planet systems, game tick
- **3-4**: Economy, population, taxes
- **1-2**: Cleanup, maintenance, cache

### Worker Configuration
- **Concurrency**: 4 workers per instance
- **Prefetch**: 1 task per worker
- **Time limits**: 30 minutes max, 25 minutes soft
- **Retries**: 3 attempts with 60-second delay

## Performance Considerations

### Database Optimization
- Batch database operations
- Use connection pooling
- Index frequently queried fields
- Clean up old data regularly

### Memory Management
- Workers restart after 1000 tasks
- Clear caches periodically
- Monitor memory usage
- Use Redis for caching

### Scaling
- Add more worker instances
- Use separate queues for different priorities
- Distribute workers across machines
- Monitor queue lengths

## Troubleshooting

### Common Issues

1. **Tasks not executing**
   - Check Redis connection
   - Verify worker is running
   - Check task routing

2. **High memory usage**
   - Reduce worker concurrency
   - Increase worker restart frequency
   - Clear caches more often

3. **Database connection errors**
   - Check connection pool settings
   - Verify database is accessible
   - Monitor connection limits

### Debug Commands
```bash
# Check worker status
celery -A app.core.celery:celery_app inspect active

# Check scheduled tasks
celery -A app.core.celery:celery_app inspect scheduled

# Check registered tasks
celery -A app.core.celery:celery_app inspect registered

# Purge all tasks
celery -A app.core.celery:celery_app purge
```

## Integration with Original Game

This system replicates the following original C functions:

### Ship Processing (`warrti`, `warrti2`, `warrti3`)
- Ship movement and navigation
- Combat processing
- System updates
- AI behavior

### Planet Processing (`plarti`)
- Production and manufacturing
- Tax collection
- Population growth
- Economic updates

### Automatic Processing (`autorti`)
- Cleanup tasks
- Maintenance routines
- Leaderboard updates
- Event processing

## Future Enhancements

1. **Real-time WebSocket Integration**
   - Live ship position updates
   - Instant combat notifications
   - Real-time planet changes

2. **Advanced AI**
   - Machine learning for AI behavior
   - Dynamic difficulty adjustment
   - Player behavior analysis

3. **Performance Optimization**
   - Task result caching
   - Database query optimization
   - Horizontal scaling

4. **Monitoring and Analytics**
   - Performance metrics
   - Game balance analysis
   - Player statistics

## Conclusion

The background task system provides a robust, scalable foundation for the Galactic Empire game's real-time processing needs. It maintains compatibility with the original game's logic while leveraging modern async processing capabilities.
