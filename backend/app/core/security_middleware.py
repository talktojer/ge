"""
Security Middleware

This middleware integrates all security services (RBAC, validation, rate limiting, 
audit logging, cheat prevention) into a unified security layer for the FastAPI application.
"""

import json
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.auth import auth_service
from ..core.rbac_service import rbac_service
from ..core.validation_service import validation_service, ValidationError
from ..core.rate_limiting_service import rate_limiting_service
from ..core.audit_service import audit_service, AuditEventType, AuditSeverity
from ..core.cheat_prevention_service import cheat_prevention_service
from ..models.user import User
from ..models.role import APIKey


# Security scheme for JWT tokens
security_scheme = HTTPBearer()


class SecurityContext:
    """Security context for request processing"""
    
    def __init__(self):
        self.user: Optional[User] = None
        self.api_key: Optional[APIKey] = None
        self.permissions: set = set()
        self.is_authenticated: bool = False
        self.is_admin: bool = False
        self.request_id: str = ""
        self.start_time: float = time.time()


class SecurityMiddleware:
    """Main security middleware class"""
    
    def __init__(self):
        self.exempt_paths = {
            '/docs',
            '/openapi.json',
            '/health',
            '/metrics',
            '/api/auth/login',
            '/api/auth/register',
            '/api/auth/refresh'
        }
        
        self.admin_paths = {
            '/api/admin',
            '/api/config',
            '/api/system'
        }
    
    async def __call__(self, request: Request, call_next: Callable, db: Session):
        """Main middleware processing"""
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}-{id(request)}"
        request.state.request_id = request_id
        
        # Skip security for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Create security context
        security_context = SecurityContext()
        security_context.request_id = request_id
        request.state.security = security_context
        
        try:
            # 1. Authentication
            await self._authenticate_request(request, security_context, db)
            
            # 2. Rate Limiting
            await self._apply_rate_limiting(request, security_context)
            
            # 3. Authorization
            await self._authorize_request(request, security_context, db)
            
            # 4. Input Validation (for POST/PUT requests)
            if request.method in ['POST', 'PUT', 'PATCH']:
                await self._validate_request_input(request, security_context)
            
            # 5. Cheat Prevention (for game actions)
            if request.url.path.startswith('/api/ships') or request.url.path.startswith('/api/planets'):
                await self._check_cheat_prevention(request, security_context, db)
            
            # Process request
            response = await call_next(request)
            
            # 6. Audit Logging
            await self._log_request(request, response, security_context, db)
            
            return response
            
        except HTTPException as e:
            # Log security violation
            await self._log_security_violation(request, security_context, db, str(e.detail))
            raise
        except Exception as e:
            # Log unexpected error
            await self._log_security_violation(request, security_context, db, f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal security error"
            )
    
    async def _authenticate_request(self, request: Request, context: SecurityContext, db: Session):
        """Authenticate the request"""
        # Check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            context.api_key = await self._validate_api_key(db, api_key)
            if context.api_key:
                context.user = context.api_key.user
                context.is_authenticated = True
                return
        
        # Check for JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            payload = auth_service.verify_token(token)
            if payload:
                user_id = payload.get('sub')
                if user_id:
                    context.user = db.query(User).filter(User.id == int(user_id)).first()
                    if context.user and context.user.is_active:
                        context.is_authenticated = True
                        context.permissions = rbac_service.get_user_permissions(db, context.user.id)
                        context.is_admin = any(role.name in ['admin', 'sysop'] for role in context.user.roles)
                        return
        
        # Check if authentication is required for this path
        if request.url.path.startswith('/api/') and request.url.path not in self.exempt_paths:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def _validate_api_key(self, db: Session, api_key: str) -> Optional[APIKey]:
        """Validate API key"""
        try:
            # Hash the provided key
            key_hash = validation_service.sanitize_sql(api_key)  # Basic sanitization
            
            # Find matching API key
            db_api_key = db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if db_api_key:
                # Check expiration
                if db_api_key.expires_at and db_api_key.expires_at < datetime.utcnow():
                    return None
                
                # Update last used timestamp
                db_api_key.last_used_at = datetime.utcnow()
                db.commit()
                
                return db_api_key
            
        except Exception:
            pass
        
        return None
    
    async def _apply_rate_limiting(self, request: Request, context: SecurityContext):
        """Apply rate limiting"""
        try:
            rate_limiting_service.apply_rate_limit(request, context.user, context.api_key)
        except HTTPException as e:
            # Log rate limit violation
            if context.user:
                audit_service.log_from_request(
                    db=get_db().__next__(),  # Get DB session
                    request=request,
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    description=f"Rate limit exceeded for user {context.user.userid}",
                    user_id=context.user.id,
                    severity=AuditSeverity.MEDIUM
                )
            raise
    
    async def _authorize_request(self, request: Request, context: SecurityContext, db: Session):
        """Authorize the request based on RBAC"""
        # Skip authorization for public endpoints
        if request.url.path in self.exempt_paths:
            return
        
        # Check admin access for admin paths
        if any(request.url.path.startswith(path) for path in self.admin_paths):
            if not context.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            return
        
        # Check resource-based permissions
        resource, action = self._extract_resource_action(request)
        if resource and action:
            if context.user:
                has_permission = rbac_service.user_has_permission(db, context.user.id, resource, action)
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {resource}:{action}"
                    )
    
    def _extract_resource_action(self, request: Request) -> tuple:
        """Extract resource and action from request path and method"""
        path = request.url.path
        method = request.method.lower()
        
        # Map HTTP methods to actions
        method_action_map = {
            'get': 'read',
            'post': 'write',
            'put': 'write',
            'patch': 'write',
            'delete': 'delete'
        }
        
        action = method_action_map.get(method, 'read')
        
        # Extract resource from path
        if '/api/ships' in path:
            return 'ship', action
        elif '/api/planets' in path:
            return 'planet', action
        elif '/api/teams' in path:
            return 'team', action
        elif '/api/users' in path:
            return 'user', action
        elif '/api/communication' in path:
            return 'communication', action
        elif '/api/game' in path:
            return 'game', action
        elif '/api/system' in path:
            return 'system', action
        
        return None, None
    
    async def _validate_request_input(self, request: Request, context: SecurityContext):
        """Validate request input data"""
        try:
            # Get request body
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    # Basic validation - more specific validation should be done in endpoints
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, str):
                                # Sanitize strings
                                data[key] = validation_service.sanitize_html(value)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON in request body"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input validation failed: {str(e)}"
            )
    
    async def _check_cheat_prevention(self, request: Request, context: SecurityContext, db: Session):
        """Check for potential cheating"""
        if not context.user:
            return
        
        try:
            # Extract action and data from request
            action = self._extract_game_action(request)
            if action:
                # Get request data
                body = await request.body()
                data = {}
                if body:
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        pass
                
                # Validate action for cheating
                result = cheat_prevention_service.validate_user_action(
                    db, context.user.id, action, data
                )
                
                if result.is_suspicious and result.confidence_score > 0.8:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Suspicious activity detected"
                    )
        except HTTPException:
            raise
        except Exception:
            # Don't fail request on cheat detection errors
            pass
    
    def _extract_game_action(self, request: Request) -> Optional[str]:
        """Extract game action from request"""
        path = request.url.path
        method = request.method.lower()
        
        if method == 'post':
            if '/move' in path:
                return 'move_ship'
            elif '/attack' in path:
                return 'attack_ship'
            elif '/colonize' in path:
                return 'colonize_planet'
        elif method == 'put':
            if '/ships/' in path:
                return 'update_ship'
            elif '/planets/' in path:
                return 'update_planet'
        
        return None
    
    async def _log_request(self, request: Request, response: Response, context: SecurityContext, db: Session):
        """Log the request for audit purposes"""
        # Only log significant events, not every GET request
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            event_type = AuditEventType.SYSTEM_START  # Default
            description = f"{request.method} {request.url.path}"
            
            # Determine event type based on path
            if '/api/auth/' in request.url.path:
                if 'login' in request.url.path:
                    event_type = AuditEventType.LOGIN if response.status_code < 400 else AuditEventType.LOGIN_FAILED
                elif 'logout' in request.url.path:
                    event_type = AuditEventType.LOGOUT
            elif '/api/ships/' in request.url.path:
                event_type = AuditEventType.SHIP_MOVED
            elif '/api/planets/' in request.url.path:
                event_type = AuditEventType.PLANET_COLONIZED
            
            # Calculate processing time
            processing_time = time.time() - context.start_time
            
            audit_service.log_from_request(
                db=db,
                request=request,
                event_type=event_type,
                description=description,
                user_id=context.user.id if context.user else None,
                severity=AuditSeverity.LOW,
                metadata={
                    'processing_time': processing_time,
                    'status_code': response.status_code,
                    'request_id': context.request_id
                },
                success=response.status_code < 400
            )
    
    async def _log_security_violation(self, request: Request, context: SecurityContext, db: Session, error_detail: str):
        """Log security violations"""
        audit_service.log_from_request(
            db=db,
            request=request,
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            description=f"Security violation: {error_detail}",
            user_id=context.user.id if context.user else None,
            severity=AuditSeverity.HIGH,
            metadata={
                'error_detail': error_detail,
                'request_id': context.request_id
            },
            success=False,
            error_message=error_detail
        )


# Dependency functions for FastAPI
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = auth_service.verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify admin privileges"""
    if not any(role.name in ['admin', 'sysop'] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not rbac_service.user_has_permission(db, current_user.id, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {resource}:{action}"
            )
        return current_user
    
    return Depends(permission_checker)


# Global security middleware instance
security_middleware = SecurityMiddleware()
