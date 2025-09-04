# 📚 API Documentation Pattern

## Overview

API documentation patterns ensure that the API is well-documented, discoverable, and easy to use while following Clean Architecture principles.

## OpenAPI/Swagger Documentation

### Enhanced FastAPI Documentation

```python
# main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Vacancy Portal API",
    description="""
    Clean Architecture implementation of Vacancy Portal API.
    
    ## Features
    
    * **Tenant Management**: Complete CRUD operations for tenants
    * **Organization Support**: Multi-tenant architecture
    * **Waitlist Management**: Automated admission workflows
    * **Authentication**: JWT-based authentication
    * **Authorization**: Role-based access control
    
    ## Getting Started
    
    1. Obtain an API key from `/auth/login`
    2. Include the token in `Authorization: Bearer {token}` header
    3. Start making requests to the API endpoints
    
    ## Error Handling
    
    All errors follow a consistent format:
    ```json
    {
        "error_code": "TENANT_NOT_FOUND",
        "message": "Tenant with ID 123 not found",
        "details": {"tenant_id": 123}
    }
    ```
    
    ## Rate Limiting
    
    API requests are rate limited to prevent abuse:
    - 100 requests per minute for authenticated users
    - 10 requests per minute for anonymous users
    """,
    version="2.0.0",
    contact={
        "name": "API Support",
        "email": "support@vacancyportal.com",
        "url": "https://vacancyportal.com/support"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/api/docs",           # Swagger UI
    redoc_url="/api/redoc",         # ReDoc
    openapi_url="/api/openapi.json" # OpenAPI JSON
)

# Custom OpenAPI schema generator
def custom_openapi():
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "apiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Set global security
    openapi_schema["security"] = [
        {"bearerAuth": []},
        {"apiKey": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Endpoint Documentation

```python
# presentation/controllers/tenant_controller.py
@tenant_router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=201,
    summary="Create a new tenant",
    description="""
    Creates a new tenant in the system with validation and business rules.
    
    **Required Permissions:**
    - `create:tenants` for the specified organization
    
    **Business Rules:**
    - Tenant name must be unique within the organization
    - Organization must exist and be active
    - User must have permission to create tenants in the organization
    
    **Side Effects:**
    - Sends notification to organization administrators
    - Updates organization's tenant count metrics
    """,
    response_description="Successfully created tenant",
    responses={
        201: {
            "description": "Tenant created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "John Doe",
                        "organization_id": 1,
                        "is_waitlist": True,
                        "created_at": "2023-01-01T12:00:00Z"
                    }
                }
            }
        },
        409: {
            "description": "Tenant already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "TENANT_ALREADY_EXISTS",
                        "message": "Tenant 'John Doe' already exists in organization 1",
                        "details": {
                            "tenant_name": "John Doe",
                            "organization_id": 1
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "name"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_tenant(
    request: CreateTenantRequest,
    use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> TenantResponse:
    """Create a new tenant"""
    return await use_case.execute(request)
```

## Interactive Documentation

### Swagger UI Customization

```python
# presentation/docs/swagger_config.py
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.ico",
        init_oauth=None,
        swagger_ui_parameters={
            "deepLinking": True,
            "displayOperationId": True,
            "defaultModelsExpandDepth": 1,
            "defaultModelExpandDepth": 1,
            "defaultModelRendering": "model",
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "maxDisplayedTags": None,
            "operationsSorter": "alpha",
            "showExtensions": True,
            "showCommonExtensions": True,
            "tagsSorter": "alpha",
            "validatorUrl": None,
            "supportedSubmitMethods": ["get", "put", "post", "delete", "options", "head", "patch", "trace"]
        }
    )
```

### API Examples and Tutorials

```python
# presentation/docs/examples.py
API_EXAMPLES = {
    "create_tenant": {
        "title": "Create a New Tenant",
        "description": "Add a new tenant to the waitlist",
        "language": "python",
        "code": """
import requests

# Set up authentication
headers = {
    "Authorization": "Bearer your-jwt-token",
    "Content-Type": "application/json"
}

# Create tenant
tenant_data = {
    "name": "John Doe",
    "organization_id": 1,
    "is_waitlist": True
}

response = requests.post(
    "https://api.vacancyportal.com/api/v2/tenants",
    json=tenant_data,
    headers=headers
)

print(f"Created tenant: {response.json()}")
        """,
        "curl": """
curl -X POST "https://api.vacancyportal.com/api/v2/tenants" \\
  -H "Authorization: Bearer your-jwt-token" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "John Doe",
    "organization_id": 1,
    "is_waitlist": true
  }'
        """
    },
    
    "admit_tenant": {
        "title": "Admit a Tenant",
        "description": "Move a tenant from waitlist to admitted status",
        "language": "javascript",
        "code": """
// Using fetch API
const admitTenant = async (tenantId, admissionDate) => {
    const response = await fetch(`/api/v2/tenants/${tenantId}/admit`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            admission_date: admissionDate
        })
    });
    
    const result = await response.json();
    console.log('Tenant admitted:', result);
};

// Usage
admitTenant(123, '2023-01-15T10:00:00Z');
        """
    }
}
```

## Version Management

### API Version Headers

```python
# presentation/middleware/version_middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API versioning"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract version from header or URL
        version = self._extract_version(request)
        
        # Add version to request state
        request.state.api_version = version
        
        # Process request
        response = await call_next(request)
        
        # Add version header to response
        response.headers["X-API-Version"] = version
        
        return response
    
    def _extract_version(self, request: Request) -> str:
        """Extract API version from request"""
        # Check Accept header
        accept = request.headers.get("Accept", "")
        if "application/vnd.api.v" in accept:
            # Extract version from Accept header
            version_part = accept.split("application/vnd.api.v")[1].split("+")[0]
            return f"v{version_part}"
        
        # Check URL path
        if request.url.path.startswith("/api/v"):
            version = request.url.path.split("/api/v")[1].split("/")[0]
            return f"v{version}"
        
        # Default version
        return "v1"
```

### Version Compatibility

```python
# presentation/compatibility/version_compatibility.py
API_VERSIONS = {
    "v1": {
        "supported": True,
        "deprecated": True,
        "sunset_date": "2024-12-31",
        "changes": [
            "Response format differs from v2",
            "Limited filtering options"
        ]
    },
    "v2": {
        "supported": True,
        "deprecated": False,
        "features": [
            "Enhanced filtering",
            "Bulk operations",
            "Improved error messages"
        ]
    }
}

def get_version_info(version: str) -> dict:
    """Get information about an API version"""
    return API_VERSIONS.get(version, {
        "supported": False,
        "message": f"API version {version} is not supported"
    })

def check_version_compatibility(request_version: str, required_version: str) -> bool:
    """Check if request version is compatible with required version"""
    # Simple version comparison - in practice, you'd want semantic versioning
    request_num = int(request_version.lstrip('v'))
    required_num = int(required_version.lstrip('v'))
    
    return request_num >= required_num
```

## Developer Portal

### Interactive API Explorer

```python
# presentation/docs/portal.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

portal_router = APIRouter()
templates = Jinja2Templates(directory="presentation/templates")

@portal_router.get("/", response_class=HTMLResponse)
async def api_portal(request: Request):
    """API Developer Portal"""
    return templates.TemplateResponse("portal.html", {
        "request": request,
        "title": "Vacancy Portal API",
        "version": "2.0.0",
        "endpoints": [
            {
                "path": "/api/v2/tenants",
                "method": "POST",
                "description": "Create a new tenant",
                "example": {
                    "name": "John Doe",
                    "organization_id": 1,
                    "is_waitlist": True
                }
            }
        ],
        "examples": API_EXAMPLES
    })

@portal_router.get("/changelog")
async def api_changelog():
    """API Changelog"""
    return {
        "versions": [
            {
                "version": "2.0.0",
                "date": "2023-01-01",
                "changes": [
                    "Added bulk operations",
                    "Enhanced filtering",
                    "Improved error messages"
                ]
            },
            {
                "version": "1.0.0",
                "date": "2022-01-01",
                "changes": [
                    "Initial release",
                    "Basic CRUD operations"
                ]
            }
        ]
    }
```

### API Status and Health

```python
# presentation/docs/status.py
@portal_router.get("/status")
async def api_status():
    """API Status and Health Information"""
    return {
        "status": "operational",
        "version": "2.0.0",
        "uptime": "15 days",
        "response_time": "45ms",
        "endpoints": {
            "total": 25,
            "deprecated": 3,
            "experimental": 2
        },
        "rate_limits": {
            "authenticated": "100/minute",
            "anonymous": "10/minute"
        },
        "last_deployment": "2023-01-15T10:00:00Z"
    }

@portal_router.get("/metrics")
async def api_metrics():
    """API Usage Metrics"""
    return {
        "requests_today": 15420,
        "requests_this_week": 89234,
        "popular_endpoints": [
            {"path": "/api/v2/tenants", "requests": 5432},
            {"path": "/api/v2/organizations", "requests": 3210},
            {"path": "/api/v2/auth/login", "requests": 2890}
        ],
        "error_rate": "0.02%",
        "avg_response_time": "45ms"
    }
```

## SDK Generation

### TypeScript SDK

```python
# infrastructure/docs/typescript_sdk.py
from fastapi.openapi.utils import get_openapi
import json

def generate_typescript_sdk():
    """Generate TypeScript SDK from OpenAPI spec"""
    
    # Get OpenAPI spec
    openapi_spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    # Generate TypeScript interfaces
    typescript_code = []
    
    # Generate models
    for name, schema in openapi_spec.get("components", {}).get("schemas", {}).items():
        ts_interface = generate_typescript_interface(name, schema)
        typescript_code.append(ts_interface)
    
    # Generate API client
    api_client = generate_api_client(openapi_spec)
    typescript_code.append(api_client)
    
    return "\n\n".join(typescript_code)

def generate_typescript_interface(name: str, schema: dict) -> str:
    """Generate TypeScript interface from OpenAPI schema"""
    properties = schema.get("properties", {})
    
    interface_lines = [f"export interface {name} {{"]
    
    for prop_name, prop_schema in properties.items():
        prop_type = openapi_type_to_typescript(prop_schema)
        optional = "" if prop_name in schema.get("required", []) else "?"
        interface_lines.append(f"  {prop_name}{optional}: {prop_type};")
    
    interface_lines.append("}")
    
    return "\n".join(interface_lines)

def openapi_type_to_typescript(schema: dict) -> str:
    """Convert OpenAPI type to TypeScript type"""
    type_map = {
        "string": "string",
        "integer": "number",
        "boolean": "boolean",
        "array": "Array",
        "object": "{}"
    }
    
    openapi_type = schema.get("type", "object")
    typescript_type = type_map.get(openapi_type, "any")
    
    if openapi_type == "array":
        items_schema = schema.get("items", {})
        item_type = openapi_type_to_typescript(items_schema)
        typescript_type = f"{item_type}[]"
    
    return typescript_type
```

## Documentation as Code

### Automated Documentation Updates

```python
# infrastructure/docs/auto_update.py
import os
import json
from pathlib import Path
from fastapi.openapi.utils import get_openapi

def update_api_documentation():
    """Automatically update API documentation"""
    
    # Generate latest OpenAPI spec
    openapi_spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    # Save OpenAPI JSON
    docs_dir = Path("docs/api")
    docs_dir.mkdir(exist_ok=True)
    
    with open(docs_dir / "openapi.json", "w") as f:
        json.dump(openapi_spec, f, indent=2)
    
    # Update version information
    version_info = {
        "version": app.version,
        "last_updated": datetime.utcnow().isoformat(),
        "endpoints": len([r for r in app.routes if hasattr(r, 'methods')]),
        "models": len(openapi_spec.get("components", {}).get("schemas", {}))
    }
    
    with open(docs_dir / "version.json", "w") as f:
        json.dump(version_info, f, indent=2)
    
    print("API documentation updated successfully")

# Run on startup
@app.on_event("startup")
async def update_docs():
    """Update documentation on startup"""
    update_api_documentation()
```

### Documentation Testing

```python
# tests/docs/test_api_documentation.py
def test_openapi_spec_valid():
    """Test that OpenAPI spec is valid"""
    openapi_spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    # Validate required fields
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec
    assert "paths" in openapi_spec
    assert "components" in openapi_spec
    
    # Validate info section
    info = openapi_spec["info"]
    assert info["title"] == "Vacancy Portal API"
    assert "version" in info
    assert "description" in info

def test_all_endpoints_documented():
    """Test that all endpoints have documentation"""
    openapi_spec = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes
    )
    
    paths = openapi_spec["paths"]
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            # Check that operation has summary and description
            assert "summary" in operation, f"Missing summary for {method.upper()} {path}"
            assert "description" in operation, f"Missing description for {method.upper()} {path}"
            
            # Check responses
            assert "responses" in operation, f"Missing responses for {method.upper()} {path}"

def test_response_schemas_match_models():
    """Test that response schemas match Pydantic models"""
    # This would validate that the OpenAPI schemas
    # match the actual Pydantic model schemas
    pass
```

This pattern ensures comprehensive, interactive, and maintainable API documentation that evolves with the codebase.
