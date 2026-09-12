"""
Event publisher for Redis pubsub.
Publishes simulation deltas to Redis channels for WebSocket fan-out.
"""
import structlog
import json
import redis.asyncio as aioredis
import os
from typing import Optional

logger = structlog.get_logger()

class EventPublisher:
    """
    Publishes simulation events to Redis pubsub channels.
    WebSocket handlers subscribe to these channels and fan-out to connected clients.
    """
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
    
    async def connect(self):
        """Connect to Redis if not already connected."""
        if self.redis is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis = await aioredis.from_url(redis_url, decode_responses=True)
            logger.info("event_publisher_connected", redis_url=redis_url)
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("event_publisher_closed")
    
    async def publish_ship_moved(self, sector_x: int, sector_y: int, ship_data: dict):
        """
        Publish ship movement event.
        Channel: sector:{x}:{y}:ship_moved
        """
        channel = f"sector:{sector_x}:{sector_y}:ship_moved"
        message = json.dumps(ship_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, ship_id=ship_data.get("ship_id"))
    
    async def publish_combat_damage(self, sector_x: int, sector_y: int, combat_data: dict):
        """
        Publish combat damage event.
        Channel: sector:{x}:{y}:combat_damage
        """
        channel = f"sector:{sector_x}:{sector_y}:combat_damage"
        message = json.dumps(combat_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, attacker=combat_data.get("attacker_id"))
    
    async def publish_ship_destroyed(self, sector_x: int, sector_y: int, ship_data: dict):
        """
        Publish ship destroyed event.
        Channel: sector:{x}:{y}:ship_destroyed
        """
        channel = f"sector:{sector_x}:{sector_y}:ship_destroyed"
        message = json.dumps(ship_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, ship_id=ship_data.get("ship_id"))
    
    async def publish_planet_production_complete(self, planet_id: int, production_data: dict):
        """
        Publish planet production complete event.
        Channel: planet:{id}:production_ready
        """
        channel = f"planet:{planet_id}:production_ready"
        message = json.dumps(production_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, planet_id=planet_id)
    
    async def publish_planet_stockpile_full(self, planet_id: int, planet_data: dict):
        """
        Publish planet stockpile full event.
        Channel: planet:{id}:stockpile_full
        """
        channel = f"planet:{planet_id}:stockpile_full"
        message = json.dumps(planet_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, planet_id=planet_id)
    
    async def publish_spy_report(self, player_id: str, spy_data: dict):
        """
        Publish spy report event.
        Channel: player:{id}:spy_report
        """
        channel = f"player:{player_id}:spy_report"
        message = json.dumps(spy_data)
        await self.redis.publish(channel, message)
        logger.debug("event_publish", channel=channel, player_id=player_id)
    
    async def publish_sector_delta(self, sector_id: int, events: list):
        """
        Publish sector delta event with multiple sub-events.
        Channel: sector:{id}:delta
        
        This is the main channel for sector updates that combines
        multiple event types (ship moves, combat, etc.) in one message.
        """
        channel = f"sector:{sector_id}:delta"
        message = json.dumps({
            "type": "sector_delta",
            "sector_id": sector_id,
            "events": events
        })
        await self.redis.publish(channel, message)
        logger.debug("sector_delta_published", channel=channel, event_count=len(events))
