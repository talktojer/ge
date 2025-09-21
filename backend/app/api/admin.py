"""
Galactic Empire - Admin Configuration API

Administrative endpoints for game configuration, balance management,
and system monitoring.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.game_config import game_config, ConfigCategory, ConfigParameter
from app.core.balance_service import balance_service, BalanceMetrics, BalanceFactor
from app.core.scoring_service import scoring_service, ScoreBreakdown, PlayerRanking, TeamRanking
from app.core.data_persistence import data_persistence_service
from app.models.config import GameConfig, ConfigHistory, ConfigVersion, BalanceAdjustment
from app.models.user import User
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


# Pydantic models for API
class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any
    reason: Optional[str] = None


class ConfigBatchUpdateRequest(BaseModel):
    updates: List[ConfigUpdateRequest]
    reason: Optional[str] = None


class ConfigVersionRequest(BaseModel):
    version_name: str
    description: Optional[str] = None


class BalanceAnalysisRequest(BaseModel):
    factors: Optional[List[str]] = None
    include_recommendations: bool = True


class ScoreCalculationRequest(BaseModel):
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    recalculate: bool = False


class AdminStatsResponse(BaseModel):
    total_players: int
    active_players: int
    total_teams: int
    game_uptime: str
    configuration_count: int
    pending_balance_adjustments: int
    system_health: str


class BackupRequest(BaseModel):
    backup_name: Optional[str] = None
    include_data: bool = True


class RestoreRequest(BaseModel):
    backup_name: str
    confirm: bool = False


class ExportRequest(BaseModel):
    export_name: Optional[str] = None
    include_users: bool = True
    include_ships: bool = True
    include_planets: bool = True
    include_teams: bool = True
    include_communications: bool = True


class ImportRequest(BaseModel):
    export_name: str
    confirm: bool = False


class CleanupRequest(BaseModel):
    days_to_keep: int = 30


# Authentication dependency for admin users
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user has admin privileges"""
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get administrative dashboard statistics"""
    try:
        # Get basic statistics
        total_players = db.query(User).count()
        
        # Active players (logged in within last 24 hours)
        active_threshold = datetime.utcnow() - timedelta(hours=24)
        active_players = db.query(User).filter(User.last_login > active_threshold).count()
        
        # Configuration statistics
        config_count = len(game_config.get_all_configs())
        
        # Pending balance adjustments
        pending_adjustments = db.query(BalanceAdjustment).filter(
            BalanceAdjustment.status == "pending"
        ).count()
        
        # System health (simplified)
        system_health = "healthy"  # Would implement actual health checks
        
        return AdminStatsResponse(
            total_players=total_players,
            active_players=active_players,
            total_teams=0,  # Would query teams table
            game_uptime="24h 15m",  # Would calculate actual uptime
            configuration_count=config_count,
            pending_balance_adjustments=pending_adjustments,
            system_health=system_health
        )
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin statistics")


@router.get("/config")
async def get_all_configurations(
    category: Optional[str] = None,
    admin_user: User = Depends(get_admin_user)
):
    """Get all game configurations, optionally filtered by category"""
    try:
        if category:
            try:
                category_enum = ConfigCategory(category)
                configs = game_config.get_config_by_category(category_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        else:
            configs = game_config.get_all_configs()
        
        # Convert to API format
        result = {}
        for key, config in configs.items():
            result[key] = {
                "value": config.value,
                "type": config.config_type.value,
                "category": config.category.value,
                "description": config.description,
                "min_value": config.min_value,
                "max_value": config.max_value,
                "default_value": config.default_value,
                "requires_restart": config.requires_restart
            }
        
        return result
    except Exception as e:
        logger.error(f"Error getting configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configurations")


@router.get("/config/{key}")
async def get_configuration(
    key: str,
    admin_user: User = Depends(get_admin_user)
):
    """Get specific configuration value"""
    try:
        value = game_config.get_config(key)
        return {"key": key, "value": value}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting configuration {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")


@router.put("/config/{key}")
async def update_configuration(
    key: str,
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Update a single configuration value"""
    try:
        # Validate configuration exists
        if key not in game_config.get_all_configs():
            raise HTTPException(status_code=404, detail=f"Configuration '{key}' not found")
        
        # Update configuration
        success = game_config.set_config(
            key=key,
            value=request.value,
            admin_user=admin_user.username
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Configuration validation failed")
        
        # Log to database
        config_record = db.query(GameConfig).filter(GameConfig.key == key).first()
        if config_record:
            history_record = ConfigHistory(
                config_id=config_record.id,
                old_value=config_record.value,
                new_value=request.value,
                changed_by=admin_user.username,
                change_reason=request.reason
            )
            db.add(history_record)
            db.commit()
        
        return {"message": f"Configuration '{key}' updated successfully", "value": request.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating configuration {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.put("/config/batch")
async def update_configurations_batch(
    request: ConfigBatchUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Update multiple configuration values in a single operation"""
    try:
        results = []
        errors = []
        
        for update in request.updates:
            try:
                success = game_config.set_config(
                    key=update.key,
                    value=update.value,
                    admin_user=admin_user.username
                )
                
                if success:
                    results.append({"key": update.key, "value": update.value, "status": "success"})
                else:
                    errors.append({"key": update.key, "error": "Validation failed"})
            except ValueError as e:
                errors.append({"key": update.key, "error": str(e)})
        
        return {
            "message": f"Batch update completed: {len(results)} successful, {len(errors)} failed",
            "results": results,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error in batch configuration update: {e}")
        raise HTTPException(status_code=500, detail="Failed to update configurations")


@router.post("/config/reset/{key}")
async def reset_configuration(
    key: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Reset configuration to default value"""
    try:
        success = game_config.reset_to_default(key, admin_user.username)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Configuration '{key}' not found or has no default")
        
        return {"message": f"Configuration '{key}' reset to default value"}
    except Exception as e:
        logger.error(f"Error resetting configuration {key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset configuration")


@router.get("/config/history")
async def get_configuration_history(
    key: Optional[str] = None,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user)
):
    """Get configuration change history"""
    try:
        history = game_config.get_config_history(limit)
        
        if key:
            # Filter by specific key
            history = [h for h in history if h.get("key") == key]
        
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting configuration history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration history")


@router.post("/config/export")
async def export_configurations(
    admin_user: User = Depends(get_admin_user)
):
    """Export all configurations as JSON"""
    try:
        config_data = game_config.export_config()
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": admin_user.username,
            "configurations": config_data
        }
    except Exception as e:
        logger.error(f"Error exporting configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to export configurations")


@router.post("/config/import")
async def import_configurations(
    config_data: Dict[str, Any],
    admin_user: User = Depends(get_admin_user)
):
    """Import configurations from JSON"""
    try:
        errors = game_config.import_config(config_data, admin_user.username)
        
        return {
            "message": "Configuration import completed",
            "errors": errors,
            "imported_by": admin_user.username
        }
    except Exception as e:
        logger.error(f"Error importing configurations: {e}")
        raise HTTPException(status_code=500, detail="Failed to import configurations")


@router.post("/config/version")
async def create_config_version(
    request: ConfigVersionRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Create a configuration version snapshot"""
    try:
        # Export current configuration
        config_snapshot = game_config.export_config()
        
        # Create version record
        version = ConfigVersion(
            version_name=request.version_name,
            description=request.description,
            config_snapshot=config_snapshot,
            created_by=admin_user.username
        )
        
        db.add(version)
        db.commit()
        
        return {"message": f"Configuration version '{request.version_name}' created successfully"}
    except Exception as e:
        logger.error(f"Error creating config version: {e}")
        raise HTTPException(status_code=500, detail="Failed to create configuration version")


@router.get("/balance/analysis")
async def get_balance_analysis(
    request: BalanceAnalysisRequest = Depends(),
    admin_user: User = Depends(get_admin_user)
):
    """Get game balance analysis and recommendations"""
    try:
        metrics = balance_service.analyze_game_balance()
        
        # Filter by requested factors if specified
        if request.factors:
            metrics = [m for m in metrics if m.factor.value in request.factors]
        
        # Convert to API format
        result = []
        for metric in metrics:
            result.append({
                "factor": metric.factor.value,
                "current_value": metric.current_value,
                "target_value": metric.target_value,
                "deviation_percent": metric.deviation_percent,
                "recommendation": metric.recommendation,
                "impact_level": metric.impact_level
            })
        
        return {"analysis": result, "generated_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error getting balance analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze game balance")


@router.get("/balance/ship/{ship_class}")
async def get_ship_balance_analysis(
    ship_class: str,
    admin_user: User = Depends(get_admin_user)
):
    """Get balance analysis for a specific ship class"""
    try:
        balance = balance_service.get_ship_class_balance(ship_class)
        
        return {
            "ship_class": balance.ship_class,
            "energy_efficiency": balance.energy_efficiency,
            "combat_effectiveness": balance.combat_effectiveness,
            "economic_value": balance.economic_value,
            "strategic_value": balance.strategic_value,
            "balance_score": balance.balance_score,
            "recommendations": balance.recommendations
        }
    except Exception as e:
        logger.error(f"Error getting ship balance for {ship_class}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze ship balance")


@router.get("/balance/history")
async def get_balance_history(
    limit: int = 100,
    admin_user: User = Depends(get_admin_user)
):
    """Get balance adjustment history"""
    try:
        history = balance_service.get_balance_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting balance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve balance history")


@router.get("/scoring/rankings/players")
async def get_player_rankings(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get player rankings"""
    try:
        rankings = scoring_service.get_player_rankings(db, limit)
        
        # Convert to API format
        result = []
        for ranking in rankings:
            result.append({
                "user_id": ranking.user_id,
                "username": ranking.username,
                "rank": ranking.rank,
                "total_score": ranking.score,
                "score_breakdown": {
                    "kill_score": ranking.score_breakdown.kill_score,
                    "planet_score": ranking.score_breakdown.planet_score,
                    "team_score": ranking.score_breakdown.team_score,
                    "net_worth": ranking.score_breakdown.net_worth,
                    "combat_rating": ranking.score_breakdown.combat_rating,
                    "economic_rating": ranking.score_breakdown.economic_rating,
                    "strategic_rating": ranking.score_breakdown.strategic_rating,
                    "overall_rating": ranking.score_breakdown.overall_rating
                },
                "team_name": ranking.team_name,
                "last_active": ranking.last_active.isoformat() if ranking.last_active else None,
                "achievements": ranking.achievements
            })
        
        return {"rankings": result}
    except Exception as e:
        logger.error(f"Error getting player rankings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve player rankings")


@router.get("/scoring/rankings/teams")
async def get_team_rankings(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get team rankings"""
    try:
        rankings = scoring_service.get_team_rankings(db, limit)
        
        # Convert to API format
        result = []
        for ranking in rankings:
            result.append({
                "team_id": ranking.team_id,
                "team_name": ranking.team_name,
                "rank": ranking.rank,
                "total_score": ranking.total_score,
                "member_count": ranking.member_count,
                "average_score": ranking.average_score,
                "coordination_bonus": ranking.coordination_bonus,
                "last_active": ranking.last_active.isoformat() if ranking.last_active else None
            })
        
        return {"rankings": result}
    except Exception as e:
        logger.error(f"Error getting team rankings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team rankings")


@router.get("/scoring/player/{user_id}")
async def get_player_score_breakdown(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get detailed score breakdown for a specific player"""
    try:
        breakdown = scoring_service.get_player_score_breakdown(user_id, db)
        
        return {
            "user_id": user_id,
            "score_breakdown": {
                "kill_score": breakdown.kill_score,
                "planet_score": breakdown.planet_score,
                "team_score": breakdown.team_score,
                "net_worth": breakdown.net_worth,
                "combat_rating": breakdown.combat_rating,
                "economic_rating": breakdown.economic_rating,
                "strategic_rating": breakdown.strategic_rating,
                "overall_rating": breakdown.overall_rating,
                "total_score": breakdown.get_total_score()
            }
        }
    except Exception as e:
        logger.error(f"Error getting player score breakdown for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve player score breakdown")


@router.post("/scoring/recalculate")
async def recalculate_scores(
    request: ScoreCalculationRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Force recalculation of scores"""
    try:
        if request.user_id:
            # Recalculate specific player
            scoring_service.clear_cache()
            breakdown = scoring_service.get_player_score_breakdown(request.user_id, db)
            return {"message": f"Scores recalculated for user {request.user_id}"}
        elif request.team_id:
            # Recalculate specific team
            scoring_service.clear_cache()
            return {"message": f"Team scores recalculated for team {request.team_id}"}
        else:
            # Recalculate all scores
            scoring_service.clear_cache()
            return {"message": "All scores recalculated"}
    except Exception as e:
        logger.error(f"Error recalculating scores: {e}")
        raise HTTPException(status_code=500, detail="Failed to recalculate scores")


@router.get("/scoring/achievements/{user_id}")
async def get_player_achievements(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get achievements for a specific player"""
    try:
        achievements = scoring_service.check_achievements(user_id, db)
        
        result = []
        for achievement in achievements:
            result.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "type": achievement.achievement_type.value,
                "reward_score": achievement.reward_score,
                "icon": achievement.icon,
                "rarity": achievement.rarity
            })
        
        return {"user_id": user_id, "achievements": result}
    except Exception as e:
        logger.error(f"Error getting achievements for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve player achievements")


@router.post("/system/clear-cache")
async def clear_system_cache(
    admin_user: User = Depends(get_admin_user)
):
    """Clear system caches"""
    try:
        # Clear scoring service cache
        scoring_service.clear_cache()
        
        # Clear other caches as needed
        # game_config.clear_cache()  # If implemented
        
        return {"message": "System caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing system cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear system caches")


# =============================================================================
# DATA PERSISTENCE ENDPOINTS
# =============================================================================

@router.get("/data/backups")
async def get_backup_list(
    admin_user: User = Depends(get_admin_user)
):
    """Get list of available database backups"""
    try:
        backups = data_persistence_service.get_backup_list()
        return {"backups": backups}
    except Exception as e:
        logger.error(f"Error getting backup list: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve backup list")


@router.post("/data/backup")
async def create_backup(
    request: BackupRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Create a new database backup"""
    try:
        backup_info = data_persistence_service.create_backup(
            backup_name=request.backup_name,
            include_data=request.include_data
        )
        
        return {
            "message": "Backup created successfully",
            "backup_info": backup_info
        }
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@router.post("/data/restore")
async def restore_backup(
    request: RestoreRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Restore database from backup"""
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="Restore operation requires confirmation. Set 'confirm' to true."
            )
        
        restore_info = data_persistence_service.restore_backup(
            backup_name=request.backup_name,
            confirm=request.confirm
        )
        
        return {
            "message": "Backup restored successfully",
            "restore_info": restore_info
        }
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")


@router.get("/data/exports")
async def get_export_list(
    admin_user: User = Depends(get_admin_user)
):
    """Get list of available game state exports"""
    try:
        exports = data_persistence_service.get_export_list()
        return {"exports": exports}
    except Exception as e:
        logger.error(f"Error getting export list: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export list")


@router.post("/data/export")
async def export_game_state(
    request: ExportRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Export game state to JSON format"""
    try:
        export_info = data_persistence_service.export_game_state(
            export_name=request.export_name,
            include_users=request.include_users,
            include_ships=request.include_ships,
            include_planets=request.include_planets,
            include_teams=request.include_teams,
            include_communications=request.include_communications
        )
        
        return {
            "message": "Game state exported successfully",
            "export_info": export_info
        }
    except Exception as e:
        logger.error(f"Error exporting game state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export game state: {str(e)}")


@router.post("/data/import")
async def import_game_state(
    request: ImportRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Import game state from JSON export"""
    try:
        if not request.confirm:
            raise HTTPException(
                status_code=400, 
                detail="Import operation requires confirmation. Set 'confirm' to true."
            )
        
        import_info = data_persistence_service.import_game_state(
            export_name=request.export_name,
            confirm=request.confirm
        )
        
        return {
            "message": "Game state imported successfully",
            "import_info": import_info
        }
    except Exception as e:
        logger.error(f"Error importing game state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import game state: {str(e)}")


@router.get("/data/validate")
async def validate_data_integrity(
    admin_user: User = Depends(get_admin_user)
):
    """Validate database integrity and consistency"""
    try:
        validation_results = data_persistence_service.validate_data_integrity()
        return validation_results
    except Exception as e:
        logger.error(f"Error validating data integrity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate data integrity: {str(e)}")


@router.post("/data/cleanup")
async def cleanup_old_backups(
    request: CleanupRequest,
    admin_user: User = Depends(get_admin_user)
):
    """Clean up old backup files"""
    try:
        cleanup_info = data_persistence_service.cleanup_old_backups(
            days_to_keep=request.days_to_keep
        )
        
        return {
            "message": "Backup cleanup completed successfully",
            "cleanup_info": cleanup_info
        }
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {str(e)}")
