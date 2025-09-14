"""
Galactic Empire - Movement Physics System

This module implements ship movement physics including speed, acceleration,
rotation, and movement calculations ported from the original C code.
"""

import math
from typing import Optional
from dataclasses import dataclass
from .coordinates import Coordinate, deg_to_rad, wrap_coordinate, clamp_to_galaxy


@dataclass
class MovementState:
    """Current movement state of a ship"""
    position: Coordinate
    heading: float  # 0-360 degrees
    speed: float
    target_speed: float
    acceleration: float
    deceleration: float
    max_speed: float
    max_acceleration: float


class MovementPhysics:
    """Handles ship movement physics calculations"""
    
    def __init__(self, max_speed: float = 50000.0, max_acceleration: float = 2000.0):
        self.max_speed = max_speed
        self.max_acceleration = max_acceleration
        # Movement scaling factor from original code (65000.0)
        self.movement_scale = 65000.0
    
    def calculate_movement(self, state: MovementState, wrap_enabled: bool = True) -> MovementState:
        """Calculate new position based on current movement state"""
        if state.speed <= 0:
            return state
        
        # Calculate movement delta using trigonometry
        # Original formula: coord += (speed * sin/cos(heading)) / 65000.0
        dx = (state.speed * math.sin(deg_to_rad(state.heading))) / self.movement_scale
        dy = (state.speed * math.cos(deg_to_rad(state.heading))) / self.movement_scale
        
        # Apply movement (note: Y is inverted in original coordinate system)
        new_x = state.position.x + dx
        new_y = state.position.y - dy  # Y is inverted
        
        new_position = Coordinate(new_x, new_y)
        
        # Handle galaxy boundaries
        if wrap_enabled:
            new_position = wrap_coordinate(new_position, wrap_enabled)
        else:
            new_position = clamp_to_galaxy(new_position)
        
        return MovementState(
            position=new_position,
            heading=state.heading,
            speed=state.speed,
            target_speed=state.target_speed,
            acceleration=state.acceleration,
            deceleration=state.deceleration,
            max_speed=state.max_speed,
            max_acceleration=state.max_acceleration
        )
    
    def accelerate(self, state: MovementState, target_speed: float) -> MovementState:
        """Apply acceleration to reach target speed"""
        if target_speed > state.max_speed:
            target_speed = state.max_speed
        if target_speed < 0:
            target_speed = 0
        
        state.target_speed = target_speed
        
        if abs(state.speed - target_speed) <= state.acceleration:
            # Close enough to target speed
            state.speed = target_speed
        else:
            # Apply acceleration or deceleration
            if state.speed < target_speed:
                state.speed += state.acceleration
            else:
                state.speed -= state.deceleration
        
        return state
    
    def rotate(self, state: MovementState, target_heading: float) -> MovementState:
        """Rotate ship to target heading"""
        # Normalize headings to 0-360 range
        current = state.heading % 360
        target = target_heading % 360
        
        # Calculate shortest rotation direction
        diff = target - current
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        # Apply rotation (assuming instant rotation for now)
        # In original code, rotation was also gradual
        state.heading = target % 360
        
        return state
    
    def set_heading(self, state: MovementState, heading: float) -> MovementState:
        """Set ship heading directly"""
        state.heading = heading % 360
        return state
    
    def set_speed(self, state: MovementState, speed: float) -> MovementState:
        """Set ship speed directly"""
        state.speed = max(0, min(speed, state.max_speed))
        state.target_speed = state.speed
        return state
    
    def stop(self, state: MovementState) -> MovementState:
        """Stop the ship"""
        state.speed = 0
        state.target_speed = 0
        return state
    
    def warp_speed(self, state: MovementState, warp_factor: int) -> MovementState:
        """Set warp speed (warp factor 1-10)"""
        if 1 <= warp_factor <= 10:
            # Warp speeds from original code
            warp_speeds = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
            target_speed = warp_speeds[warp_factor] * 1000  # Scale up
            return self.accelerate(state, target_speed)
        return state
    
    def impulse_speed(self, state: MovementState, impulse_power: int) -> MovementState:
        """Set impulse speed (1-100)"""
        if 1 <= impulse_power <= 100:
            target_speed = (impulse_power / 100.0) * 1000  # Scale to 0-1000
            return self.accelerate(state, target_speed)
        return state


class ShipMovement:
    """High-level ship movement controller"""
    
    def __init__(self, physics: MovementPhysics):
        self.physics = physics
    
    def move_ship(self, state: MovementState, wrap_enabled: bool = True) -> MovementState:
        """Main ship movement function - equivalent to moveship() in original"""
        # Apply acceleration to reach target speed
        state = self.physics.accelerate(state, state.target_speed)
        
        # Calculate new position
        new_state = self.physics.calculate_movement(state, wrap_enabled)
        
        return new_state
    
    def rotate_ship(self, state: MovementState, target_heading: float) -> MovementState:
        """Rotate ship to target heading"""
        return self.physics.rotate(state, target_heading)
    
    def accelerate_ship(self, state: MovementState, target_speed: float) -> MovementState:
        """Accelerate ship to target speed"""
        return self.physics.accelerate(state, target_speed)
    
    def set_warp(self, state: MovementState, warp_factor: int) -> MovementState:
        """Set warp speed"""
        return self.physics.warp_speed(state, warp_factor)
    
    def set_impulse(self, state: MovementState, impulse_power: int) -> MovementState:
        """Set impulse power"""
        return self.physics.impulse_speed(state, impulse_power)
    
    def stop_ship(self, state: MovementState) -> MovementState:
        """Stop the ship"""
        return self.physics.stop(state)


def create_movement_state(
    position: Coordinate,
    heading: float = 0.0,
    speed: float = 0.0,
    max_speed: float = 50000.0,
    max_acceleration: float = 2000.0
) -> MovementState:
    """Create a new movement state"""
    return MovementState(
        position=position,
        heading=heading,
        speed=speed,
        target_speed=speed,
        acceleration=max_acceleration,
        deceleration=max_acceleration,
        max_speed=max_speed,
        max_acceleration=max_acceleration
    )
