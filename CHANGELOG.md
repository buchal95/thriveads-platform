# Changelog

All notable changes to ThriveAds Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Complete conversion funnel visualization
- Real-time week-on-week comparisons
- Automated data aggregation scheduling
- Multi-client dashboard support
- Advanced attribution modeling
- Custom date range selections
- Export functionality (PDF/Excel reports)

## [1.0.0] - 2025-01-23

### Added
- **Complete database schema** with PostgreSQL
  - 10 tables with strategic performance indexes
  - Forever data retention policy
  - Pre-calculated weekly/monthly aggregations
  - Data sync tracking and error handling
- **FastAPI backend** with async support
  - Meta Marketing API v18.0 integration
  - ROAS-based performance ranking
  - Czech language and currency support
  - Structured JSON logging
- **Core API endpoints**
  - `GET /api/v1/ads/top-performing` - Top performing ads by ROAS
  - `GET /api/v1/clients/` - Client management
  - `GET /api/v1/metrics/week-on-week` - Performance comparisons
  - `GET /health` - Health check endpoint
- **Next.js frontend structure**
  - TypeScript configuration
  - Tailwind CSS setup
  - Shadcn/ui components ready
- **Development infrastructure**
  - Automated setup script (`setup-dev.sh`)
  - Alembic database migrations
  - Docker configuration for Railway deployment
  - Comprehensive documentation

### Database Schema
- **clients** - Client information with Meta API credentials
- **campaigns** - Meta campaign data storage
- **ads** - Individual ad performance tracking
- **ad_metrics** - Daily performance metrics (kept forever)
- **campaign_metrics** - Daily campaign aggregations
- **weekly_ad_metrics** - Pre-calculated weekly summaries
- **monthly_ad_metrics** - Pre-calculated monthly summaries
- **weekly_campaign_metrics** - Weekly campaign aggregations
- **monthly_campaign_metrics** - Monthly campaign aggregations
- **data_sync_log** - API synchronization tracking

### Performance Optimizations
- 14 strategic database indexes for fast queries
- ROAS-based sorting optimization
- Date range query optimization
- Composite primary keys for efficient lookups

### Client Configuration
- **Mimilátky CZ** pre-configured (ID: 513010266454814)
- Czech language defaults (cs)
- Czech Republic country setting (CZ)
- Czech Koruna currency (CZK)
- Europe/Prague timezone

### Meta API Integration
- Real-time data fetching from Meta Marketing API
- ROAS calculation and ranking
- Monday-Sunday week period calculations
- Attribution model support (default, 7d_click)
- Multi-currency support from Meta API
- Error handling and retry logic

### Development Features
- Monorepo architecture
- Automated PostgreSQL setup
- Database seeding with client data
- Comprehensive test suite
- API documentation with FastAPI/OpenAPI
- Environment-based configuration

### Deployment Ready
- **Vercel** configuration for frontend deployment
- **Railway** configuration for backend deployment
- Docker containerization
- Environment variable management
- Health check endpoints
- Production logging configuration

## [0.1.0] - 2025-01-20

### Added
- Initial project structure
- Basic Next.js frontend setup
- FastAPI backend foundation
- Database design planning
- Meta API research and planning

---

## Version History

- **v1.0.0** - Full MVP with working Meta API integration
- **v0.1.0** - Initial project setup and planning

## Migration Notes

### v1.0.0
- First production release
- Requires PostgreSQL 15+
- Requires Meta API access token
- Database migrations included
- No breaking changes (initial release)

## Support

For questions about changes or upgrades, please:
1. Check the documentation
2. Review the migration notes
3. Create an issue on GitHub
4. Contact the development team

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) format for consistency and clarity.
