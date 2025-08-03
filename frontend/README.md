# WhatsApp Business Platform Frontend

A professional Next.js 15+ frontend for the WhatsApp Business platform with modern design, real-time messaging, and comprehensive chat management features.

## 🚀 Features

### Core Functionality
- **Session-based Authentication** - Secure login/logout with httpOnly cookies
- **Real-time Messaging** - WebSocket integration for live chat updates  
- **Multi-environment Support** - Development, staging, and production configurations
- **Responsive Design** - Mobile-first approach with proper responsive breakpoints
- **Dark/Light Themes** - Theme switching with persistent preferences
- **Role-based Access Control** - Permission-based UI rendering and route protection

### User Interface
- **Modern Design System** - Consistent components with Tailwind CSS
- **WhatsApp-style Chat** - Familiar messaging interface with proper bubble alignment
- **Toast Notifications** - User-friendly error and success messages
- **Loading States** - Proper loading indicators and skeleton screens
- **Accessibility** - WCAG AA compliance with keyboard navigation

### Technical Stack
- **Framework**: Next.js 15+ with App Router
- **Styling**: Tailwind CSS with CSS variables
- **State Management**: Zustand for UI and authentication state
- **Forms**: React Hook Form with Zod validation
- **Real-time**: WebSocket client with auto-reconnection
- **Theme**: next-themes with class strategy
- **Icons**: Heroicons and Lucide React

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js App Router pages
│   ├── (auth)/                   # Authentication pages
│   │   ├── login/page.tsx        # Login page
│   │   └── layout.tsx            # Auth layout
│   ├── (dashboard)/              # Protected dashboard pages
│   │   ├── conversations/        # Conversation management
│   │   ├── departments/          # Department management
│   │   ├── users/                # User management
│   │   ├── analytics/            # Analytics dashboard
│   │   ├── settings/             # Application settings
│   │   └── layout.tsx            # Dashboard layout
│   ├── (api)/api/                # BFF API routes
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Root page (redirects)
│   └── globals.css               # Global styles
├── components/                   # Reusable components
│   ├── ui/                       # Design system primitives
│   │   ├── Button.tsx            # Button component with variants
│   │   ├── Input.tsx             # Input with validation states
│   │   ├── Card.tsx              # Card container components
│   │   ├── Badge.tsx             # Status indicators
│   │   ├── Avatar.tsx            # User avatars with fallbacks
│   │   ├── Dialog.tsx            # Modal dialogs
│   │   └── Toast.tsx             # Notification system
│   ├── layout/                   # Layout components
│   │   ├── Header.tsx            # Dashboard header
│   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   └── Navigation.tsx        # Navigation components
│   ├── chat/                     # Chat-specific components
│   ├── theme/                    # Theme management
│   │   ├── ThemeProvider.tsx     # Theme context provider
│   │   └── ThemeToggle.tsx       # Theme switcher
│   └── auth/                     # Authentication components
│       └── AuthWrapper.tsx       # Auth state wrapper
├── features/                     # Feature-based modules
│   ├── auth/api/authApi.ts       # Authentication API client
│   ├── conversations/            # Conversation management
│   ├── messages/                 # Message handling
│   ├── departments/              # Department management
│   └── users/                    # User management
├── lib/                          # Utility libraries
│   ├── config.ts                 # Environment configuration
│   ├── http.ts                   # HTTP client with error handling
│   ├── ws.ts                     # WebSocket client
│   ├── auth.ts                   # Authentication utilities
│   ├── store.ts                  # Zustand state management
│   └── utils.ts                  # Helper functions
├── tailwind.config.ts            # Tailwind configuration
├── next.config.mjs               # Next.js configuration
├── tsconfig.json                 # TypeScript configuration
└── .env.example                  # Environment variables template
```

## 🛠️ Development Setup

### Prerequisites
- Node.js 18+ and npm
- Access to the FastAPI backend running on port 8000

### Installation

1. **Clone and navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your backend configuration:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   NEXT_PUBLIC_API_PREFIX=/api/v1
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

5. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🔧 Configuration

### Environment Variables

The frontend supports multiple environment configurations:

- **Development**: Uses `localhost:8000` by default
- **Staging**: Set `NEXT_PUBLIC_STAGING_BASE_URL` and `NEXT_PUBLIC_STAGING_WS_URL`
- **Production**: Set `NEXT_PUBLIC_PRODUCTION_BASE_URL` and `NEXT_PUBLIC_PRODUCTION_WS_URL`

### Backend Integration

The frontend integrates with the FastAPI backend through:

1. **Session Cookies**: Authentication managed via httpOnly cookies
2. **REST API**: All CRUD operations via `/api/v1` endpoints
3. **WebSocket**: Real-time updates via `/ws/chat/{user_id}`
4. **Error Handling**: Centralized error codes and user-friendly messages

### Key Integration Points

- **Login**: `POST /auth/users/login` - Sets session cookie
- **Logout**: `POST /auth/users/logout` - Clears session cookie
- **Conversations**: `GET /whatsapp/chat/conversations/` - List conversations
- **Messages**: `POST /whatsapp/chat/messages/send` - Send messages
- **WebSocket**: `ws://backend/ws/chat/{user_id}` - Real-time updates

## 🎨 Design System

### Colors (CSS Variables)

**Light Theme**:
- Primary: `#2563eb` (blue-600)
- Background: `#ffffff` (white)
- Surface: `#f8fafc` (slate-50)
- Text: `#0f172a` (slate-900)

**Dark Theme**:
- Primary: `#3b82f6` (blue-500)
- Background: `#0f172a` (slate-900)
- Surface: `#1e293b` (slate-800)
- Text: `#f8fafc` (slate-50)

### Component Guidelines

- **Consistent Spacing**: 4px grid system
- **Border Radius**: 8px for cards and buttons
- **Transitions**: 150ms ease-in-out
- **Typography**: Inter font family
- **Icons**: 24px outline style from Heroicons

## 🚀 Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment-specific Builds

For staging:
```bash
NODE_ENV=staging npm run build
```

For production:
```bash
NODE_ENV=production npm run build
```

### Docker Deployment

Create `Dockerfile`:
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

Build and run:
```bash
docker build -t whatsapp-frontend .
docker run -p 3000:3000 whatsapp-frontend
```

## 🧪 Testing

### Running Tests

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

### Test Structure

- **Unit Tests**: Component rendering and hook logic
- **Integration Tests**: API client functions
- **E2E Tests**: Critical user flows with Playwright

## 📚 Key Features Implementation

### Authentication Flow

1. User visits protected route → redirected to `/login`
2. User submits login form → `AuthApi.login()` called
3. Backend sets httpOnly session cookie
4. Frontend stores auth state in Zustand
5. User redirected to `/conversations`
6. Subsequent requests include session cookie automatically

### Real-time Messaging

1. User authenticates → WebSocket connection established
2. User joins conversation → `wsClient.joinConversation(id)`
3. New message received → WebSocket event triggers UI update
4. User types → typing indicators sent via WebSocket
5. Connection lost → automatic reconnection with exponential backoff

### Error Handling

1. API error occurs → `ApiError` thrown with error code
2. `handleApiError()` maps error codes to user messages
3. Toast notification displayed with appropriate message
4. Detailed error logged to console for debugging

## 🔒 Security Features

- **Session Management**: httpOnly cookies prevent XSS
- **CSP Headers**: Content Security Policy prevents injection
- **Input Validation**: Zod schemas validate all user input
- **Route Protection**: Middleware enforces authentication
- **Error Sanitization**: No sensitive data in error messages

## 📝 Development Guidelines

### Code Style

- **TypeScript Strict**: No `any` types allowed
- **Component Size**: Keep under 200 lines where practical
- **File Organization**: Feature-based structure
- **Naming**: Use descriptive, consistent naming

### Best Practices

- Use Server Components by default
- Client Components only for interactivity
- Implement proper loading states
- Handle error boundaries
- Follow accessibility guidelines
- Use semantic HTML structure

## 🤝 Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following coding standards
3. Test thoroughly (unit + E2E)
4. Submit pull request with description
5. Code review and merge

### Coding Standards

- Follow existing patterns and conventions
- Write self-documenting code
- Add proper TypeScript types
- Include error handling
- Test critical functionality

## 📞 Support

For support and questions:

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs and features
- **Backend Integration**: Refer to backend API documentation

## 📄 License

This project is part of the WhatsApp Business Platform suite. All rights reserved.