# Backend Development Rules - FastAPI/MongoDB Standards

## 🏗️ **Service Layer Architecture**

### **Professional Service Structure**
```python
"""
Enhanced service for domain-specific operations.
Follows single responsibility principle and dependency injection patterns.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.logger import logger
from app.db.client import database
from app.core.error_handling import handle_database_error
from app.schemas.domain.entity import EntityCreate, EntityUpdate, EntityResponse


class EntityService:
    """Professional service for entity management."""
    
    def __init__(self):
        self.collection_name = "entities"
    
    async def _get_db(self):
        """Get database instance."""
        return await database.get_database()
    
    async def create_entity(self, entity_data: EntityCreate, created_by: ObjectId) -> Dict[str, Any]:
        """Create a new entity with proper validation and error handling."""
        db = await self._get_db()
        
        try:
            # Validate input data
            if not entity_data.name.strip():
                raise ValueError("Entity name cannot be empty")
            
            # Check for duplicates
            existing = await db[self.collection_name].find_one({"name": entity_data.name})
            if existing:
                raise ValueError("Entity with this name already exists")
            
            # Prepare document
            now = datetime.utcnow()
            entity_doc = {
                "name": entity_data.name.strip(),
                "description": entity_data.description,
                "status": "active",
                "created_at": now,
                "updated_at": now,
                "created_by": created_by,
                "updated_by": created_by,
            }
            
            # Insert document
            result = await db[self.collection_name].insert_one(entity_doc)
            entity_doc["_id"] = result.inserted_id
            
            logger.info(f"✅ Created entity: {entity_data.name} (ID: {result.inserted_id})")
            return entity_doc
            
        except Exception as e:
            logger.error(f"❌ Error creating entity: {str(e)}")
            raise handle_database_error(e, "create_entity", "entity")
    
    async def get_entity(self, entity_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get entity by ID with proper error handling."""
        db = await self._get_db()
        
        try:
            entity = await db[self.collection_name].find_one({"_id": entity_id})
            return entity
            
        except Exception as e:
            logger.error(f"❌ Error getting entity: {str(e)}")
            raise handle_database_error(e, "get_entity", "entity")
    
    async def list_entities(
        self, 
        skip: int = 0, 
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List entities with pagination and filtering."""
        db = await self._get_db()
        
        try:
            # Build filter
            filter_query = {}
            if status:
                filter_query["status"] = status
            
            # Execute query with pagination
            cursor = (db[self.collection_name]
                     .find(filter_query)
                     .sort([("created_at", DESCENDING)])
                     .skip(skip)
                     .limit(limit))
            
            entities = await cursor.to_list(length=limit)
            return entities
            
        except Exception as e:
            logger.error(f"❌ Error listing entities: {str(e)}")
            raise handle_database_error(e, "list_entities", "entity")
    
    async def update_entity(
        self, 
        entity_id: ObjectId, 
        update_data: EntityUpdate, 
        updated_by: ObjectId
    ) -> Optional[Dict[str, Any]]:
        """Update entity with validation and audit trail."""
        db = await self._get_db()
        
        try:
            # Prepare update
            update_fields = {}
            if update_data.name is not None:
                update_fields["name"] = update_data.name.strip()
            if update_data.description is not None:
                update_fields["description"] = update_data.description
            if update_data.status is not None:
                update_fields["status"] = update_data.status
            
            if not update_fields:
                return await self.get_entity(entity_id)
            
            update_fields["updated_at"] = datetime.utcnow()
            update_fields["updated_by"] = updated_by
            
            # Execute update
            result = await db[self.collection_name].update_one(
                {"_id": entity_id},
                {"$set": update_fields}
            )
            
            if result.modified_count == 0:
                return None
            
            logger.info(f"✅ Updated entity: {entity_id}")
            return await self.get_entity(entity_id)
            
        except Exception as e:
            logger.error(f"❌ Error updating entity: {str(e)}")
            raise handle_database_error(e, "update_entity", "entity")
    
    async def delete_entity(self, entity_id: ObjectId) -> bool:
        """Soft delete entity (set status to inactive)."""
        db = await self._get_db()
        
        try:
            result = await db[self.collection_name].update_one(
                {"_id": entity_id},
                {
                    "$set": {
                        "status": "inactive",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"✅ Deleted entity: {entity_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting entity: {str(e)}")
            raise handle_database_error(e, "delete_entity", "entity")


# Global service instance
entity_service = EntityService()
```

## 🗄️ **Database Schema & Indexes**

### **Professional Collection Indexes**
```python
async def _create_entity_indexes(self) -> None:
    """Create indexes for entities collection with proper naming."""
    collection = self.db.entities
    
    indexes = [
        # Primary lookup indexes
        IndexModel([("name", ASCENDING)], name="idx_entities_name"),
        IndexModel([("status", ASCENDING)], name="idx_entities_status"),
        
        # Compound indexes for common queries
        IndexModel([
            ("status", ASCENDING), 
            ("created_at", DESCENDING)
        ], name="idx_entities_status_created"),
        
        # Text search index
        IndexModel([
            ("name", TEXT), 
            ("description", TEXT)
        ], name="idx_entities_search"),
        
        # Audit indexes
        IndexModel([("created_by", ASCENDING)], name="idx_entities_created_by"),
        IndexModel([("updated_by", ASCENDING)], name="idx_entities_updated_by"),
        IndexModel([("created_at", DESCENDING)], name="idx_entities_created_at"),
        IndexModel([("updated_at", DESCENDING)], name="idx_entities_updated_at"),
    ]
    
    await collection.create_indexes(indexes)
    logger.info("Created indexes for entities collection")
```

### **Professional Document Schema**
```python
class Entity(BaseModel):
    """Professional entity model with proper validation."""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100, description="Entity name")
    description: Optional[str] = Field(None, max_length=500, description="Entity description")
    status: str = Field(default="active", description="Entity status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PyObjectId] = Field(None, description="Creator user ID")
    updated_by: Optional[PyObjectId] = Field(None, description="Updater user ID")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
```

## 🛣️ **API Route Patterns**

### **Professional Route Structure**
```python
"""
Professional API route following project patterns.
Includes proper validation, error handling, and audit logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.domain.entity import EntityCreate, EntityUpdate, EntityResponse, EntityListResponse
from app.services.auth import require_permissions
from app.services.domain.entity_service import entity_service
from app.services.audit.audit_service import audit_service
from app.core.error_handling import handle_database_error
from app.core.utils import get_correlation_id

router = APIRouter()


@router.post(
    "/",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create entity",
    description="Create a new entity with proper validation",
    responses={
        201: {
            "description": "Entity created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "65a1b2c3d4e5f6789abcdef0",
                        "name": "Example Entity",
                        "description": "Example description",
                        "status": "active",
                        "created_at": "2024-01-10T12:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Entity already exists"},
        500: {"description": "Internal server error"}
    }
)
async def create_entity(
    entity_data: EntityCreate,
    current_user: User = Depends(require_permissions(["entities:create"]))
):
    """
    Create a new entity.
    
    **Features:**
    - Validates input data
    - Checks for duplicates
    - Creates audit trail
    - Returns created entity
    
    **Authentication:**
    Requires 'entities:create' permission.
    """
    logger.info(f"🏗️ [CREATE_ENTITY] Creating entity: {entity_data.name}")
    logger.info(f"👤 [CREATE_ENTITY] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Create entity using service
        entity = await entity_service.create_entity(entity_data, current_user.id)
        
        # Audit logging
        correlation_id = get_correlation_id()
        await audit_service.log_event(
            action="entity_created",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            resource_type="entity",
            resource_id=str(entity["_id"]),
            payload={
                "entity_name": entity["name"],
                "entity_description": entity.get("description")
            },
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [CREATE_ENTITY] Entity created: {entity['_id']}")
        
        return EntityResponse(
            id=str(entity["_id"]),
            name=entity["name"],
            description=entity.get("description"),
            status=entity["status"],
            created_at=entity["created_at"].isoformat(),
            updated_at=entity["updated_at"].isoformat()
        )
        
    except ValueError as e:
        logger.error(f"❌ [CREATE_ENTITY] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ [CREATE_ENTITY] Unexpected error: {str(e)}")
        raise handle_database_error(e, "create_entity", "entity")


@router.get(
    "/",
    response_model=EntityListResponse,
    summary="List entities",
    description="Get paginated list of entities with filtering",
    responses={
        200: {
            "description": "Entities retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "entities": [
                            {
                                "id": "65a1b2c3d4e5f6789abcdef0",
                                "name": "Example Entity",
                                "status": "active",
                                "created_at": "2024-01-10T12:00:00Z"
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "limit": 50
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"}
    }
)
async def list_entities(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=50, ge=1, le=100, description="Number of items to return"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    current_user: User = Depends(require_permissions(["entities:read"]))
):
    """
    Get paginated list of entities.
    
    **Features:**
    - Pagination support
    - Status filtering
    - Proper error handling
    
    **Authentication:**
    Requires 'entities:read' permission.
    """
    logger.info(f"📋 [LIST_ENTITIES] Listing entities: skip={skip}, limit={limit}, status={status}")
    logger.info(f"👤 [LIST_ENTITIES] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Get entities using service
        entities = await entity_service.list_entities(skip=skip, limit=limit, status=status)
        
        # Convert to response format
        entity_responses = []
        for entity in entities:
            entity_responses.append(EntityResponse(
                id=str(entity["_id"]),
                name=entity["name"],
                description=entity.get("description"),
                status=entity["status"],
                created_at=entity["created_at"].isoformat(),
                updated_at=entity["updated_at"].isoformat()
            ))
        
        logger.info(f"✅ [LIST_ENTITIES] Found {len(entity_responses)} entities")
        
        return EntityListResponse(
            entities=entity_responses,
            total=len(entity_responses),
            page=(skip // limit) + 1,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"❌ [LIST_ENTITIES] Unexpected error: {str(e)}")
        raise handle_database_error(e, "list_entities", "entity")
```

## 🔧 **Error Handling Patterns**

### **Professional Error Handling**
```python
def handle_database_error(error: Exception, operation: str, resource_type: str) -> HTTPException:
    """Standardized database error handling."""
    error_message = str(error).lower()
    
    if "duplicate key" in error_message:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=get_error_response(ErrorCode.RESOURCE_ALREADY_EXISTS)["message"]
        )
    elif "not found" in error_message:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=get_error_response(ErrorCode.RESOURCE_NOT_FOUND)["message"]
        )
    elif "validation" in error_message:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_error_response(ErrorCode.VALIDATION_ERROR)["message"]
        )
    else:
        logger.error(f"❌ Database error in {operation} for {resource_type}: {str(error)}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)["message"]
        )
```

## 📊 **Configuration Management**

### **Professional Settings Structure**
```python
class Settings(BaseSettings):
    """Professional application settings with proper defaults."""
    
    # Database settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="chat_platform")
    
    # Application settings
    APP_NAME: str = Field(default="WhatsApp Business Platform")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Feature flags
    AUTO_CLOSE_ENABLED: bool = Field(default=True)
    SURVEY_ON_CLOSE_ENABLED: bool = Field(default=True)
    
    # Limits and constraints
    MAX_TAGS_PER_CONVERSATION: int = Field(default=10)
    QUICK_ADD_TAGS_LIMIT: int = Field(default=7)
    MAX_AGENT_TRANSFERS: int = Field(default=10)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

## 🧪 **Testing Patterns**

### **Professional Test Structure**
```python
"""
Professional test file with proper setup and teardown.
Uses super admin user for authentication.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.core.logger import logger

@pytest_asyncio.fixture(scope="module")
async def login_token():
    """Get authentication session for super admin user."""
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"

    async with AsyncClient(base_url=base_url) as ac:
        login_payload = {
            "email": "testuser@example.com", 
            "password": "testpassword123"
        }
        resp = await ac.post(f"{api_prefix}/auth/users/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()
        cookies = resp.cookies
        session_cookie = cookies.get("session_token")
        return session_cookie, data

@pytest.mark.asyncio
async def test_create_entity(login_token):
    """Test entity creation endpoint."""
    logger.info("[TEST] Starting test_create_entity")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"

    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test entity creation
            entity_data = {
                "name": "Test Entity",
                "description": "Test description"
            }
            
            resp = await ac.post(
                f"{api_prefix}/entities", 
                json=entity_data, 
                cookies=cookies
            )
            
            logger.info(f"[TEST] Create entity status: {resp.status_code}")
            assert resp.status_code == 201
            
            data = resp.json()
            assert "id" in data
            assert data["name"] == entity_data["name"]
            assert data["status"] == "active"
            
            logger.info(f"[TEST] Entity created: {data['id']}")

    except AssertionError as e:
        logger.error(f"[TEST] test_create_entity failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_create_entity unexpected error: {e}")
        raise

    logger.info("[TEST] test_create_entity completed successfully.")
```

## 🚀 **Implementation Checklist**

When creating new backend features, ensure:

- [ ] ✅ Service layer follows single responsibility principle
- [ ] ✅ Proper error handling with standardized responses
- [ ] ✅ Database indexes are optimized for common queries
- [ ] ✅ Input validation with Pydantic schemas
- [ ] ✅ Audit logging for all operations
- [ ] ✅ Proper authentication and authorization
- [ ] ✅ Comprehensive API documentation
- [ ] ✅ Unit and integration tests
- [ ] ✅ Configuration management with environment variables
- [ ] ✅ Proper logging with correlation IDs
- [ ] ✅ Database transactions for complex operations
- [ ] ✅ Rate limiting and security measures
- [ ] ✅ Performance monitoring and metrics
- [ ] ✅ Proper HTTP status codes
- [ ] ✅ Consistent API response formats

This rule set ensures consistent, professional, and maintainable backend development! 🎯
