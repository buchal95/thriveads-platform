# 🚀 ThriveAds Platform

> **Meta advertising analytics platform for displaying client advertising results and performance metrics**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Meta API](https://img.shields.io/badge/Meta_API-1877F2?style=for-the-badge&logo=meta&logoColor=white)](https://developers.facebook.com/docs/marketing-api/)

## ✨ Features

- 📊 **Real-time Meta advertising analytics** with ROAS calculations
- 📈 **Week-on-week performance comparisons** (Monday-Sunday periods)
- 🎯 **Top 10 best performing ads** with clickable Facebook links
- 💰 **Multi-currency support** pulled directly from Meta API
- 🔄 **Conversion funnel visualization** for complete customer journey
- 🎛️ **Attribution switching** (default vs 7d click attribution)
- 🇨🇿 **Czech language interface** with localized formatting
- ⚡ **Performance optimized** with pre-calculated weekly/monthly aggregations
- 🗄️ **Forever data retention** - historical data never deleted

## 🏗️ Architecture

**Monorepo structure with modern deployment:**

```
thriveads-platform/
├── 🎨 thriveads-client-platform/    # Next.js frontend → Vercel
├── 🐍 thriveads-backend/            # FastAPI backend → Railway
├── 📚 docs/                         # Documentation
├── 🛠️ setup-dev.sh                  # Development setup script
└── 📋 README.md                     # This file
```

## 🛠️ Tech Stack

### Frontend (Vercel)
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui components
- **Charts**: Recharts for performance visualizations
- **State Management**: React Query for API state
- **Deployment**: Automatic deployment from GitHub

### Backend (Railway)
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Integration**: Meta Marketing API v18.0
- **Data Processing**: Pandas + NumPy for analytics
- **Migrations**: Alembic for database versioning
- **Logging**: Structured JSON logging

### Database Design
- **Daily metrics storage** (kept forever)
- **Pre-calculated weekly/monthly aggregations** for performance
- **Strategic indexes** for fast ROAS-based queries
- **Data sync tracking** with error handling and retry logic

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/buchal95/thriveads-platform.git
cd thriveads-platform
chmod +x setup-dev.sh
./setup-dev.sh
```

### 2. Configure Meta API
```bash
# Edit backend environment
nano thriveads-backend/.env

# Add your Meta credentials:
META_ACCESS_TOKEN=your_long_lived_access_token
DEFAULT_CLIENT_ID=your_meta_ad_account_id
```

### 3. Setup Database
```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb thriveads

# Run migrations
cd thriveads-backend
source venv/bin/activate
alembic upgrade head
python seed_database.py
```

### 4. Start Development Servers
```bash
# Backend (Terminal 1)
cd thriveads-backend
source venv/bin/activate
uvicorn main:app --reload

# Frontend (Terminal 2)
cd thriveads-client-platform
npm run dev
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin**: Use your preferred PostgreSQL client

## 📊 API Endpoints

### Core Analytics
- `GET /api/v1/ads/top-performing` - Top performing ads by ROAS
- `GET /api/v1/campaigns/top-performing` - Best campaigns overview
- `GET /api/v1/metrics/funnel` - Conversion funnel data
- `GET /api/v1/metrics/week-on-week` - Performance comparisons

### Client Management
- `GET /api/v1/clients/` - List all clients
- `GET /api/v1/clients/{client_id}` - Client details

### Example Response
```json
{
  "id": "120218615280550704",
  "name": "28-1-2025 - gen-prelepka-3",
  "campaign_name": "HB - DABA - 21-1-2025",
  "metrics": {
    "impressions": 2317,
    "clicks": 84,
    "spend": "259.91",
    "conversions": 3,
    "conversion_value": "6680.79",
    "roas": 25.704243776691932
  },
  "currency": "CZK"
}
```

## 🔧 Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=ThriveAds Platform
```

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://username@localhost:5432/thriveads

# Meta API Configuration
META_ACCESS_TOKEN=your_long_lived_access_token
META_API_VERSION=v18.0

# Application Settings
ENVIRONMENT=development
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000", "https://your-domain.vercel.app"]

# Client Configuration
DEFAULT_CLIENT_ID=513010266454814  # Mimilátky CZ
```

## 🚀 Deployment

### Automatic Deployment
- **Frontend**: Vercel automatically deploys from `main` branch
- **Backend**: Railway automatically deploys from `main` branch
- **Database**: Railway PostgreSQL addon

### Manual Deployment

#### Vercel (Frontend)
```bash
cd thriveads-client-platform
npm run build
vercel --prod
```

#### Railway (Backend)
```bash
# Connect to Railway
railway login
railway link
railway up
```

## 📈 Database Schema

### Core Tables
- **clients** - Client information and Meta API credentials
- **campaigns** - Meta campaign data
- **ads** - Individual ad performance data
- **ad_metrics** - Daily performance metrics (kept forever)

### Aggregation Tables (Performance Optimized)
- **weekly_ad_metrics** - Pre-calculated weekly summaries
- **monthly_ad_metrics** - Pre-calculated monthly summaries
- **data_sync_log** - API sync tracking and error handling

### Key Features
- **Strategic indexes** for fast ROAS-based queries
- **Composite primary keys** for efficient lookups
- **Forever data retention** - no automatic deletion
- **Czech localization** - language, currency, timezone defaults

## 🧪 Testing

### Backend Tests
```bash
cd thriveads-backend
source venv/bin/activate
pytest test_main.py -v
```

### Frontend Tests
```bash
cd thriveads-client-platform
npm test
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running backend
- **Database Schema**: See `thriveads-backend/alembic/versions/`
- **Setup Guide**: Run `./setup-dev.sh` for automated setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is private and proprietary to ThriveAds Platform.

## 🎯 Roadmap

- [ ] Complete conversion funnel visualization
- [ ] Implement real-time week-on-week comparisons
- [ ] Add automated data aggregation scheduling
- [ ] Multi-client dashboard support
- [ ] Advanced attribution modeling
- [ ] Custom date range selections
- [ ] Export functionality (PDF/Excel reports)

## 📞 Support

For support and questions, please contact the development team.

---

**Built with ❤️ for Meta advertising specialists**
```
