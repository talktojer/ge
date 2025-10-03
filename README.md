# Galactic Empire - Modern Web Port

A modern web-based port of the classic Galactic Empire BBS door game, built with FastAPI, React, and PostgreSQL.

## 🎮 Game Overview

Galactic Empire is a space exploration and conquest game where players:
- Command ships across a vast galaxy
- Colonize and manage planets
- Engage in tactical space combat
- Form alliances and compete for dominance
- Build economic empires through trade and production

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Production Deployment

1. Clone the repository:
```bash
git clone <repository-url>
cd galactic-empire
```

2. Set up environment variables:
```bash
cp env.prod.example .env.prod
# Edit .env.prod with your production values
```

3. Deploy:
```bash
./deploy.sh
```

4. Access the game:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

## 🏗️ Architecture

### Backend (FastAPI)
- **Core Game Engine**: Real-time tick system, movement physics, combat mechanics
- **Database Models**: User accounts, ships, planets, teams, communications
- **API Endpoints**: RESTful API with WebSocket support for real-time features
- **Game Services**: Ship operations, planetary management, combat systems
- **Configuration System**: Dynamic game balance and configuration management

### Frontend (React)
- **Modern UI**: Responsive design with TypeScript and styled-components
- **Real-time Updates**: WebSocket integration for live game state
- **Game Interface**: Ship controls, tactical displays, galaxy map
- **State Management**: Redux Toolkit for complex game state

### Infrastructure
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis for session management and caching
- **Reverse Proxy**: Nginx with load balancing and SSL termination
- **Monitoring**: Prometheus and Grafana for metrics and dashboards
- **Background Tasks**: Celery for game tick processing and maintenance

## 🎯 Key Features

### Core Game Systems ✅
- Real-time tick system with configurable intervals
- Coordinate system with sector-based galaxy map
- Ship movement physics with warp and impulse drives
- User management with authentication and authorization

### Ship Systems ✅
- 12 ship classes from Interceptor to Flagship, plus Cyborg and Droid
- Navigation commands (warp, impulse, rotate, stop)
- Shield management with multiple shield types
- Cloaking system with energy requirements
- Cargo management with weight calculations

### Combat Systems ✅
- Phaser weapons (regular and hyper-phasers)
- Torpedo system with lock-on and tracking
- Missile system with enhanced tracking
- Ion cannon system for specialized attacks
- Decoy and jammer systems for countermeasures
- Mine laying and detection system

### Planetary Systems ✅
- Planet colonization with environment and resource factors
- Economic system with production and trading
- Planetary defense with troops, fighters, and ion cannons
- Tax system and population management
- Team trading with alliance support

### Communication Systems ✅
- In-game mail system with database integration
- Distress call system with team notifications
- Team communication channels
- Beacon system for sector-wide messaging
- Spy system for intelligence gathering

### Advanced Features ✅
- Wormhole navigation system
- Mine field systems with multiple mine types
- Zipper weapon for mine field disruption
- Combat AI for Cyborg and Droid ships
- Tactical displays with real-time scanner integration

### Game Balance & Configuration ✅
- Dynamic configuration system with real-time updates
- Original scoring formulas with kill/planet/team scoring
- Ship class point values from original game
- Energy consumption and weapon damage balancing
- Economic factor adjustments

### Production Infrastructure ✅
- Docker containerization with multi-stage builds
- Nginx reverse proxy with SSL support
- Prometheus and Grafana monitoring
- Redis caching system
- Celery background task processing
- Automated deployment scripts

## 🔧 Development

### Local Development Setup

1. Install dependencies:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

2. Set up database:
```bash
# Start PostgreSQL
docker run -d --name ge-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15

# Run migrations
cd backend
alembic upgrade head
```

3. Start development servers:
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm start
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 Monitoring

### Grafana Dashboards
- Game metrics (active players, game ticks, API response times)
- System metrics (database connections, error rates)
- Custom dashboards for game-specific monitoring

### Prometheus Metrics
- Application metrics (request counts, response times, error rates)
- Game-specific metrics (active players, game ticks, ship counts)
- System metrics (CPU, memory, disk usage)

## 🎮 Game Commands

### Navigation
- `navigate <sector_x> <sector_y>` - Navigate to specific sector
- `jettison [ALL/<number>] [item_type]` - Jettison cargo
- `maintenance [planet_id]` - Request ship maintenance
- `new <type> <class>` - Purchase new equipment
- `sell <quantity> <item_type>` - Sell goods back to Zygor

### Communication
- `freq <channel> [frequency/hail]` - Set communication frequency
- `who [all]` - List online players
- `send <channel> <message>` - Send message

### Ship Operations
- `warp <speed> [heading]` - Engage warp drive
- `impulse <speed> [heading]` - Engage impulse engines
- `rotate <heading>` - Rotate ship heading
- `shield [up/down]` - Control shields
- `cloak [on/off]` - Control cloaking system

### Combat
- `phaser <direction> [spread]` - Fire phasers
- `torpedo [target/@]` - Fire torpedo
- `missile [target/@] [energy]` - Fire missile
- `decoy` - Deploy decoy
- `jammer` - Launch jammer
- `mine [time]` - Lay mine

### Planetary Management
- `admin` - Planet administration menu
- `attack [number] [tro/fig]` - Attack planet
- `buy [number] [item_type] [password]` - Buy goods
- `transfer [up/down] [number] [item_type]` - Transfer cargo
- `orbit [planet_number]` - Enter planet orbit

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Rate limiting and DDoS protection
- SQL injection prevention
- XSS protection
- CSRF protection

## 📈 Performance

- Redis caching for frequently accessed data
- Database query optimization
- Connection pooling
- Gzip compression
- CDN-ready static file serving
- Horizontal scaling support

## 🚀 Deployment

### Production Checklist

- [ ] Update all default passwords in `.env.prod`
- [ ] Configure SSL certificates for HTTPS
- [ ] Set up proper firewall rules
- [ ] Configure backup strategies
- [ ] Set up monitoring alerts
- [ ] Test disaster recovery procedures
- [ ] Configure log rotation
- [ ] Set up health checks

### Scaling Considerations

- Use multiple backend instances behind load balancer
- Implement database read replicas for heavy read workloads
- Use Redis cluster for high availability
- Consider Kubernetes for container orchestration
- Implement horizontal pod autoscaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original Galactic Empire by Mike Murdock
- Modern port by the development team
- Community contributors and testers

## 📞 Support

- Documentation: [Wiki](link-to-wiki)
- Issues: [GitHub Issues](link-to-issues)
- Discord: [Community Server](link-to-discord)
- Email: support@galacticempire.game

---

**Galactic Empire** - Where the stars are your playground! 🌟
