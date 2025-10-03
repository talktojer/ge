"""
Galactic Empire - Planetary API endpoints

This module provides API endpoints for planetary management including
colonization, resource management, trading, and planet information.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.planetary_service import PlanetaryService
from ..models.planet import Planet
from ..models.user import User

router = APIRouter()


# Pydantic models for requests
class ColonizationRequest(BaseModel):
    population_to_send: int


class TaxRateRequest(BaseModel):
    tax_rate: int


class BeaconMessageRequest(BaseModel):
    message: str


class ProductionRequest(BaseModel):
    item_type_id: int
    production_rate: int


class TradingRequest(BaseModel):
    item_type_id: int
    action: str  # "buy" or "sell"
    quantity: int


# Planet Information Endpoints

@router.get("/planets", response_model=List[Dict[str, Any]])
async def get_planets(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all planets with pagination"""
    try:
        offset = (page - 1) * per_page
        planets = db.query(Planet).offset(offset).limit(per_page).all()
        
        results = []
        for planet in planets:
            results.append({
                "id": planet.id,
                "name": planet.name,
                "sector": (planet.xsect, planet.ysect),
                "position": (planet.x_coord, planet.y_coord),
                "environment": planet.environment,
                "resource": planet.resource,
                "owner_id": planet.owner_id,
                "cash": planet.cash,
                "debt": planet.debt,
                "population": planet.population,
                "tax_rate": planet.tax_rate,
                "beacon_text": planet.beacon_text
            })
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving planets: {str(e)}"
        )


@router.get("/planets/{planet_id}/status", response_model=Dict[str, Any])
async def get_planet_status(
    planet_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive planet status"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.get_planet_status(planet_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Planet not found")
        )
    
    return result


@router.get("/planets/search", response_model=List[Dict[str, Any]])
async def search_planets(
    query: str = Query(..., description="Search query for planet name or owner"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Search planets by name or owner"""
    planetary_service = PlanetaryService(db)
    results = planetary_service.search_planets(query, limit)
    return results


@router.get("/planets/uncolonized", response_model=List[Dict[str, Any]])
async def get_uncolonized_planets(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Get uncolonized planets available for colonization"""
    planetary_service = PlanetaryService(db)
    planets = planetary_service.get_uncolonized_planets(limit)
    
    results = []
    for planet in planets:
        results.append({
            "id": planet.id,
            "name": planet.name,
            "sector": (planet.xsect, planet.ysect),
            "position": (planet.x_coord, planet.y_coord),
            "environment": planet.environment,
            "resource": planet.resource,
            "beacon_message": planet.beacon_message
        })
    
    return results


@router.get("/planets/near", response_model=List[Dict[str, Any]])
async def get_planets_near_position(
    x: float = Query(..., description="X coordinate"),
    y: float = Query(..., description="Y coordinate"),
    max_distance: float = Query(100000.0, ge=1000.0, le=1000000.0, description="Maximum distance"),
    db: Session = Depends(get_db)
):
    """Get planets near a specific position"""
    planetary_service = PlanetaryService(db)
    nearby_planets = planetary_service.get_planets_near_position(x, y, max_distance)
    
    results = []
    for planet, distance in nearby_planets:
        results.append({
            "id": planet.id,
            "name": planet.name,
            "owner": planet.userid,
            "sector": (planet.xsect, planet.ysect),
            "position": (planet.x_coord, planet.y_coord),
            "distance": distance,
            "environment": planet.environment,
            "resource": planet.resource,
            "is_colonized": planet.owner_id is not None
        })
    
    return results


@router.get("/sectors/{xsect}/{ysect}", response_model=Dict[str, Any])
async def get_sector_info(
    xsect: int,
    ysect: int,
    db: Session = Depends(get_db)
):
    """Get information about a sector"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.get_sector_info(xsect, ysect)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Sector not found")
        )
    
    return result


# Planet Management Endpoints

@router.get("/planets/owned", response_model=List[Dict[str, Any]])
async def get_user_planets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all planets owned by the current user"""
    planetary_service = PlanetaryService(db)
    planets = planetary_service.get_user_planets(current_user.id)
    
    results = []
    for planet in planets:
        results.append({
            "id": planet.id,
            "name": planet.name,
            "sector": (planet.xsect, planet.ysect),
            "position": (planet.x_coord, planet.y_coord),
            "environment": planet.environment,
            "resource": planet.resource,
            "cash": planet.cash,
            "debt": planet.debt,
            "tax_rate": planet.tax_rate,
            "tax_collected": planet.tax,
            "technology": planet.technology,
            "beacon_message": planet.beacon_message,
            "last_attack": planet.last_attack
        })
    
    return results


@router.post("/planets/{planet_id}/colonize", response_model=Dict[str, Any])
async def colonize_planet(
    planet_id: int,
    colonization_request: ColonizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Colonize a planet"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.colonize_planet(
        planet_id, current_user.id, colonization_request.population_to_send
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Colonization failed")
        )
    
    return result


@router.put("/planets/{planet_id}/tax-rate", response_model=Dict[str, Any])
async def set_tax_rate(
    planet_id: int,
    tax_request: TaxRateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set planet tax rate"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.set_tax_rate(planet_id, current_user.id, tax_request.tax_rate)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to set tax rate")
        )
    
    return result


@router.put("/planets/{planet_id}/beacon", response_model=Dict[str, Any])
async def set_beacon_message(
    planet_id: int,
    beacon_request: BeaconMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set planet beacon message"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.set_beacon_message(planet_id, current_user.id, beacon_request.message)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to set beacon message")
        )
    
    return result


# Production and Economy Endpoints

@router.put("/planets/{planet_id}/production", response_model=Dict[str, Any])
async def set_item_production(
    planet_id: int,
    production_request: ProductionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set item production rate for a planet"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.set_item_production(
        planet_id, current_user.id, 
        production_request.item_type_id, production_request.production_rate
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to set production rate")
        )
    
    return result


@router.post("/planets/{planet_id}/trade", response_model=Dict[str, Any])
async def trade_items(
    planet_id: int,
    trading_request: TradingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trade items with a planet"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.trade_items(
        planet_id, current_user.id,
        trading_request.item_type_id, trading_request.action, trading_request.quantity
    )
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Trading failed")
        )
    
    return result


@router.get("/planets/{planet_id}/items", response_model=List[Dict[str, Any]])
async def get_planet_items(
    planet_id: int,
    db: Session = Depends(get_db)
):
    """Get all items available on a planet"""
    planetary_service = PlanetaryService(db)
    planet_items = planetary_service.get_planet_items(planet_id)
    
    results = []
    for planet_item in planet_items:
        # Get item type information
        item_type = db.query(planetary_service.db.query(planetary_service.ItemType).filter(
            planetary_service.ItemType.id == planet_item.item_id
        ).first())
        
        if item_type:
            results.append({
                "item_id": planet_item.item_id,
                "item_name": item_type.name,
                "item_keyword": item_type.keyword,
                "quantity": planet_item.quantity,
                "production_rate": planet_item.rate,
                "sell_to_allies": planet_item.sell_to_allies,
                "reserve": planet_item.reserve,
                "markup_to_allies": planet_item.markup_to_allies,
                "sold_to_allies": planet_item.sold_to_allies
            })
    
    return results


@router.get("/planets/{planet_id}/prices/{item_type_id}", response_model=Dict[str, Any])
async def get_item_prices(
    planet_id: int,
    item_type_id: int,
    db: Session = Depends(get_db)
):
    """Get current buy/sell prices for an item on a planet"""
    planetary_service = PlanetaryService(db)
    
    planet = planetary_service.get_planet_by_id(planet_id)
    if not planet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planet not found"
        )
    
    # Get item type
    from ..models.item import ItemType
    item_type = db.query(ItemType).filter(ItemType.id == item_type_id).first()
    if not item_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item type not found"
        )
    
    # Get planet item for quantity
    planet_item = planetary_service.get_planet_item(planet_id, item_type_id)
    quantity = planet_item.quantity if planet_item else 0
    
    # Calculate prices
    prices = planetary_service.planet_management.economy.calculate_item_prices(
        planet, item_type_id, item_type.base_price, quantity
    )
    
    return {
        "item_id": item_type_id,
        "item_name": item_type.name,
        "quantity_available": quantity,
        "buy_price": prices["buy_price"],
        "sell_price": prices["sell_price"],
        "base_price": prices["base_price"],
        "supply_factor": prices["supply_factor"],
        "environment_modifier": prices["environment_modifier"]
    }


# Administrative Endpoints

@router.post("/planets/{planet_id}/tick", response_model=Dict[str, Any])
async def process_planet_tick(
    planet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process planet systems for one tick (admin/debug endpoint)"""
    planetary_service = PlanetaryService(db)
    result = planetary_service.process_planet_tick(planet_id)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Tick processing failed")
        )
    
    return result


@router.get("/planets/{planet_id}/defense", response_model=Dict[str, Any])
async def get_planet_defense_info(
    planet_id: int,
    db: Session = Depends(get_db)
):
    """Get planet defense information"""
    planetary_service = PlanetaryService(db)
    
    planet = planetary_service.get_planet_by_id(planet_id)
    if not planet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planet not found"
        )
    
    # Calculate defense strength (placeholder population)
    population = 10000 if planet.owner_id else 0
    troops = 0  # TODO: Implement troop tracking
    fighters = 0  # TODO: Implement fighter tracking
    
    defense_strength = planetary_service.planet_management.defense.calculate_defense_strength(
        planet, population, troops, fighters
    )
    
    return {
        "planet_id": planet_id,
        "defense_strength": defense_strength,
        "population": population,
        "troops": troops,
        "fighters": fighters,
        "technology_level": planet.technology,
        "environment": planet.environment,
        "last_attack": planet.last_attack
    }
