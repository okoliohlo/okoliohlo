"""
Product API Response Schemas
"""

PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "price": {"type": "number"},
        "category": {"type": "string"},
        "stock": {"type": "integer"},
        "image_url": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    },
    "required": ["id", "name", "price"]
}

PRODUCT_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "products": {
            "type": "array",
            "items": PRODUCT_SCHEMA
        },
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"}
    },
    "required": ["products", "total", "page", "limit"]
}