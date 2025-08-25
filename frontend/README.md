# WhatsApp Business Platform Frontend

A modern, enterprise-grade Next.js 15+ frontend application for the WhatsApp Business Platform, featuring real-time messaging, comprehensive chat management, and a sophisticated design system.

## 🚀 Core Features

### **Real-time Communication**
- **WebSocket Integration** - Live messaging with automatic reconnection
- **Real-time Updates** - Instant conversation and message synchronization
- **Typing Indicators** - Live typing status across all connected clients
- **Message Status Tracking** - Delivery, read, and sent status indicators

### **Advanced Chat Management**
- **Conversation Management** - Multi-conversation support with intelligent routing
- **Message History** - Virtualized message lists for optimal performance
- **File Attachments** - Support for images, documents, and media files
- **Message Search** - Advanced search capabilities across conversations
- **Tag System** - Organize conversations with custom tags and categories

### **AI-Powered Features**
- **AI Agent Integration** - Intelligent chatbot responses and automation
- **Smart Suggestions** - Context-aware message suggestions
- **Automated Responses** - Pre-configured response templates
- **Analytics Dashboard** - AI-driven insights and conversation analytics

### **User Management & Security**
- **Role-based Access Control** - Granular permissions and user roles
- **Department Management** - Multi-department support with routing
- **Session Management** - Secure authentication with httpOnly cookies
- **Multi-environment Support** - Development, staging, and production configs

## 🛠️ Technology Stack

### **Frontend Framework**
- **Next.js 15+** - React framework with App Router
- **React 19** - Latest React with concurrent features
- **TypeScript** - Full type safety and developer experience

### **State Management & Data**
- **Zustand** - Lightweight state management
- **TanStack Query** - Server state management and caching
- **React Hook Form** - Form handling with Zod validation

### **Styling & UI**
- **Tailwind CSS** - Utility-first CSS framework
- **SCSS** - Advanced styling with custom mixins and variables
- **Headless UI** - Accessible UI primitives
- **Lucide React** - Modern icon library
- **next-themes** - Dark/light theme switching

### **Real-time & Communication**
- **Socket.IO Client** - WebSocket communication
- **React Virtuoso** - Virtualized lists for performance

### **Development Tools**
- **ESLint** - Code linting and quality
- **Jest** - Unit testing framework
- **PostCSS** - CSS processing pipeline

## 📁 Project Architecture

```
frontend/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (auth)/                   # Authentication routes
│   │   │   ├── login/                # Login page
│   │   │   └── layout.tsx            # Auth layout
│   │   ├── (dashboard)/              # Protected dashboard routes
│   │   │   ├── conversations/        # Chat management
│   │   │   └── layout.tsx            # Dashboard layout
│   │   ├── api/                      # API routes (BFF)
│   │   ├── globals.scss              # Global styles
│   │   ├── layout.tsx                # Root layout
│   │   └── providers.tsx             # App providers
│   ├── components/                   # Reusable UI components
│   │   ├── ui/                       # Design system primitives
│   │   ├── layout/                   # Layout components
│   │   ├── conversations/            # Chat-specific components
│   │   ├── forms/                    # Form components
│   │   ├── feedback/                 # Notifications and alerts
│   │   └── theme/                    # Theme management
│   ├── features/                     # Feature-based modules
│   │   ├── auth/                     # Authentication
│   │   ├── conversations/            # Chat management
│   │   ├── messages/                 # Message handling
│   │   ├── users/                    # User management
│   │   ├── departments/              # Department management
│   │   ├── tags/                     # Tag system
│   │   └── ai/                       # AI features
│   ├── lib/                          # Core utilities
│   │   ├── config.ts                 # Environment configuration
│   │   ├── http.ts                   # HTTP client
│   │   ├── websocket.ts              # WebSocket management
│   │   ├── store.ts                  # Zustand stores
│   │   ├── auth.ts                   # Auth utilities
│   │   └── utils.ts                  # Helper functions
│   ├── hooks/                        # Custom React hooks
│   └── styles/                       # SCSS styles and variables
├── public/                           # Static assets
├── tests/                            # Test files
│   └── unit/                         # Unit tests
├── tailwind.config.ts                # Tailwind configuration
├── next.config.mjs                   # Next.js configuration
└── package.json                      # Dependencies and scripts
```

## 🎨 Design System

### **Color Palette**
The application uses a sophisticated color system with CSS custom properties supporting both light and dark themes:

- **Primary Colors**: Blue variants for brand identity
- **Semantic Colors**: Success, warning, error states
- **Neutral Colors**: Backgrounds, surfaces, and text
- **Accessibility**: WCAG AA compliant contrast ratios

### **Component Architecture**
- **Atomic Design** - Consistent component hierarchy
- **Variant System** - Flexible component variants using CVA
- **Responsive Design** - Mobile-first approach
- **Accessibility** - ARIA labels and keyboard navigation

### **Typography**
- **Font Family**: System fonts with fallbacks
- **Scale**: Consistent typographic scale
- **Hierarchy**: Clear visual hierarchy for content

## 🔧 Development Setup

### **Prerequisites**
- Node.js 18+ and npm
- Access to the FastAPI backend (port 8010)

### **Installation**

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   # Create .env.local file
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8010
   NEXT_PUBLIC_API_PREFIX=/api/v1
   NEXT_PUBLIC_WS_URL=ws://localhost:8010/api/v1/ws
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Access the application**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🌐 Environment Configuration

The application supports multiple environments with automatic configuration:

### **Development**
- Backend: `http://localhost:8010`
- WebSocket: `ws://localhost:8010/api/v1/ws`

### **Production**
- Backend: `https://api.yourdomain.com`
- WebSocket: `wss://api.yourdomain.com/api/v1/ws`

### **Environment Variables**
```env
NEXT_PUBLIC_API_BASE_URL=    # Backend API base URL
NEXT_PUBLIC_API_PREFIX=      # API endpoint prefix
NEXT_PUBLIC_WS_URL=          # WebSocket connection URL
NODE_ENV=                    # Environment mode
```

## 🔌 Backend Integration

### **Authentication Flow**
1. **Login**: `POST /auth/users/login` - Session-based authentication
2. **Logout**: `POST /auth/users/logout` - Session termination
3. **Session Management**: httpOnly cookies for security

### **API Endpoints**
- **Conversations**: `GET /whatsapp/chat/conversations/`
- **Messages**: `POST /whatsapp/chat/messages/send`
- **Users**: `GET /users/` - User management
- **Departments**: `GET /departments/` - Department management

### **WebSocket Events**
- **Message Events**: Real-time message delivery
- **Status Updates**: Message read/delivery status
- **Typing Indicators**: Live typing status
- **Connection Management**: Auto-reconnection with backoff

## 🚀 Deployment

### **Build for Production**
```bash
npm run build
npm start
```

### **Docker Deployment**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### **Environment-specific Builds**
```bash
# Staging
NODE_ENV=staging npm run build

# Production
NODE_ENV=production npm run build
```

## 🧪 Testing

### **Running Tests**
```bash
# Unit tests
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### **Test Structure**
- **Unit Tests**: Component rendering and logic
- **Integration Tests**: API client functions
- **E2E Tests**: Critical user flows

## 🔒 Security Features

- **Content Security Policy** - XSS protection
- **Session Security** - httpOnly cookies
- **Input Validation** - Zod schema validation
- **Route Protection** - Authentication middleware
- **Error Handling** - Sanitized error messages

## 📊 Performance Optimizations

- **Code Splitting** - Automatic route-based splitting
- **Image Optimization** - Next.js Image component
- **Virtual Scrolling** - React Virtuoso for large lists
- **Caching Strategy** - TanStack Query caching
- **Bundle Analysis** - Optimized bundle sizes

## 🤝 Contributing

### **Development Workflow**
1. Create feature branch: `git checkout -b feature/your-feature`
2. Follow coding standards and patterns
3. Write comprehensive tests
4. Submit pull request with detailed description

### **Code Standards**
- **TypeScript Strict**: No `any` types
- **Component Guidelines**: Keep components focused and reusable
- **Testing**: Maintain high test coverage
- **Documentation**: Update documentation for new features

## 📚 Key Features Implementation

### **Real-time Messaging**
- WebSocket connection management with automatic reconnection
- Message virtualization for performance with large chat histories
- Typing indicators and message status tracking
- File attachment support with preview

### **Authentication System**
- Session-based authentication with secure cookies
- Role-based access control implementation
- Protected routes with middleware
- Automatic session refresh

### **AI Integration**
- AI agent responses with intelligent routing
- Automated message suggestions
- Conversation analytics and insights
- Smart tagging and categorization

## 📞 Support & Documentation

- **API Documentation**: Refer to backend API docs
- **Component Library**: Inline documentation for UI components
- **Issue Tracking**: GitHub issues for bugs and features
- **Development Guide**: This README and inline comments


---

**Built with ❤️ using Next.js 15, React 19, and modern web technologies**