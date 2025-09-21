"""
Rate Limiting Service

This service provides API rate limiting and throttling functionality
to prevent abuse and ensure fair usage of the Galactic Empire game API.
"""

import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.role import APIKey


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10  # Burst allowance
    window_size: int = 60  # Window size in seconds


@dataclass
class RateLimitStatus:
    """Current rate limit status"""
    allowed: bool
    remaining_requests: int
    reset_time: datetime
    retry_after: Optional[int] = None


class RateLimitingService:
    """Service for API rate limiting and throttling"""
    
    def __init__(self):
        # In-memory storage for rate limit tracking
        # In production, this should use Redis or similar
        self.request_history: Dict[str, deque] = defaultdict(deque)
        self.user_limits: Dict[int, RateLimitRule] = {}
        self.ip_limits: Dict[str, RateLimitRule] = {}
        
        # Default rate limit rules
        self.default_rules = {
            'anonymous': RateLimitRule(
                name='anonymous',
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                burst_limit=5
            ),
            'authenticated': RateLimitRule(
                name='authenticated',
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000,
                burst_limit=20
            ),
            'api_key': RateLimitRule(
                name='api_key',
                requests_per_minute=120,
                requests_per_hour=5000,
                requests_per_day=50000,
                burst_limit=50
            ),
            'admin': RateLimitRule(
                name='admin',
                requests_per_minute=300,
                requests_per_hour=10000,
                requests_per_day=100000,
                burst_limit=100
            )
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/auth/login': RateLimitRule(
                name='login',
                requests_per_minute=5,
                requests_per_hour=20,
                requests_per_day=100,
                burst_limit=2
            ),
            '/api/auth/register': RateLimitRule(
                name='register',
                requests_per_minute=2,
                requests_per_hour=5,
                requests_per_day=10,
                burst_limit=1
            ),
            '/api/ships/attack': RateLimitRule(
                name='attack',
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=2000,
                burst_limit=10
            ),
            '/api/communication/send': RateLimitRule(
                name='send_message',
                requests_per_minute=20,
                requests_per_hour=200,
                requests_per_day=1000,
                burst_limit=5
            )
        }
    
    def _get_client_id(self, request: Request, user_id: Optional[int] = None, api_key: Optional[str] = None) -> str:
        """Generate unique client identifier for rate limiting"""
        if api_key:
            return f"api_key:{api_key[:8]}"
        elif user_id:
            return f"user:{user_id}"
        else:
            # Use IP address for anonymous requests
            client_ip = request.client.host
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                client_ip = forwarded_for.split(',')[0].strip()
            return f"ip:{client_ip}"
    
    def _get_rate_limit_rule(self, request: Request, user: Optional[User] = None, api_key: Optional[APIKey] = None) -> RateLimitRule:
        """Get applicable rate limit rule for the request"""
        endpoint = request.url.path
        
        # Check for endpoint-specific limits first
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Check for custom API key limits
        if api_key and api_key.rate_limit_per_minute:
            return RateLimitRule(
                name=f'api_key_{api_key.id}',
                requests_per_minute=api_key.rate_limit_per_minute,
                requests_per_hour=api_key.rate_limit_per_hour or api_key.rate_limit_per_minute * 60,
                requests_per_day=api_key.rate_limit_per_hour * 24 if api_key.rate_limit_per_hour else api_key.rate_limit_per_minute * 1440,
                burst_limit=max(10, api_key.rate_limit_per_minute // 4)
            )
        
        # Check user role-based limits
        if user:
            # Admin users get higher limits
            if any(role.name in ['admin', 'sysop'] for role in user.roles):
                return self.default_rules['admin']
            
            # Check for custom user limits
            if user.id in self.user_limits:
                return self.user_limits[user.id]
            
            return self.default_rules['authenticated']
        
        # API key limits
        if api_key:
            return self.default_rules['api_key']
        
        # Default anonymous limits
        return self.default_rules['anonymous']
    
    def _clean_old_requests(self, request_times: deque, window_seconds: int):
        """Remove old requests outside the time window"""
        current_time = time.time()
        while request_times and current_time - request_times[0] > window_seconds:
            request_times.popleft()
    
    def _count_requests_in_window(self, client_id: str, window_seconds: int) -> int:
        """Count requests in the specified time window"""
        request_times = self.request_history[client_id]
        self._clean_old_requests(request_times, window_seconds)
        return len(request_times)
    
    def check_rate_limit(self, request: Request, user: Optional[User] = None, api_key: Optional[APIKey] = None) -> RateLimitStatus:
        """Check if request is within rate limits"""
        client_id = self._get_client_id(request, user.id if user else None, api_key.key_prefix if api_key else None)
        rule = self._get_rate_limit_rule(request, user, api_key)
        
        current_time = time.time()
        
        # Count requests in different time windows
        requests_last_minute = self._count_requests_in_window(client_id, 60)
        requests_last_hour = self._count_requests_in_window(client_id, 3600)
        requests_last_day = self._count_requests_in_window(client_id, 86400)
        
        # Check burst limit (requests in last 10 seconds)
        requests_last_10_seconds = self._count_requests_in_window(client_id, 10)
        
        # Determine if request should be allowed
        allowed = True
        retry_after = None
        remaining = rule.requests_per_minute
        
        if requests_last_10_seconds >= rule.burst_limit:
            allowed = False
            retry_after = 10
            remaining = 0
        elif requests_last_minute >= rule.requests_per_minute:
            allowed = False
            retry_after = 60
            remaining = 0
        elif requests_last_hour >= rule.requests_per_hour:
            allowed = False
            retry_after = 3600
            remaining = 0
        elif requests_last_day >= rule.requests_per_day:
            allowed = False
            retry_after = 86400
            remaining = 0
        else:
            remaining = rule.requests_per_minute - requests_last_minute
        
        # Calculate reset time
        reset_time = datetime.now() + timedelta(seconds=retry_after or 60)
        
        return RateLimitStatus(
            allowed=allowed,
            remaining_requests=remaining,
            reset_time=reset_time,
            retry_after=retry_after
        )
    
    def record_request(self, request: Request, user: Optional[User] = None, api_key: Optional[APIKey] = None):
        """Record a request for rate limiting"""
        client_id = self._get_client_id(request, user.id if user else None, api_key.key_prefix if api_key else None)
        current_time = time.time()
        
        # Add current request time
        self.request_history[client_id].append(current_time)
        
        # Clean old requests to prevent memory bloat
        self._clean_old_requests(self.request_history[client_id], 86400)  # Keep 24 hours
    
    def apply_rate_limit(self, request: Request, user: Optional[User] = None, api_key: Optional[APIKey] = None) -> RateLimitStatus:
        """Apply rate limiting to a request"""
        status = self.check_rate_limit(request, user, api_key)
        
        if not status.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": status.retry_after,
                    "reset_time": status.reset_time.isoformat()
                },
                headers={
                    "Retry-After": str(status.retry_after) if status.retry_after else "60",
                    "X-RateLimit-Remaining": str(status.remaining_requests),
                    "X-RateLimit-Reset": str(int(status.reset_time.timestamp()))
                }
            )
        
        # Record the request
        self.record_request(request, user, api_key)
        return status
    
    def get_rate_limit_headers(self, status: RateLimitStatus) -> Dict[str, str]:
        """Get rate limit headers for response"""
        return {
            "X-RateLimit-Remaining": str(status.remaining_requests),
            "X-RateLimit-Reset": str(int(status.reset_time.timestamp())),
        }
    
    # Custom Rate Limit Management
    def set_user_rate_limit(self, user_id: int, rule: RateLimitRule):
        """Set custom rate limit for a specific user"""
        self.user_limits[user_id] = rule
    
    def remove_user_rate_limit(self, user_id: int):
        """Remove custom rate limit for a user"""
        if user_id in self.user_limits:
            del self.user_limits[user_id]
    
    def set_ip_rate_limit(self, ip_address: str, rule: RateLimitRule):
        """Set custom rate limit for a specific IP"""
        self.ip_limits[ip_address] = rule
    
    def remove_ip_rate_limit(self, ip_address: str):
        """Remove custom rate limit for an IP"""
        if ip_address in self.ip_limits:
            del self.ip_limits[ip_address]
    
    def clear_rate_limit_history(self, client_id: str = None):
        """Clear rate limit history for a client or all clients"""
        if client_id:
            if client_id in self.request_history:
                del self.request_history[client_id]
        else:
            self.request_history.clear()
    
    def get_client_status(self, client_id: str) -> Dict[str, any]:
        """Get current status for a client"""
        if client_id not in self.request_history:
            return {"requests": 0, "last_request": None}
        
        request_times = self.request_history[client_id]
        if not request_times:
            return {"requests": 0, "last_request": None}
        
        return {
            "requests_last_minute": self._count_requests_in_window(client_id, 60),
            "requests_last_hour": self._count_requests_in_window(client_id, 3600),
            "requests_last_day": self._count_requests_in_window(client_id, 86400),
            "total_requests": len(request_times),
            "last_request": datetime.fromtimestamp(request_times[-1]).isoformat()
        }
    
    def get_all_clients_status(self) -> Dict[str, Dict[str, any]]:
        """Get status for all tracked clients"""
        return {
            client_id: self.get_client_status(client_id)
            for client_id in self.request_history.keys()
        }


# Middleware function for FastAPI
async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    # Skip rate limiting for certain paths
    skip_paths = ['/docs', '/openapi.json', '/health', '/metrics']
    if request.url.path in skip_paths:
        return await call_next(request)
    
    # Apply rate limiting
    try:
        status = rate_limiting_service.apply_rate_limit(request)
        response = await call_next(request)
        
        # Add rate limit headers
        headers = rate_limiting_service.get_rate_limit_headers(status)
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
    except HTTPException:
        raise


# Global rate limiting service instance
rate_limiting_service = RateLimitingService()
