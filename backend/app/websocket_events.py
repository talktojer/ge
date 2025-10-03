"""
WebSocket Event Broadcasting for Game State Updates
Integration with game systems to broadcast real-time updates
"""

from typing import Dict, Any, Optional
from .websocket_server import (
    broadcast_game_update,
    broadcast_ship_update,
    broadcast_planet_update,
    send_message_to_user,
    broadcast_combat_event
)

class GameEventBroadcaster:
    """Handles broadcasting game events via WebSocket"""
    
    @staticmethod
    async def ship_moved(ship_id: int, ship_data: Dict[str, Any]):
        """Broadcast ship movement update"""
        await broadcast_ship_update({
            'type': 'movement',
            'ship_id': ship_id,
            'position': ship_data.get('position'),
            'sector': ship_data.get('sector'),
            'speed': ship_data.get('speed'),
            'heading': ship_data.get('heading'),
            'timestamp': ship_data.get('timestamp')
        }, ship_id)
    
    @staticmethod
    async def ship_status_changed(ship_id: int, ship_data: Dict[str, Any]):
        """Broadcast ship status change"""
        await broadcast_ship_update({
            'type': 'status_change',
            'ship_id': ship_id,
            'shields': ship_data.get('shields'),
            'energy': ship_data.get('energy'),
            'damage': ship_data.get('damage'),
            'cloaked': ship_data.get('cloaked'),
            'timestamp': ship_data.get('timestamp')
        }, ship_id)
    
    @staticmethod
    async def combat_started(sector_id: int, combat_data: Dict[str, Any]):
        """Broadcast combat start event"""
        await broadcast_combat_event({
            'type': 'combat_started',
            'sector_id': sector_id,
            'participants': combat_data.get('participants'),
            'timestamp': combat_data.get('timestamp')
        }, sector_id)
    
    @staticmethod
    async def combat_damage(sector_id: int, damage_data: Dict[str, Any]):
        """Broadcast combat damage event"""
        await broadcast_combat_event({
            'type': 'damage_dealt',
            'sector_id': sector_id,
            'attacker': damage_data.get('attacker'),
            'target': damage_data.get('target'),
            'weapon': damage_data.get('weapon'),
            'damage': damage_data.get('damage'),
            'timestamp': damage_data.get('timestamp')
        }, sector_id)
    
    @staticmethod
    async def ship_destroyed(sector_id: int, ship_data: Dict[str, Any]):
        """Broadcast ship destruction event"""
        await broadcast_combat_event({
            'type': 'ship_destroyed',
            'sector_id': sector_id,
            'ship_id': ship_data.get('ship_id'),
            'owner': ship_data.get('owner'),
            'killer': ship_data.get('killer'),
            'timestamp': ship_data.get('timestamp')
        }, sector_id)
    
    @staticmethod
    async def planet_attacked(planet_data: Dict[str, Any]):
        """Broadcast planet attack event"""
        sector_id = planet_data.get('sector_id')
        await broadcast_planet_update({
            'type': 'under_attack',
            'planet_id': planet_data.get('planet_id'),
            'attacker': planet_data.get('attacker'),
            'defenses': planet_data.get('defenses'),
            'timestamp': planet_data.get('timestamp')
        }, sector_id)
    
    @staticmethod
    async def planet_conquered(planet_data: Dict[str, Any]):
        """Broadcast planet conquest event"""
        sector_id = planet_data.get('sector_id')
        await broadcast_planet_update({
            'type': 'conquered',
            'planet_id': planet_data.get('planet_id'),
            'new_owner': planet_data.get('new_owner'),
            'previous_owner': planet_data.get('previous_owner'),
            'timestamp': planet_data.get('timestamp')
        }, sector_id)
    
    @staticmethod
    async def message_sent(user_id: int, message_data: Dict[str, Any]):
        """Send message to specific user"""
        await send_message_to_user(user_id, {
            'type': 'message',
            'from': message_data.get('from'),
            'subject': message_data.get('subject'),
            'content': message_data.get('content'),
            'timestamp': message_data.get('timestamp')
        })
    
    @staticmethod
    async def team_message(team_id: int, message_data: Dict[str, Any]):
        """Broadcast message to team members"""
        # This would need team member lookup, simplified for now
        await broadcast_game_update({
            'type': 'team_message',
            'team_id': team_id,
            'from': message_data.get('from'),
            'content': message_data.get('content'),
            'timestamp': message_data.get('timestamp')
        }, room=f"team_{team_id}")
    
    @staticmethod
    async def game_tick_update(tick_data: Dict[str, Any]):
        """Broadcast game tick update to all players"""
        await broadcast_game_update({
            'type': 'tick_update',
            'tick_number': tick_data.get('tick_number'),
            'timestamp': tick_data.get('timestamp'),
            'active_players': tick_data.get('active_players'),
            'active_ships': tick_data.get('active_ships')
        })

# Global broadcaster instance
game_broadcaster = GameEventBroadcaster()
