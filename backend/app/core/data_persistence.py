"""
Data Persistence Service for Galactic Empire

Handles database backup, restore, export/import, and data validation
operations for the game state.
"""

import json
import os
import shutil
import zipfile
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.core.database import engine, SessionLocal
from app.core.config import settings
from app.models.base import Base
from app.models import *

logger = logging.getLogger(__name__)


class DataPersistenceService:
    """Service for managing data persistence operations"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        
    def create_backup(self, backup_name: Optional[str] = None, include_data: bool = True) -> Dict[str, Any]:
        """
        Create a complete database backup
        
        Args:
            backup_name: Custom name for backup (optional)
            include_data: Whether to include actual data or just schema
            
        Returns:
            Dict with backup information
        """
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"ge_backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.sql"
            
            # Parse database URL to get connection details
            db_url = settings.database_url
            if db_url.startswith("postgresql://"):
                # Extract connection details
                parts = db_url.replace("postgresql://", "").split("/")
                db_name = parts[-1]
                auth_parts = parts[0].split("@")
                user_pass = auth_parts[0].split(":")
                username = user_pass[0]
                password = user_pass[1] if len(user_pass) > 1 else ""
                host_port = auth_parts[1].split(":")
                host = host_port[0]
                port = host_port[1] if len(host_port) > 1 else "5432"
                
                # Use pg_dump to create backup
                cmd = [
                    "pg_dump",
                    f"--host={host}",
                    f"--port={port}",
                    f"--username={username}",
                    f"--dbname={db_name}",
                    "--no-password",
                    "--verbose",
                    "--clean",
                    "--if-exists",
                    "--create"
                ]
                
                if include_data:
                    cmd.append("--data-only")
                else:
                    cmd.append("--schema-only")
                
                # Set password environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = password
                
                import subprocess
                with open(backup_path, 'w') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
                
                if result.returncode != 0:
                    raise Exception(f"pg_dump failed: {result.stderr.decode()}")
                
                # Get backup size
                backup_size = backup_path.stat().st_size
                
                # Create backup metadata
                metadata = {
                    "backup_name": backup_name,
                    "backup_path": str(backup_path),
                    "created_at": datetime.now().isoformat(),
                    "database_url": db_url,
                    "include_data": include_data,
                    "backup_size_bytes": backup_size,
                    "backup_size_mb": round(backup_size / (1024 * 1024), 2)
                }
                
                # Save metadata
                metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Backup created successfully: {backup_name}")
                return metadata
                
            else:
                raise Exception("Only PostgreSQL backups are currently supported")
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Restore database from backup
        
        Args:
            backup_name: Name of backup to restore
            confirm: Confirmation flag to prevent accidental restores
            
        Returns:
            Dict with restore information
        """
        if not confirm:
            raise Exception("Restore operation requires confirmation")
        
        try:
            backup_path = self.backup_dir / f"{backup_name}.sql"
            metadata_path = self.backup_dir / f"{backup_name}_metadata.json"
            
            if not backup_path.exists():
                raise Exception(f"Backup file not found: {backup_path}")
            
            # Load metadata
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Parse database URL
            db_url = settings.database_url
            parts = db_url.replace("postgresql://", "").split("/")
            db_name = parts[-1]
            auth_parts = parts[0].split("@")
            user_pass = auth_parts[0].split(":")
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
            host_port = auth_parts[1].split(":")
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            
            # Use psql to restore backup
            cmd = [
                "psql",
                f"--host={host}",
                f"--port={port}",
                f"--username={username}",
                f"--dbname={db_name}",
                "--no-password",
                "--quiet"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            
            import subprocess
            with open(backup_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env)
            
            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr.decode()}")
            
            restore_info = {
                "backup_name": backup_name,
                "restored_at": datetime.now().isoformat(),
                "database_url": db_url,
                "metadata": metadata
            }
            
            logger.info(f"Backup restored successfully: {backup_name}")
            return restore_info
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise
    
    def export_game_state(self, export_name: Optional[str] = None, 
                         include_users: bool = True,
                         include_ships: bool = True,
                         include_planets: bool = True,
                         include_teams: bool = True,
                         include_communications: bool = True) -> Dict[str, Any]:
        """
        Export game state to JSON format
        
        Args:
            export_name: Custom name for export
            include_users: Whether to include user data
            include_ships: Whether to include ship data
            include_planets: Whether to include planet data
            include_teams: Whether to include team data
            include_communications: Whether to include communications data
            
        Returns:
            Dict with export information
        """
        try:
            if not export_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_name = f"ge_export_{timestamp}"
            
            export_path = self.export_dir / f"{export_name}.json"
            
            db = SessionLocal()
            try:
                export_data = {
                    "export_info": {
                        "export_name": export_name,
                        "exported_at": datetime.now().isoformat(),
                        "game_version": "1.0.0",
                        "database_url": settings.database_url,
                        "includes": {
                            "users": include_users,
                            "ships": include_ships,
                            "planets": include_planets,
                            "teams": include_teams,
                            "communications": include_communications
                        }
                    },
                    "data": {}
                }
                
                # Export users
                if include_users:
                    users = db.query(User).all()
                    export_data["data"]["users"] = [
                        {
                            "id": user.id,
                            "userid": user.userid,
                            "email": user.email,
                            "score": user.score,
                            "kills": user.kills,
                            "planets": user.planets,
                            "cash": user.cash,
                            "debt": user.debt,
                            "teamcode": user.teamcode,
                            "created_at": user.created_at.isoformat() if user.created_at else None,
                            "last_login": user.last_login.isoformat() if user.last_login else None
                        }
                        for user in users
                    ]
                
                # Export ships
                if include_ships:
                    ships = db.query(Ship).all()
                    export_data["data"]["ships"] = [
                        {
                            "id": ship.id,
                            "shipno": ship.shipno,
                            "userid": ship.userid,
                            "shipname": ship.shipname,
                            "class_number": ship.class_number,
                            "x_coord": ship.x_coord,
                            "y_coord": ship.y_coord,
                            "xsect": ship.xsect,
                            "ysect": ship.ysect,
                            "energy": ship.energy,
                            "max_energy": ship.max_energy,
                            "shields": ship.shields,
                            "max_shields": ship.max_shields,
                            "cargo": ship.cargo,
                            "max_cargo": ship.max_cargo,
                            "created_at": ship.created_at.isoformat() if ship.created_at else None
                        }
                        for ship in ships
                    ]
                
                # Export planets
                if include_planets:
                    planets = db.query(Planet).all()
                    export_data["data"]["planets"] = [
                        {
                            "id": planet.id,
                            "planetno": planet.planetno,
                            "planetname": planet.planetname,
                            "xsect": planet.xsect,
                            "ysect": planet.ysect,
                            "x_coord": planet.x_coord,
                            "y_coord": planet.y_coord,
                            "owner": planet.owner,
                            "population": planet.population,
                            "max_population": planet.max_population,
                            "environment": planet.environment,
                            "created_at": planet.created_at.isoformat() if planet.created_at else None
                        }
                        for planet in planets
                    ]
                
                # Export teams
                if include_teams:
                    teams = db.query(Team).all()
                    export_data["data"]["teams"] = [
                        {
                            "id": team.id,
                            "teamname": team.teamname,
                            "teamcode": team.teamcode,
                            "teamcount": team.teamcount,
                            "teamscore": team.teamscore,
                            "created_at": team.created_at.isoformat() if team.created_at else None
                        }
                        for team in teams
                    ]
                
                # Export communications
                if include_communications:
                    mails = db.query(Mail).all()
                    export_data["data"]["communications"] = [
                        {
                            "id": mail.id,
                            "from_user": mail.from_user,
                            "to_user": mail.to_user,
                            "subject": mail.subject,
                            "message": mail.message,
                            "is_read": mail.is_read,
                            "created_at": mail.created_at.isoformat() if mail.created_at else None
                        }
                        for mail in mails
                    ]
                
                # Write export file
                with open(export_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                # Get export size
                export_size = export_path.stat().st_size
                
                export_info = {
                    "export_name": export_name,
                    "export_path": str(export_path),
                    "exported_at": datetime.now().isoformat(),
                    "export_size_bytes": export_size,
                    "export_size_mb": round(export_size / (1024 * 1024), 2),
                    "record_counts": {
                        "users": len(export_data["data"].get("users", [])),
                        "ships": len(export_data["data"].get("ships", [])),
                        "planets": len(export_data["data"].get("planets", [])),
                        "teams": len(export_data["data"].get("teams", [])),
                        "communications": len(export_data["data"].get("communications", []))
                    }
                }
                
                logger.info(f"Game state exported successfully: {export_name}")
                return export_info
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to export game state: {e}")
            raise
    
    def import_game_state(self, export_name: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Import game state from JSON export
        
        Args:
            export_name: Name of export to import
            confirm: Confirmation flag to prevent accidental imports
            
        Returns:
            Dict with import information
        """
        if not confirm:
            raise Exception("Import operation requires confirmation")
        
        try:
            export_path = self.export_dir / f"{export_name}.json"
            
            if not export_path.exists():
                raise Exception(f"Export file not found: {export_path}")
            
            # Load export data
            with open(export_path, 'r') as f:
                export_data = json.load(f)
            
            db = SessionLocal()
            try:
                import_info = {
                    "export_name": export_name,
                    "imported_at": datetime.now().isoformat(),
                    "imported_records": {},
                    "errors": []
                }
                
                # Import users
                if "users" in export_data["data"]:
                    user_count = 0
                    for user_data in export_data["data"]["users"]:
                        try:
                            # Check if user already exists
                            existing_user = db.query(User).filter(User.userid == user_data["userid"]).first()
                            if not existing_user:
                                user = User(
                                    userid=user_data["userid"],
                                    email=user_data["email"],
                                    score=user_data.get("score", 0),
                                    kills=user_data.get("kills", 0),
                                    planets=user_data.get("planets", 0),
                                    cash=user_data.get("cash", 0),
                                    debt=user_data.get("debt", 0),
                                    teamcode=user_data.get("teamcode", 0)
                                )
                                db.add(user)
                                user_count += 1
                        except Exception as e:
                            import_info["errors"].append(f"User {user_data.get('userid', 'unknown')}: {str(e)}")
                    
                    db.commit()
                    import_info["imported_records"]["users"] = user_count
                
                # Import ships
                if "ships" in export_data["data"]:
                    ship_count = 0
                    for ship_data in export_data["data"]["ships"]:
                        try:
                            # Check if ship already exists
                            existing_ship = db.query(Ship).filter(Ship.shipno == ship_data["shipno"]).first()
                            if not existing_ship:
                                ship = Ship(
                                    shipno=ship_data["shipno"],
                                    userid=ship_data["userid"],
                                    shipname=ship_data["shipname"],
                                    class_number=ship_data["class_number"],
                                    x_coord=ship_data["x_coord"],
                                    y_coord=ship_data["y_coord"],
                                    xsect=ship_data["xsect"],
                                    ysect=ship_data["ysect"],
                                    energy=ship_data.get("energy", 100),
                                    max_energy=ship_data.get("max_energy", 100),
                                    shields=ship_data.get("shields", 0),
                                    max_shields=ship_data.get("max_shields", 0),
                                    cargo=ship_data.get("cargo", 0),
                                    max_cargo=ship_data.get("max_cargo", 0)
                                )
                                db.add(ship)
                                ship_count += 1
                        except Exception as e:
                            import_info["errors"].append(f"Ship {ship_data.get('shipno', 'unknown')}: {str(e)}")
                    
                    db.commit()
                    import_info["imported_records"]["ships"] = ship_count
                
                # Import planets
                if "planets" in export_data["data"]:
                    planet_count = 0
                    for planet_data in export_data["data"]["planets"]:
                        try:
                            # Check if planet already exists
                            existing_planet = db.query(Planet).filter(Planet.planetno == planet_data["planetno"]).first()
                            if not existing_planet:
                                planet = Planet(
                                    planetno=planet_data["planetno"],
                                    planetname=planet_data["planetname"],
                                    xsect=planet_data["xsect"],
                                    ysect=planet_data["ysect"],
                                    x_coord=planet_data["x_coord"],
                                    y_coord=planet_data["y_coord"],
                                    owner=planet_data.get("owner", ""),
                                    population=planet_data.get("population", 0),
                                    max_population=planet_data.get("max_population", 1000),
                                    environment=planet_data.get("environment", 0)
                                )
                                db.add(planet)
                                planet_count += 1
                        except Exception as e:
                            import_info["errors"].append(f"Planet {planet_data.get('planetno', 'unknown')}: {str(e)}")
                    
                    db.commit()
                    import_info["imported_records"]["planets"] = planet_count
                
                # Import teams
                if "teams" in export_data["data"]:
                    team_count = 0
                    for team_data in export_data["data"]["teams"]:
                        try:
                            # Check if team already exists
                            existing_team = db.query(Team).filter(Team.teamcode == team_data["teamcode"]).first()
                            if not existing_team:
                                team = Team(
                                    teamname=team_data["teamname"],
                                    teamcode=team_data["teamcode"],
                                    teamcount=team_data.get("teamcount", 0),
                                    teamscore=team_data.get("teamscore", 0)
                                )
                                db.add(team)
                                team_count += 1
                        except Exception as e:
                            import_info["errors"].append(f"Team {team_data.get('teamname', 'unknown')}: {str(e)}")
                    
                    db.commit()
                    import_info["imported_records"]["teams"] = team_count
                
                # Import communications
                if "communications" in export_data["data"]:
                    comm_count = 0
                    for comm_data in export_data["data"]["communications"]:
                        try:
                            mail = Mail(
                                from_user=comm_data["from_user"],
                                to_user=comm_data["to_user"],
                                subject=comm_data["subject"],
                                message=comm_data["message"],
                                is_read=comm_data.get("is_read", False)
                            )
                            db.add(mail)
                            comm_count += 1
                        except Exception as e:
                            import_info["errors"].append(f"Communication {comm_data.get('id', 'unknown')}: {str(e)}")
                    
                    db.commit()
                    import_info["imported_records"]["communications"] = comm_count
                
                logger.info(f"Game state imported successfully: {export_name}")
                return import_info
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to import game state: {e}")
            raise
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate database integrity and consistency
        
        Returns:
            Dict with validation results
        """
        try:
            db = SessionLocal()
            try:
                validation_results = {
                    "validated_at": datetime.now().isoformat(),
                    "checks": [],
                    "errors": [],
                    "warnings": []
                }
                
                # Check foreign key constraints
                try:
                    # Check users with invalid team references
                    invalid_team_users = db.execute(text("""
                        SELECT u.id, u.userid, u.teamcode 
                        FROM users u 
                        LEFT JOIN teams t ON u.teamcode = t.teamcode 
                        WHERE u.teamcode > 0 AND t.teamcode IS NULL
                    """)).fetchall()
                    
                    if invalid_team_users:
                        validation_results["warnings"].append({
                            "check": "foreign_key_teams",
                            "message": f"Found {len(invalid_team_users)} users with invalid team references",
                            "details": [{"user_id": row[0], "userid": row[1], "teamcode": row[2]} for row in invalid_team_users]
                        })
                    else:
                        validation_results["checks"].append({
                            "check": "foreign_key_teams",
                            "status": "passed",
                            "message": "All user team references are valid"
                        })
                
                except Exception as e:
                    validation_results["errors"].append({
                        "check": "foreign_key_teams",
                        "error": str(e)
                    })
                
                # Check ship coordinates consistency
                try:
                    invalid_coordinates = db.execute(text("""
                        SELECT s.id, s.shipno, s.xsect, s.ysect, s.x_coord, s.y_coord
                        FROM ships s
                        WHERE (s.xsect < 0 OR s.xsect >= 30 OR s.ysect < 0 OR s.ysect >= 15)
                           OR (s.x_coord < 0 OR s.x_coord >= 100 OR s.y_coord < 0 OR s.y_coord >= 100)
                    """)).fetchall()
                    
                    if invalid_coordinates:
                        validation_results["errors"].append({
                            "check": "ship_coordinates",
                            "message": f"Found {len(invalid_coordinates)} ships with invalid coordinates",
                            "details": [{"ship_id": row[0], "shipno": row[1], "xsect": row[2], "ysect": row[3], "x_coord": row[4], "y_coord": row[5]} for row in invalid_coordinates]
                        })
                    else:
                        validation_results["checks"].append({
                            "check": "ship_coordinates",
                            "status": "passed",
                            "message": "All ship coordinates are valid"
                        })
                
                except Exception as e:
                    validation_results["errors"].append({
                        "check": "ship_coordinates",
                        "error": str(e)
                    })
                
                # Check planet coordinates consistency
                try:
                    invalid_planet_coords = db.execute(text("""
                        SELECT p.id, p.planetno, p.xsect, p.ysect, p.x_coord, p.y_coord
                        FROM planets p
                        WHERE (p.xsect < 0 OR p.xsect >= 30 OR p.ysect < 0 OR p.ysect >= 15)
                           OR (p.x_coord < 0 OR p.x_coord >= 100 OR p.y_coord < 0 OR p.y_coord >= 100)
                    """)).fetchall()
                    
                    if invalid_planet_coords:
                        validation_results["errors"].append({
                            "check": "planet_coordinates",
                            "message": f"Found {len(invalid_planet_coords)} planets with invalid coordinates",
                            "details": [{"planet_id": row[0], "planetno": row[1], "xsect": row[2], "ysect": row[3], "x_coord": row[4], "y_coord": row[5]} for row in invalid_planet_coords]
                        })
                    else:
                        validation_results["checks"].append({
                            "check": "planet_coordinates",
                            "status": "passed",
                            "message": "All planet coordinates are valid"
                        })
                
                except Exception as e:
                    validation_results["errors"].append({
                        "check": "planet_coordinates",
                        "error": str(e)
                    })
                
                # Check for orphaned records
                try:
                    orphaned_ships = db.execute(text("""
                        SELECT s.id, s.shipno, s.userid
                        FROM ships s
                        LEFT JOIN users u ON s.userid = u.userid
                        WHERE u.userid IS NULL
                    """)).fetchall()
                    
                    if orphaned_ships:
                        validation_results["warnings"].append({
                            "check": "orphaned_ships",
                            "message": f"Found {len(orphaned_ships)} ships with invalid user references",
                            "details": [{"ship_id": row[0], "shipno": row[1], "userid": row[2]} for row in orphaned_ships]
                        })
                    else:
                        validation_results["checks"].append({
                            "check": "orphaned_ships",
                            "status": "passed",
                            "message": "No orphaned ships found"
                        })
                
                except Exception as e:
                    validation_results["errors"].append({
                        "check": "orphaned_ships",
                        "error": str(e)
                    })
                
                # Summary
                validation_results["summary"] = {
                    "total_checks": len(validation_results["checks"]),
                    "passed_checks": len([c for c in validation_results["checks"] if c["status"] == "passed"]),
                    "total_errors": len(validation_results["errors"]),
                    "total_warnings": len(validation_results["warnings"]),
                    "overall_status": "healthy" if len(validation_results["errors"]) == 0 else "issues_found"
                }
                
                return validation_results
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            raise
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.sql"):
                backup_name = backup_file.stem
                metadata_file = self.backup_dir / f"{backup_name}_metadata.json"
                
                backup_info = {
                    "backup_name": backup_name,
                    "backup_path": str(backup_file),
                    "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    "backup_size_bytes": backup_file.stat().st_size,
                    "backup_size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2)
                }
                
                # Load metadata if available
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for {backup_name}: {e}")
                
                backups.append(backup_info)
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to get backup list: {e}")
            raise
    
    def get_export_list(self) -> List[Dict[str, Any]]:
        """Get list of available exports"""
        try:
            exports = []
            
            for export_file in self.export_dir.glob("*.json"):
                export_name = export_file.stem
                
                export_info = {
                    "export_name": export_name,
                    "export_path": str(export_file),
                    "created_at": datetime.fromtimestamp(export_file.stat().st_mtime).isoformat(),
                    "export_size_bytes": export_file.stat().st_size,
                    "export_size_mb": round(export_file.stat().st_size / (1024 * 1024), 2)
                }
                
                # Try to load export metadata
                try:
                    with open(export_file, 'r') as f:
                        export_data = json.load(f)
                    
                    if "export_info" in export_data:
                        export_info.update(export_data["export_info"])
                    
                    if "data" in export_data:
                        export_info["record_counts"] = {
                            "users": len(export_data["data"].get("users", [])),
                            "ships": len(export_data["data"].get("ships", [])),
                            "planets": len(export_data["data"].get("planets", [])),
                            "teams": len(export_data["data"].get("teams", [])),
                            "communications": len(export_data["data"].get("communications", []))
                        }
                
                except Exception as e:
                    logger.warning(f"Failed to load export metadata for {export_name}: {e}")
                
                exports.append(export_info)
            
            # Sort by creation time (newest first)
            exports.sort(key=lambda x: x["created_at"], reverse=True)
            
            return exports
            
        except Exception as e:
            logger.error(f"Failed to get export list: {e}")
            raise
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old backup files
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Dict with cleanup information
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_files = []
            total_size_freed = 0
            
            for backup_file in self.backup_dir.glob("*.sql"):
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    file_size = backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_files.append(str(backup_file))
                    total_size_freed += file_size
                    
                    # Also delete metadata file if it exists
                    metadata_file = self.backup_dir / f"{backup_file.stem}_metadata.json"
                    if metadata_file.exists():
                        metadata_file.unlink()
            
            cleanup_info = {
                "cleaned_at": datetime.now().isoformat(),
                "days_to_keep": days_to_keep,
                "deleted_files": deleted_files,
                "files_deleted": len(deleted_files),
                "size_freed_bytes": total_size_freed,
                "size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
            }
            
            logger.info(f"Backup cleanup completed: {len(deleted_files)} files deleted, {cleanup_info['size_freed_mb']} MB freed")
            return cleanup_info
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            raise


# Global service instance
data_persistence_service = DataPersistenceService()
