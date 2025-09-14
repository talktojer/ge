"""
Galactic Empire - Coordinate System and Mathematical Functions

This module implements the core coordinate system and mathematical functions
for the Galactic Empire game engine, ported from the original C code.
"""

import math
from typing import Tuple, NamedTuple
from dataclasses import dataclass


class Coordinate(NamedTuple):
    """Coordinate structure with x,y coordinates"""
    x: float
    y: float


@dataclass
class Sector:
    """Sector coordinates in the galaxy grid"""
    x: int
    y: int


# Galaxy constants from original code
SSMAX = 10000  # Sector size maximum (10000x10000 parsecs per sector)
UNIVMAX = 300  # Galaxy radius (300 sectors in each direction from center)
PI = math.pi


def deg_to_rad(degrees: float) -> float:
    """Convert degrees to radians"""
    return degrees * (PI / 180)


def rad_to_deg(radians: float) -> float:
    """Convert radians to degrees"""
    return radians * (180 / PI)


def absolute(value: float) -> float:
    """Double absolute function"""
    return abs(value)


def normal(angle: float) -> float:
    """Bring an angle back into the range 0 - 360"""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def smallest_angle(a1: float, a2: float) -> float:
    """Determine the smallest of two complementary angles"""
    diff = abs(a1 - a2)
    if diff > 180:
        return 360 - diff
    return diff


def distance(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the distance between two coordinates"""
    dx = coord1.x - coord2.x
    dy = coord1.y - coord2.y
    return math.sqrt(dx * dx + dy * dy)


def vector(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the angle from one coordinate to another"""
    if coord1.x >= coord2.x and coord1.y <= coord2.y:
        angle = angle_b(coord1, coord2)
        return 270.0 - angle
    elif coord1.x >= coord2.x and coord1.y >= coord2.y:
        angle = angle_b(coord1, coord2)
        return 270.0 + angle
    elif coord1.x <= coord2.x and coord1.y <= coord2.y:
        angle = angle_c(coord1, coord2)
        return 180.0 - angle
    elif coord1.x <= coord2.x and coord1.y >= coord2.y:
        angle = angle_c(coord1, coord2)
        return 0.0 + angle
    else:
        return 99999.0


def angle_b(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the angle from the center to the other coordinate"""
    dist = distance(coord1, coord2)
    dx = absolute(coord1.x - coord2.x)
    dy = absolute(coord1.y - coord2.y)
    
    if dist * dx > 0:
        angle = math.acos(((dist * dist) + (dx * dx) - (dy * dy)) / (2 * dist * dx))
    else:
        angle = 0
    
    return rad_to_deg(angle)


def angle_c(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the angle from the center to the other coordinate"""
    dist = distance(coord1, coord2)
    dx = absolute(coord1.x - coord2.x)
    dy = absolute(coord1.y - coord2.y)
    
    if dist * dy > 0:
        angle = math.acos(((dist * dist) + (dy * dy) - (dx * dx)) / (2 * dist * dy))
    else:
        angle = 0
    
    return rad_to_deg(angle)


def bearing(coord1: Coordinate, coord2: Coordinate, heading: float) -> float:
    """Calculate ship bearing between two objects"""
    # Add small offset to avoid division by zero
    coord1_offset = Coordinate(coord1.x + 0.000001, coord1.y + 0.000001)
    
    vec = vector(coord1_offset, coord2)
    bearing_angle = normal(360 - heading + vec)
    
    if bearing_angle > 180:
        bearing_angle -= 360
    
    return bearing_angle


def coord1(dcoord: float) -> int:
    """Convert coordinate to sector number (integer part)"""
    return int(math.floor(dcoord))


def coord2(dcoord: float) -> int:
    """Convert coordinate to position within sector (0-SSMAX)"""
    # Extract fractional part and scale to SSMAX
    fractional_part = dcoord - math.floor(dcoord)
    return int(fractional_part * SSMAX)


def get_sector(coord: Coordinate) -> Sector:
    """Get sector coordinates from a coordinate"""
    return Sector(
        x=coord1(coord.x),
        y=coord1(coord.y)
    )


def same_sector(coord1: Coordinate, coord2: Coordinate) -> bool:
    """Check if two coordinates are in the same sector"""
    sector1 = get_sector(coord1)
    sector2 = get_sector(coord2)
    return sector1.x == sector2.x and sector1.y == sector2.y


def move_coord(source: Coordinate, dest: Coordinate) -> Coordinate:
    """Move one coordinate to another (copy operation)"""
    return Coordinate(dest.x, dest.y)


def is_in_galaxy(coord: Coordinate) -> bool:
    """Check if coordinate is within galaxy bounds"""
    return (-UNIVMAX <= coord.x <= UNIVMAX and 
            -UNIVMAX <= coord.y <= UNIVMAX)


def wrap_coordinate(coord: Coordinate, wrap_enabled: bool = True) -> Coordinate:
    """Wrap coordinate around galaxy edges if wrap is enabled"""
    if not wrap_enabled:
        return coord
    
    x, y = coord.x, coord.y
    
    # Wrap X coordinate
    if x > UNIVMAX:
        x -= UNIVMAX * 2
    elif x < -UNIVMAX:
        x += UNIVMAX * 2
    
    # Wrap Y coordinate  
    if y > UNIVMAX:
        y -= UNIVMAX * 2
    elif y < -UNIVMAX:
        y += UNIVMAX * 2
    
    return Coordinate(x, y)


def clamp_to_galaxy(coord: Coordinate) -> Coordinate:
    """Clamp coordinate to galaxy bounds (no wrapping)"""
    x = max(-UNIVMAX + 2, min(UNIVMAX - 2, coord.x))
    y = max(-UNIVMAX + 2, min(UNIVMAX - 2, coord.y))
    return Coordinate(x, y)
