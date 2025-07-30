# WhatsApp Business Platform Backend

A production-ready, comprehensive WhatsApp Business Platform backend built with FastAPI and MongoDB, featuring full conversation management, RBAC authentication, media handling, and real-time capabilities.

## 🚀 Features

### Core Platform Features
- **WhatsApp Business API Integration** - Complete integration with Meta's Cloud API
- **Multi-Channel Support** - WhatsApp, Instagram, Facebook Messenger unified inbox
- **Real-time Communication** - WebSocket support for live updates
- **Comprehensive RBAC** - Role-based access control with granular permissions
- **Audit Trail** - Complete logging of all system activities for compliance
- **Media Management** - Support for all WhatsApp media types with proper validation
- **Conversation Management** - Full chat lifecycle with agent assignment and transfer
- **Department Management** - Organizational structure with routing and SLA management

### Technical Features
- **Async/Await** - Full asynchronous support for high performance
- **MongoDB Integration** - Optimized with proper indexing and connection pooling
- **JWT Authentication** - Secure token-based authentication with refresh tokens
- **Comprehensive Validation** - Pydantic schemas for all requests/responses
- **Error Handling** - Centralized error codes and structured error responses
- **Health Monitoring** - Built-in health checks and metrics
- **API Documentation** - Auto-generated OpenAPI/Swagger documentation
- **Rate Limiting** - Built-in protection against abuse
- **CORS Support** - Proper cross-origin resource sharing configuration

## 📋 Requirements

- Python 3.11+
- MongoDB 4.4+
- Redis 6.0+ (for caching and sessions)
- WhatsApp Business Account with API access

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cu-su-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:

```env
# Application Settings
APP_NAME="WhatsApp Business Platform Backend"
APP_VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=true
SECRET_KEY="your-super-secret-key-here"

# Database Configuration
MONGODB_URI="mongodb://localhost:27017"
DATABASE_NAME="whatsapp_business_platform"
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_POOL_SIZE=100

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN="your-whatsapp-access-token"
WHATSAPP_VERIFY_TOKEN="your-webhook-verify-token"
WHATSAPP_BUSINESS_ID="your-business-account-id"
WHATSAPP_PHONE_NUMBER_ID="your-phone-number-id"

# Redis Configuration
REDIS_URL="redis://localhost:6379"
REDIS_PASSWORD=""
REDIS_DB=0

# Email Configuration
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_SENDER_EMAIL="noreply@yourcompany.com"
SMTP_SENDER_PASSWORD="your-email-password"

# Security Settings
SESSION_EXPIRE_MINUTES=160
```

### 5. Database Setup
The application will automatically create indexes and initialize the database on startup. Ensure MongoDB is running and accessible.

### 6. Run the Application

#### Development
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production
```bash
python -m gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📚 API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🏗 Architecture

### Project Structure
```
app/
├── api/                    # API routes and endpoints
│   └── routes/            # Feature-based route modules
├── core/                  # Core application modules
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging configuration
│   ├── security.py       # Authentication & authorization
│   └── utils.py          # Utility functions
├── db/                   # Database layer
│   ├── client.py         # MongoDB client with indexing
│   └── models/           # Pydantic models for collections
├── services/             # Business logic services
├── schemas/              # API request/response schemas
├── config/               # Configuration files
│   └── error_codes.py    # Centralized error definitions
└── main.py               # FastAPI application factory
```

### Database Models

#### Core Collections
- **users** - User accounts with roles and permissions
- **roles** - RBAC roles with permission assignments
- **permissions** - Granular permission definitions
- **departments** - Organizational departments with settings
- **conversations** - WhatsApp conversation threads
- **messages** - Individual messages with media support
- **media** - File metadata and storage references
- **tags** - Flexible labeling system
- **notes** - Internal annotations and comments
- **audit_logs** - Complete activity audit trail
- **company_profile** - Company settings and branding

#### Key Features
- **Comprehensive Indexing** - Optimized queries for all collections
- **Relationship Management** - Proper foreign key relationships
- **Audit Trail** - Complete change tracking for compliance
- **Soft Deletion** - Data retention with deletion timestamps
- **Metadata Tracking** - Created/updated timestamps and user tracking

### Authentication & Authorization

#### Session-Based Authentication
- **Session Cookies** - Secure HTTP-only cookies for session management
- **Session Timeout** - Configurable session expiration (160 minutes default)
- **Cookie Security** - HttpOnly, Secure, and SameSite attributes for protection
- **Session Validation** - Comprehensive session verification with proper error handling

#### RBAC Implementation
- **Role-Based Access** - Users assigned to roles with specific permissions
- **Permission Granularity** - Fine-grained permissions for all operations
- **Department Scoping** - Department-level access control
- **Super Admin Override** - Bypass permissions for administrative accounts

## 🔐 Security Features

### Authentication
- Session-based authentication with secure cookie management
- Password hashing using bcrypt with salt
- Session management with proper expiration
- Two-factor authentication support (ready for implementation)

### Authorization
- Role-based access control (RBAC)
- Granular permission system
- Department-level access restrictions
- API key authentication for integrations

### Data Protection
- Input validation and sanitization
- SQL injection prevention (NoSQL injection for MongoDB)
- XSS protection through proper response handling
- Rate limiting to prevent abuse
- CORS configuration for cross-origin requests

## 📊 Monitoring & Observability

### Health Checks
- Database connectivity monitoring
- Response time tracking
- System resource monitoring
- External service health checks

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking with stack traces
- Audit trail logging for compliance

### Metrics
- API performance metrics
- Database query performance
- Authentication success/failure rates
- Business metrics (conversations, messages, etc.)

## 🔧 Configuration Management

All configuration is managed through environment variables with Pydantic Settings:

- **Database Settings** - Connection pooling, timeouts, retry logic
- **WhatsApp API Settings** - Tokens, webhooks, media limits
- **Security Settings** - Token expiration, password policies
- **Feature Flags** - Enable/disable specific features
- **Performance Settings** - Rate limits, batch sizes, timeouts

## 🚀 Deployment

### Environment Preparation
1. Set up MongoDB with replica set for production
2. Configure Redis for session storage and caching
3. Set up reverse proxy (Nginx) for SSL termination
4. Configure monitoring and logging infrastructure

### Production Checklist
- [ ] Environment variables properly configured
- [ ] Database indexes created and optimized
- [ ] SSL certificates installed
- [ ] Rate limiting configured
- [ ] Monitoring and alerting set up
- [ ] Backup and disaster recovery planned
- [ ] Security audit completed

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Structure
- **Unit Tests** - Individual component testing
- **Integration Tests** - Database and API integration
- **End-to-End Tests** - Complete workflow testing
- **Performance Tests** - Load and stress testing

## 📖 API Reference

### Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/register` - User registration

### User Management
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Conversation Management
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation details
- `POST /api/v1/conversations/{id}/transfer` - Transfer conversation
- `POST /api/v1/conversations/{id}/close` - Close conversation

### Message Handling
- `GET /api/v1/conversations/{id}/messages` - Get messages
- `POST /api/v1/conversations/{id}/messages` - Send message
- `GET /api/v1/messages/{id}` - Get message details

### Media Management
- `POST /api/v1/media/upload` - Upload media file
- `GET /api/v1/media/{id}` - Get media metadata
- `GET /api/v1/media/{id}/download` - Download media file

## WhatsApp Message Sending API

### POST /messages/send

Send a WhatsApp message to a customer. You can now provide either a `conversation_id` (to send in an existing conversation) or just a `customer_phone` (to auto-create or reuse a conversation for that customer).

#### Request Payload (Option 1: Use existing conversation)
```json
{
  "conversation_id": "<existing_conversation_id>",
  "text_content": "Hello!"
}
```

#### Request Payload (Option 2: Auto-create or reuse by phone)
```json
{
  "customer_phone": "+1234567890",
  "text_content": "Hello!"
}
```

- If `conversation_id` is omitted, the backend will look up an active/pending conversation for the phone, or create a new one if none exists.
- The response will always include the used/created `conversation_id`.

#### Response Example
```json
{
  "message": {
    "conversation_id": "<conversation_id>",
    "text_content": "Hello!",
    ...
  },
  "whatsapp_response": { ... }
}
```

#### Why?
- This change improves developer experience and reduces the need for manual conversation management in your client/frontend code.
- You can now send a message to any customer with a single API call, and the backend will handle conversation context for you.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation at `/docs` endpoint

## 🔄 Roadmap

### Upcoming Features
- [ ] Real-time WebSocket implementation
- [ ] WhatsApp webhook handlers
- [ ] Advanced analytics and reporting
- [ ] Message templates management
- [ ] Customer segmentation
- [ ] Automated chat routing
- [ ] Integration with CRM systems
- [ ] Multi-language support
- [ ] Advanced search and filtering
- [ ] Export/import functionality

### Performance Improvements
- [ ] Redis caching implementation
- [ ] Background task processing
- [ ] Database query optimization
- [ ] CDN integration for media files
- [ ] Horizontal scaling support

## 📊 Current Status

✅ **Completed Components:**
- Core application structure with FastAPI
- Comprehensive MongoDB models and indexing
- JWT authentication with RBAC
- Error handling and validation
- Configuration management
- Database client with connection pooling
- Comprehensive logging system
- Health monitoring endpoints
- API documentation structure

🚧 **In Progress:**
- WhatsApp webhook implementation
- Real-time WebSocket endpoints
- Service layer implementation
- Complete API route implementation

📋 **Next Steps:**
1. Implement WhatsApp webhook handlers
2. Add WebSocket support for real-time features
3. Create service layer for business logic
4. Implement remaining API endpoints
5. Add comprehensive testing suite
6. Set up CI/CD pipeline
7. Performance optimization and monitoring

---

Built with ❤️ using FastAPI, MongoDB, and modern Python practices. 
