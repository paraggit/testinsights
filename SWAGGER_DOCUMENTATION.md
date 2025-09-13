# TestInsight API Swagger Documentation

TestInsight now includes comprehensive Swagger/OpenAPI documentation with enhanced UI, detailed examples, and interactive testing capabilities.

## 🎯 **What's Included**

### **Enhanced API Documentation**

- **Comprehensive endpoint documentation** with detailed descriptions
- **Interactive examples** for all request/response models
- **Multiple response scenarios** with proper HTTP status codes
- **Tag-based organization** for better navigation
- **Rich markdown descriptions** with formatting and emojis

### **Custom Swagger UI**

- **Modern, polished interface** with custom styling
- **Enhanced color scheme** matching your brand
- **Improved readability** with better typography
- **Interactive testing** with "Try it out" functionality
- **Persistent authentication** (for future auth implementation)

### **Alternative Documentation Views**

- **Swagger UI** (`/docs`) - Interactive API explorer
- **ReDoc** (`/redoc`) - Clean, readable documentation
- **OpenAPI JSON** (`/openapi.json`) - Raw schema for tools

## 🚀 **Accessing the Documentation**

### **1. Start the API Server**

```bash
# Using CLI command
poetry run test_insights api start

# Or using standalone script
poetry run python run_api.py
```

### **2. View Documentation**

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📋 **Documentation Features**

### **Endpoint Categories**

#### **🤖 Queries** (`/query`)

- Natural language query processing
- AI-powered test data analysis
- Multiple LLM provider support
- Comprehensive examples for different query types

#### **🔍 Search** (`/search`)

- Vector database semantic search
- Entity type filtering
- Similarity scoring
- Direct data exploration

#### **🔄 Sync** (`/sync`)

- ReportPortal data synchronization
- Incremental and full sync options
- Project and entity filtering
- Background processing

#### **⚙️ System** (`/`, `/health`, `/status`, `/config`, `/storage`)

- API information and health checks
- System status and statistics
- Configuration management
- Storage operations

### **Request/Response Examples**

Each endpoint includes:

- **Multiple request examples** covering different use cases
- **Complete response schemas** with example data
- **Error response examples** with proper error types
- **Field validation rules** with constraints

### **Interactive Testing**

The Swagger UI allows you to:

- **Test endpoints directly** from the browser
- **Customize request parameters** with form inputs
- **View real responses** with proper formatting
- **Copy curl commands** for external testing
- **Explore different scenarios** with example data

## 🎨 **Customization Features**

### **Enhanced Styling**

- **Custom color scheme** with professional appearance
- **Improved typography** for better readability
- **Brand-consistent design** with TestInsight theming
- **Responsive layout** for mobile and desktop

### **Advanced Features**

- **Deep linking** to specific endpoints
- **Filtering capabilities** to find endpoints quickly
- **Expandable sections** for better organization
- **Code syntax highlighting** for examples
- **Request/response duration tracking**

## 📖 **Documentation Content**

### **Comprehensive Descriptions**

Each endpoint includes:

- **Purpose and use cases** with practical examples
- **Step-by-step workflow** explanations
- **Parameter details** with validation rules
- **Response format** descriptions
- **Error handling** scenarios
- **Performance considerations**

### **Example Queries for AI Endpoints**

The documentation includes realistic examples:

- `"What tests failed yesterday?"`
- `"Show me the success rate for API tests this week"`
- `"Why did the login tests fail?"`
- `"Find tests with timeout errors"`
- `"Compare test results between this week and last week"`

### **Slack Bot Integration Examples**

Special attention to Slack bot use cases:

- **Query formatting** for chat interfaces
- **Response optimization** for readability
- **Error handling** for user-friendly messages
- **Parameter suggestions** for common requests

## 🛠 **Technical Implementation**

### **OpenAPI Schema Enhancements**

- **Custom schema generation** with additional metadata
- **Example data integration** from Pydantic models
- **Tag-based organization** for logical grouping
- **External documentation links**
- **Security scheme definitions** (for future auth)

### **Custom UI Components**

- **Branded header** with TestInsight logo
- **Enhanced code blocks** with syntax highlighting
- **Improved navigation** with sticky sidebar
- **Custom CSS styling** for professional appearance
- **JavaScript enhancements** for better UX

### **Model Documentation**

- **Pydantic model examples** with realistic data
- **Field validation rules** clearly documented
- **Optional vs required fields** properly marked
- **Data type specifications** with constraints
- **Nested object examples** for complex responses

## 🔧 **Configuration Options**

### **Swagger UI Customization**

The documentation can be customized by modifying:

- `test_insights/api/swagger_config.py` - UI styling and behavior
- `test_insights/api/app.py` - OpenAPI metadata and tags
- `test_insights/api/models.py` - Request/response examples

### **Available Customizations**

- **Color schemes** and branding
- **Logo and header customization**
- **Default expansion levels** for sections
- **Authentication schemes** (for future use)
- **External documentation** links

## 📱 **Mobile Responsiveness**

The documentation is fully responsive:

- **Mobile-optimized layout** for phones and tablets
- **Touch-friendly interface** for easy navigation
- **Collapsible sections** for better mobile experience
- **Optimized font sizes** for readability

## 🚀 **Getting Started Examples**

### **Basic Query Example**

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Show me failed tests from the last 7 days",
       "show_sources": true,
       "n_results": 20
     }'
```

### **Search Example**

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "timeout error",
       "entity_types": ["test_item"],
       "limit": 10
     }'
```

### **Sync Example**

```bash
curl -X POST "http://localhost:8000/sync" \
     -H "Content-Type: application/json" \
     -d '{
       "projects": ["web-app"],
       "full": false
     }'
```

## 🎯 **Benefits for Developers**

### **API Exploration**

- **Discover available endpoints** without reading code
- **Understand request/response formats** quickly
- **Test functionality** before integration
- **Copy working examples** for implementation

### **Integration Support**

- **Clear parameter documentation** for all endpoints
- **Error response examples** for proper handling
- **Authentication preparation** for future security
- **Performance guidelines** for optimal usage

### **Maintenance Benefits**

- **Auto-generated documentation** stays in sync with code
- **Version tracking** with API schema evolution
- **Comprehensive testing** through interactive UI
- **Debugging support** with detailed error information

## 🔍 **Quality Assurance**

The documentation includes:

- ✅ **All endpoints documented** with comprehensive descriptions
- ✅ **Request/response examples** for every model
- ✅ **Error scenarios covered** with proper HTTP codes
- ✅ **Interactive testing** functionality verified
- ✅ **Mobile responsiveness** tested
- ✅ **Custom styling** applied consistently
- ✅ **External links** and metadata included

## 🎉 **Ready for Production**

Your TestInsight API now has enterprise-grade documentation that:

- **Accelerates developer onboarding**
- **Reduces support requests** with clear examples
- **Enables self-service integration** for users
- **Provides professional appearance** for stakeholders
- **Supports multiple documentation formats**

The Swagger documentation is now fully integrated and ready for use by your development team and API consumers!
