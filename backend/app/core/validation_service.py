"""
Input Validation Service

This service provides comprehensive input validation and sanitization
for all API endpoints to prevent injection attacks and ensure data integrity.
"""

import re
import html
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, validator, ValidationError
from fastapi import HTTPException, status


class ValidationService:
    """Service for input validation and sanitization"""
    
    def __init__(self):
        # Common regex patterns
        self.patterns = {
            'userid': re.compile(r'^[a-zA-Z0-9_-]{3,25}$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'password': re.compile(r'^.{8,128}$'),
            'ship_name': re.compile(r'^[a-zA-Z0-9\s\-_\']{1,50}$'),
            'planet_name': re.compile(r'^[a-zA-Z0-9\s\-_\']{1,50}$'),
            'team_name': re.compile(r'^[a-zA-Z0-9\s\-_\']{1,50}$'),
            'message': re.compile(r'^.{1,1000}$', re.DOTALL),
            'coordinate': re.compile(r'^-?\d+(\.\d+)?$'),
            'numeric_id': re.compile(r'^\d+$'),
            'hex_color': re.compile(r'^#[0-9A-Fa-f]{6}$'),
            'api_key': re.compile(r'^[a-zA-Z0-9]{32,128}$'),
        }
        
        # Dangerous characters/patterns to sanitize
        self.dangerous_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
            r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>',  # Iframes
            r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>',  # Objects
            r'<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>',  # Embeds
            r'<form\b[^<]*(?:(?!<\/form>)<[^<]*)*<\/form>',  # Forms
        ]
    
    # Basic Validation Functions
    def validate_userid(self, userid: str) -> str:
        """Validate user ID format"""
        if not userid or not isinstance(userid, str):
            raise ValidationError("User ID is required and must be a string")
        
        userid = userid.strip()
        if not self.patterns['userid'].match(userid):
            raise ValidationError("User ID must be 3-25 characters, alphanumeric, underscore, or dash only")
        
        return userid
    
    def validate_email(self, email: str) -> str:
        """Validate email format"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string")
        
        email = email.strip().lower()
        if not self.patterns['email'].match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    def validate_password(self, password: str) -> str:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required and must be a string")
        
        if not self.patterns['password'].match(password):
            raise ValidationError("Password must be 8-128 characters long")
        
        # Check for minimum complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValidationError("Password must contain at least one uppercase letter, one lowercase letter, and one digit")
        
        return password
    
    def validate_coordinates(self, x: Union[int, float], y: Union[int, float]) -> tuple:
        """Validate coordinate values"""
        try:
            x = float(x)
            y = float(y)
        except (ValueError, TypeError):
            raise ValidationError("Coordinates must be numeric")
        
        # Check reasonable bounds for game coordinates
        if not (-10000 <= x <= 10000) or not (-10000 <= y <= 10000):
            raise ValidationError("Coordinates must be within game bounds (-10000 to 10000)")
        
        return (x, y)
    
    def validate_numeric_range(self, value: Union[int, float], min_val: float = None, max_val: float = None, field_name: str = "Value") -> Union[int, float]:
        """Validate numeric value within range"""
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be numeric")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"{field_name} must be at most {max_val}")
        
        return value
    
    def validate_integer(self, value: Any, min_val: int = None, max_val: int = None, field_name: str = "Value") -> int:
        """Validate integer value within range"""
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_val is not None and value < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            raise ValidationError(f"{field_name} must be at most {max_val}")
        
        return value
    
    def validate_string_length(self, value: str, min_len: int = None, max_len: int = None, field_name: str = "Value") -> str:
        """Validate string length"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        length = len(value.strip())
        
        if min_len is not None and length < min_len:
            raise ValidationError(f"{field_name} must be at least {min_len} characters")
        
        if max_len is not None and length > max_len:
            raise ValidationError(f"{field_name} must be at most {max_len} characters")
        
        return value.strip()
    
    def validate_enum(self, value: Any, allowed_values: List[Any], field_name: str = "Value") -> Any:
        """Validate value is in allowed enum values"""
        if value not in allowed_values:
            raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, allowed_values))}")
        
        return value
    
    # Sanitization Functions
    def sanitize_html(self, text: str) -> str:
        """Sanitize HTML content"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove dangerous patterns
        for pattern in self.dangerous_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # HTML escape remaining content
        return html.escape(text)
    
    def sanitize_sql(self, text: str) -> str:
        """Sanitize potential SQL injection attempts"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove or escape SQL injection patterns
        dangerous_sql = [
            r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\s',
            r'UNION\s+SELECT',
            r'--\s',
            r'/\*.*?\*/',
            r'xp_cmdshell',
            r'sp_executesql',
        ]
        
        for pattern in dangerous_sql:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations"""
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    # Game-Specific Validation
    def validate_ship_data(self, ship_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ship data"""
        validated = {}
        
        if 'name' in ship_data:
            validated['name'] = self.validate_string_length(ship_data['name'], 1, 50, "Ship name")
            if not self.patterns['ship_name'].match(validated['name']):
                raise ValidationError("Ship name contains invalid characters")
        
        if 'ship_class' in ship_data:
            validated['ship_class'] = self.validate_integer(ship_data['ship_class'], 1, 12, "Ship class")
        
        if 'x' in ship_data and 'y' in ship_data:
            validated['x'], validated['y'] = self.validate_coordinates(ship_data['x'], ship_data['y'])
        
        if 'energy' in ship_data:
            validated['energy'] = self.validate_numeric_range(ship_data['energy'], 0, 100000, "Energy")
        
        if 'shields' in ship_data:
            validated['shields'] = self.validate_numeric_range(ship_data['shields'], 0, 100000, "Shields")
        
        return validated
    
    def validate_planet_data(self, planet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate planet data"""
        validated = {}
        
        if 'name' in planet_data:
            validated['name'] = self.validate_string_length(planet_data['name'], 1, 50, "Planet name")
            if not self.patterns['planet_name'].match(validated['name']):
                raise ValidationError("Planet name contains invalid characters")
        
        if 'x' in planet_data and 'y' in planet_data:
            validated['x'], validated['y'] = self.validate_coordinates(planet_data['x'], planet_data['y'])
        
        if 'population' in planet_data:
            validated['population'] = self.validate_integer(planet_data['population'], 0, 1000000000, "Population")
        
        if 'tax_rate' in planet_data:
            validated['tax_rate'] = self.validate_numeric_range(planet_data['tax_rate'], 0, 100, "Tax rate")
        
        return validated
    
    def validate_message_data(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate message data"""
        validated = {}
        
        if 'subject' in message_data:
            validated['subject'] = self.validate_string_length(message_data['subject'], 1, 100, "Subject")
            validated['subject'] = self.sanitize_html(validated['subject'])
        
        if 'body' in message_data:
            validated['body'] = self.validate_string_length(message_data['body'], 1, 5000, "Message body")
            validated['body'] = self.sanitize_html(validated['body'])
        
        if 'recipient_id' in message_data:
            validated['recipient_id'] = self.validate_integer(message_data['recipient_id'], 1, None, "Recipient ID")
        
        return validated
    
    # Batch Validation
    def validate_batch_operation(self, data: List[Dict[str, Any]], max_batch_size: int = 100) -> List[Dict[str, Any]]:
        """Validate batch operation data"""
        if not isinstance(data, list):
            raise ValidationError("Batch data must be a list")
        
        if len(data) > max_batch_size:
            raise ValidationError(f"Batch size cannot exceed {max_batch_size} items")
        
        if len(data) == 0:
            raise ValidationError("Batch data cannot be empty")
        
        return data
    
    # Rate Limiting Validation
    def validate_rate_limit_data(self, requests: int, time_window: int, max_requests: int) -> bool:
        """Validate rate limiting parameters"""
        if requests > max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {requests} requests in {time_window} seconds (max: {max_requests})"
            )
        return True
    
    # API Key Validation
    def validate_api_key_format(self, api_key: str) -> str:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key is required and must be a string")
        
        api_key = api_key.strip()
        if not self.patterns['api_key'].match(api_key):
            raise ValidationError("Invalid API key format")
        
        return api_key


# Validation Decorators
def validate_request_data(validation_func: Callable):
    """Decorator to validate request data using a validation function"""
    def decorator(endpoint_func):
        def wrapper(*args, **kwargs):
            # Extract request data from kwargs
            request_data = kwargs.get('request_data') or kwargs.get('data')
            if request_data:
                try:
                    validated_data = validation_func(request_data)
                    kwargs['validated_data'] = validated_data
                except ValidationError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Validation error: {str(e)}"
                    )
            return endpoint_func(*args, **kwargs)
        return wrapper
    return decorator


# Global validation service instance
validation_service = ValidationService()
