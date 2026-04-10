"""
User API Response Schemas
For JSON schema validation
"""

USER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    },
    "required": ["id", "username", "email"]
}

USER_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "users": {
            "type": "array",
            "items": USER_SCHEMA
        },
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"}
    },
    "required": ["users", "total", "page", "limit"]
}

AUTH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "token": {"type": "string"},
        "refresh_token": {"type": "string"},
        "expires_in": {"type": "integer"},
        "user": USER_SCHEMA
    },
    "required": ["token", "user"]
}