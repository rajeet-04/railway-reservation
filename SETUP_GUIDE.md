# Railway Reservation System - Complete Setup Guide

## Overview

This is a full-stack railway reservation system with:
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, GSAP, and Framer Motion
- **Backend**: FastAPI with Python
- **Database**: Supabase (PostgreSQL)
- **Features**: Dark/Light/System theme, animations, complete booking system

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- Supabase account (free tier works)

## Project Structure

```
railway-reservation/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── schemas/           # Pydantic models
│   │   ├── config.py          # Settings
│   │   ├── database.py        # Supabase connection
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js app directory
│   ├── components/            # React components
│   ├── lib/                   # API client
│   └── package.json
├── database/
│   ├── supabase_schema.sql    # Supabase schema
│   └── railway.db             # SQLite backup
├── scripts/
│   └── migrate_to_supabase.py # Data migration script
└── data/                       # Source JSON files
    ├── stations.json
    ├── trains.json
    └── schedules.json
```

## Setup Instructions

### 1. Supabase Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run the schema:
   ```sql
   -- Copy and paste contents of database/supabase_schema.sql
   ```
3. Get your credentials from Project Settings > API:
   - Project URL
   - Anon/Public key
   - Service role key (for migration script)

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Supabase credentials:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=your_anon_key
# SUPABASE_SERVICE_KEY=your_service_role_key
# SECRET_KEY=your_jwt_secret_key
```

### 3. Data Migration to Supabase

```bash
# From project root
cd scripts

# Set environment variables
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_KEY="your_service_role_key"

# Or create a .env file in the project root with:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_SERVICE_KEY=your_service_role_key

# Run migration script
python migrate_to_supabase.py
```

This will transfer:
- 8,990 stations
- 5,208 trains with routes
- 417,080 train stops
- Create train runs for next 30 days

**Note**: Migration takes 5-10 minutes depending on your internet connection.

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local if backend is not on localhost:8000
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

### 5. Start Backend Server

```bash
# In backend directory with venv activated
cd backend
python -m app.main

# Or use uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

## Features

### Frontend Features
- ✅ Dark/Light/System theme support
- ✅ Animated UI with Framer Motion
- ✅ Responsive design with Tailwind CSS
- ✅ Station search with autocomplete
- ✅ Train search and booking
- ✅ User authentication
- ✅ Booking management

### Backend Features
- ✅ RESTful API with FastAPI
- ✅ JWT authentication
- ✅ Supabase PostgreSQL database
- ✅ Station and train search
- ✅ Booking management
- ✅ Row Level Security (RLS)

### Database Features
- ✅ 8,990 railway stations
- ✅ 5,208 trains with routes
- ✅ 417,080 scheduled stops
- ✅ Optimized indexes
- ✅ Referential integrity

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `GET /api/v1/auth/me` - Get current user

### Stations
- `GET /api/v1/stations` - List/search stations
- `GET /api/v1/stations/autocomplete` - Autocomplete search
- `GET /api/v1/stations/{code}` - Get station details

### Trains
- `GET /api/v1/trains` - List trains
- `GET /api/v1/trains/{number}` - Get train details
- `GET /api/v1/trains/{number}/route` - Get train route

### Search
- `GET /api/v1/search` - Search trains between stations
- `GET /api/v1/search/direct` - Search direct trains only

### Bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings` - List user bookings
- `GET /api/v1/bookings/{id}` - Get booking details
- `POST /api/v1/bookings/{id}/cancel` - Cancel booking

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
# Use gunicorn or uvicorn with workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Environment Variables

### Backend (.env)
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
SECRET_KEY=your_jwt_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

### Migration Issues
- Ensure Supabase credentials are correct
- Check internet connection
- Verify schema was created in Supabase
- Check data files exist in `data/` directory

### Backend Issues
- Ensure virtual environment is activated
- Check Python version (3.10+)
- Verify all dependencies are installed
- Check .env file has correct values

### Frontend Issues
- Clear `.next` folder and rebuild
- Check Node.js version (18+)
- Verify backend is running
- Check CORS settings

## License

[Your License Here]

## Support

For issues, please open an issue on the repository.
