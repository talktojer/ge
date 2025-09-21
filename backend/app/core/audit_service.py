"""
Audit Logging Service

This service provides comprehensive audit logging for all user actions
and system events in the Galactic Empire game.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func
from fastapi import Request

from ..models.base import Base
from ..models.user import User


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DELETED = "account_deleted"
    
    # Game actions
    SHIP_CREATED = "ship_created"
    SHIP_MOVED = "ship_moved"
    SHIP_ATTACKED = "ship_attacked"
    SHIP_DESTROYED = "ship_destroyed"
    PLANET_COLONIZED = "planet_colonized"
    PLANET_ATTACKED = "planet_attacked"
    TEAM_JOINED = "team_joined"
    TEAM_LEFT = "team_left"
    
    # Communication
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELETED = "message_deleted"
    
    # Administrative actions
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    CONFIG_CHANGED = "config_changed"
    
    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    API_KEY_USED = "api_key_used"
    
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    DATABASE_ERROR = "database_error"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditContext:
    """Context information for audit events"""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    api_key_id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_id: Optional[str] = None


class AuditLog(Base):
    """Audit log entries"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), index=True)  # For actions on other users
    
    # Context information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(255))
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    
    # Request information
    endpoint = Column(String(255))
    http_method = Column(String(10))
    request_id = Column(String(100))
    
    # Additional data (JSON)
    metadata = Column(Text)  # JSON string
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_event_time', 'event_type', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
        Index('idx_audit_ip_time', 'ip_address', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', user_id={self.user_id}, timestamp={self.timestamp})>"


class AuditService:
    """Service for audit logging and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger("galactic_empire.audit")
        
        # Configure audit logger
        if not self.logger.handlers:
            handler = logging.FileHandler("audit.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_event(
        self,
        db: Session,
        event_type: AuditEventType,
        description: str,
        user_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        context: Optional[AuditContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log an audit event"""
        
        # Create audit log entry
        audit_entry = AuditLog(
            event_type=event_type.value,
            severity=severity.value,
            description=description,
            user_id=user_id,
            target_user_id=target_user_id,
            success=success,
            error_message=error_message
        )
        
        # Add context information
        if context:
            audit_entry.ip_address = context.ip_address
            audit_entry.user_agent = context.user_agent
            audit_entry.session_id = context.session_id
            audit_entry.api_key_id = context.api_key_id
            audit_entry.endpoint = context.endpoint
            audit_entry.http_method = context.method
            audit_entry.request_id = context.request_id
        
        # Add metadata
        if metadata:
            audit_entry.metadata = json.dumps(metadata, default=str)
        
        # Save to database
        try:
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to save audit log: {e}")
            # Continue with file logging even if DB fails
        
        # Also log to file
        log_message = f"[{event_type.value}] {description}"
        if user_id:
            log_message += f" (user_id: {user_id})"
        if context and context.ip_address:
            log_message += f" (ip: {context.ip_address})"
        
        if severity == AuditSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == AuditSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == AuditSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return audit_entry
    
    def log_from_request(
        self,
        db: Session,
        request: Request,
        event_type: AuditEventType,
        description: str,
        user_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log an audit event from a FastAPI request"""
        
        # Extract context from request
        context = AuditContext(
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent"),
            endpoint=str(request.url.path),
            method=request.method,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Check for forwarded IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            context.ip_address = forwarded_for.split(',')[0].strip()
        
        return self.log_event(
            db=db,
            event_type=event_type,
            description=description,
            user_id=user_id,
            target_user_id=target_user_id,
            severity=severity,
            context=context,
            metadata=metadata,
            success=success,
            error_message=error_message
        )
    
    # Convenience methods for common events
    def log_login(self, db: Session, request: Request, user_id: int, success: bool = True):
        """Log user login attempt"""
        event_type = AuditEventType.LOGIN if success else AuditEventType.LOGIN_FAILED
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        description = f"User login {'successful' if success else 'failed'}"
        
        return self.log_from_request(
            db=db,
            request=request,
            event_type=event_type,
            description=description,
            user_id=user_id,
            severity=severity,
            success=success
        )
    
    def log_logout(self, db: Session, request: Request, user_id: int):
        """Log user logout"""
        return self.log_from_request(
            db=db,
            request=request,
            event_type=AuditEventType.LOGOUT,
            description="User logout",
            user_id=user_id,
            severity=AuditSeverity.LOW
        )
    
    def log_ship_action(self, db: Session, request: Request, user_id: int, action: str, ship_id: int, metadata: Dict[str, Any] = None):
        """Log ship-related action"""
        event_type_map = {
            "created": AuditEventType.SHIP_CREATED,
            "moved": AuditEventType.SHIP_MOVED,
            "attacked": AuditEventType.SHIP_ATTACKED,
            "destroyed": AuditEventType.SHIP_DESTROYED
        }
        
        event_type = event_type_map.get(action, AuditEventType.SHIP_MOVED)
        description = f"Ship {action}: ship_id={ship_id}"
        
        audit_metadata = {"ship_id": ship_id, "action": action}
        if metadata:
            audit_metadata.update(metadata)
        
        return self.log_from_request(
            db=db,
            request=request,
            event_type=event_type,
            description=description,
            user_id=user_id,
            severity=AuditSeverity.LOW,
            metadata=audit_metadata
        )
    
    def log_admin_action(self, db: Session, request: Request, admin_user_id: int, action: str, target_user_id: int = None, metadata: Dict[str, Any] = None):
        """Log administrative action"""
        description = f"Admin action: {action}"
        if target_user_id:
            description += f" (target_user_id: {target_user_id})"
        
        return self.log_from_request(
            db=db,
            request=request,
            event_type=AuditEventType.CONFIG_CHANGED,
            description=description,
            user_id=admin_user_id,
            target_user_id=target_user_id,
            severity=AuditSeverity.HIGH,
            metadata=metadata
        )
    
    def log_security_event(self, db: Session, request: Request, event_type: AuditEventType, description: str, user_id: int = None, metadata: Dict[str, Any] = None):
        """Log security-related event"""
        return self.log_from_request(
            db=db,
            request=request,
            event_type=event_type,
            description=description,
            user_id=user_id,
            severity=AuditSeverity.HIGH,
            metadata=metadata
        )
    
    # Query methods
    def get_user_audit_logs(self, db: Session, user_id: int, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get audit logs for a specific user"""
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    def get_audit_logs_by_type(self, db: Session, event_type: AuditEventType, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get audit logs by event type"""
        return db.query(AuditLog).filter(
            AuditLog.event_type == event_type.value
        ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    def get_audit_logs_by_severity(self, db: Session, severity: AuditSeverity, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get audit logs by severity"""
        return db.query(AuditLog).filter(
            AuditLog.severity == severity.value
        ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    def get_recent_audit_logs(self, db: Session, hours: int = 24, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(AuditLog).filter(
            AuditLog.timestamp >= since
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    def get_failed_events(self, db: Session, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get failed events"""
        return db.query(AuditLog).filter(
            AuditLog.success == False
        ).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    def get_audit_statistics(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get audit statistics for the specified time period"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Total events
        total_events = db.query(AuditLog).filter(AuditLog.timestamp >= since).count()
        
        # Events by type
        events_by_type = db.query(
            AuditLog.event_type,
            func.count(AuditLog.id).label('count')
        ).filter(AuditLog.timestamp >= since).group_by(AuditLog.event_type).all()
        
        # Events by severity
        events_by_severity = db.query(
            AuditLog.severity,
            func.count(AuditLog.id).label('count')
        ).filter(AuditLog.timestamp >= since).group_by(AuditLog.severity).all()
        
        # Failed events
        failed_events = db.query(AuditLog).filter(
            AuditLog.timestamp >= since,
            AuditLog.success == False
        ).count()
        
        return {
            "total_events": total_events,
            "failed_events": failed_events,
            "success_rate": (total_events - failed_events) / total_events if total_events > 0 else 1.0,
            "events_by_type": {event_type: count for event_type, count in events_by_type},
            "events_by_severity": {severity: count for severity, count in events_by_severity},
            "time_period_hours": hours
        }


# Global audit service instance
audit_service = AuditService()
