# Galactic Empire Frontend

A modern React TypeScript frontend for the Galactic Empire space conquest game, featuring real-time updates, comprehensive ship management, and intuitive tactical interfaces.

## 🚀 Features

### ✅ Completed Features

- **Modern React Architecture**: Built with React 18, TypeScript, and modern hooks
- **Authentication System**: Complete JWT-based login/register with protected routes
- **Redux State Management**: Comprehensive state management with Redux Toolkit
- **Real-time Updates**: WebSocket integration for live game updates
- **Responsive Design**: Mobile-first design supporting desktop and tablet
- **Ship Management**: Full fleet overview and detailed ship control interfaces
- **Navigation System**: Intuitive sidebar navigation with collapsible menu
- **Dashboard**: Central hub with game statistics and recent activity
- **Communication Center**: Mail, team chat, and beacon messaging interfaces
- **Team Management**: Alliance system with member management
- **Settings Panel**: User preferences and account management

### 🎮 Game Interfaces

#### Main Dashboard
- Welcome screen with game statistics
- Real-time connection status
- Fleet overview and activity feed
- Quick access to all game features

#### Ship Management
- **Fleet Overview**: Grid view of all ships with status indicators
- **Ship Control Panel**: Detailed ship interface with:
  - Navigation controls (movement and coordinates)
  - System status bars (hull, shields, fuel)
  - Weapons management
  - Real-time ship data updates

#### Planetary Management
- Colony management interface
- Resource tracking and trading
- Planet scanning and colonization tools

#### Galaxy Map
- Interactive 3D galaxy visualization
- Sector navigation and exploration
- Ship and planet positioning

#### Communication System
- Multi-channel messaging (Mail, Team Chat, Beacons)
- Real-time message updates
- Distress call system

#### Team Management
- Alliance creation and management
- Member roster and permissions
- Team statistics and scoring

## 🛠 Technical Stack

### Core Technologies
- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development with full type coverage
- **Redux Toolkit** - Predictable state management
- **React Router v6** - Client-side routing with protected routes
- **Styled Components** - CSS-in-JS styling with theme support

### Real-time Communication
- **Socket.io Client** - WebSocket connections for live updates
- **Axios** - HTTP client for API communication
- **React Query** - Server state management and caching

### UI/UX Libraries
- **Framer Motion** - Smooth animations and transitions
- **React Hot Toast** - Elegant notification system
- **React Icons** - Comprehensive icon library
- **React Hook Form** - Form management and validation

### Development Tools
- **ESLint** - Code linting and style enforcement
- **TypeScript** - Static type checking
- **Styled Components** - Component-scoped styling

## 📁 Project Structure

```
src/
├── components/           # Reusable UI components
│   └── Layout/          # Main layout components
│       ├── Layout.tsx   # Main app layout
│       ├── Header.tsx   # Top navigation bar
│       └── Sidebar.tsx  # Side navigation menu
├── pages/               # Route-based page components
│   ├── Auth/           # Authentication pages
│   ├── Dashboard/      # Main game dashboard
│   ├── Ships/          # Ship management pages
│   ├── Planets/        # Planetary management
│   ├── Galaxy/         # Galaxy map interface
│   ├── Communication/  # Messaging system
│   ├── Teams/          # Team management
│   └── Settings/       # User settings
├── store/              # Redux store configuration
│   └── slices/         # Redux slices for state management
├── services/           # API and external services
│   ├── api.ts          # REST API client
│   └── websocket.ts    # WebSocket service
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
└── styles/             # Global styles and themes
```

## 🔧 Setup and Installation

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Backend API running on port 8000

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Environment Variables
Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 🎯 Key Features in Detail

### Authentication Flow
- Secure JWT-based authentication
- Protected route system
- Automatic token refresh
- Logout and session management

### Real-time Updates
- WebSocket connection management
- Automatic reconnection on disconnect
- Live ship and planet updates
- Real-time messaging and notifications

### State Management
- Centralized Redux store
- Type-safe state slices
- Optimistic updates
- Error handling and loading states

### Responsive Design
- Mobile-first approach
- Collapsible sidebar for mobile
- Touch-friendly controls
- Adaptive layouts for all screen sizes

## 🚀 Getting Started

1. **Clone the repository**
2. **Install dependencies**: `npm install`
3. **Start the backend API** (ensure it's running on port 8000)
4. **Start the frontend**: `npm start`
5. **Open your browser** to `http://localhost:3000`

## 📱 Mobile Support

The frontend is fully responsive and optimized for:
- Desktop computers (1200px+)
- Tablets (768px - 1199px)
- Mobile phones (320px - 767px)

## 🔮 Future Enhancements

### Planned Features
- Advanced 3D galaxy visualization
- Real-time combat animations
- Voice chat integration
- Mobile app (React Native)
- Advanced analytics dashboard
- Custom ship design tools
- AI-powered strategic recommendations

### Performance Optimizations
- Code splitting and lazy loading
- Virtual scrolling for large lists
- Image optimization and caching
- Service worker for offline support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the Galactic Empire game system. See the main project LICENSE for details.

---

**Galactic Empire Frontend** - Bringing the universe to your screen! 🌌✨
