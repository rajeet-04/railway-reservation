# Railway Reservation System 🚂

A modern, full-stack railway reservation system with Next.js frontend, FastAPI backend, and Supabase (PostgreSQL) database.

![Light Theme](https://github.com/user-attachments/assets/5a60ae41-c892-4a91-8d10-c30899d3216f)
![Dark Theme](https://github.com/user-attachments/assets/4ac37872-ec20-4c2f-b1a3-38d7c2cd4ccb)

## ✨ Features

### Frontend
- ✅ **Modern UI**: Built with Next.js 14 and TypeScript
- ✅ **Responsive Design**: Mobile-first approach with Tailwind CSS
- ✅ **Theme Support**: Dark/Light/System themes with smooth transitions
- ✅ **Animations**: Framer Motion for smooth, engaging animations
- ✅ **Real-time Search**: Fast station and train search with autocomplete
- ✅ **Booking System**: Complete booking flow from search to confirmation

### Backend
- ✅ **FastAPI**: Modern, fast Python web framework
- ✅ **Authentication**: JWT-based authentication with password hashing
- ✅ **RESTful API**: Clean, documented API endpoints
- ✅ **Supabase Integration**: PostgreSQL database with Row Level Security
- ✅ **Type Safety**: Pydantic models for validation

### Database
- ✅ **8,990 Railway Stations**: Complete coverage with GPS coordinates
- ✅ **5,208 Trains**: Full route and schedule information
- ✅ **417,080+ Train Stops**: Detailed timetables
- ✅ **Optimized Queries**: Indexed for fast search performance
- ✅ **Data Migration**: Automated script to transfer JSON to Supabase

## 🚀 Quick Start

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Prerequisites
- Node.js 18+
- Python 3.10+
- Supabase account

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/rajeet-04/railway-reservation.git
cd railway-reservation
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. **Setup Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
```

4. **Migrate Data to Supabase**
```bash
cd scripts
export SUPABASE_URL="your_url"
export SUPABASE_SERVICE_KEY="your_key"
python migrate_to_supabase.py
```

5. **Run the Application**
```bash
# Terminal 1 - Backend
cd backend
python -m app.main

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit http://localhost:3000 to see the app!

## 📁 Project Structure

```
railway-reservation/
├── frontend/              # Next.js frontend
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # API client and utilities
│   └── package.json
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── schemas/     # Pydantic models
│   │   ├── config.py    # Settings
│   │   ├── database.py  # Supabase connection
│   │   └── main.py      # FastAPI app
│   └── requirements.txt
├── database/
│   ├── supabase_schema.sql  # PostgreSQL schema
│   └── railway.db           # SQLite backup
├── scripts/
│   └── migrate_to_supabase.py  # Data migration
└── data/                # Source JSON files
    ├── stations.json
    ├── trains.json
    └── schedules.json
```

## 🎨 Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion & GSAP
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Theme**: next-themes (Dark/Light/System)
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT with passlib
- **Validation**: Pydantic
- **CORS**: FastAPI middleware

### Database
- **Primary**: Supabase (PostgreSQL)
- **Backup**: SQLite (87.5 MB)
- **ORM**: Supabase Python SDK
- **Security**: Row Level Security (RLS)

## 📊 API Endpoints

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

API Documentation: http://localhost:8000/docs

## 🎯 Database Statistics

- **Stations**: 8,990 (96.7% with GPS coordinates)
- **Trains**: 5,208 with complete routes
- **Train Stops**: 417,080+ scheduled stops
- **Database Size**: 87.5 MB (SQLite backup)
- **Migration Time**: ~5-10 minutes to Supabase

## 🔧 Development

### Running Backend
```bash
cd backend
source venv/bin/activate
python -m app.main
# Or with auto-reload:
uvicorn app.main:app --reload
```

### Running Frontend
```bash
cd frontend
npm run dev
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build
npm start

# Backend
cd backend
uvicorn app.main:app --workers 4
```

## 📝 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License

## 🙏 Acknowledgments

- Data sourced from Indian Railways
- Built with Next.js, FastAPI, and Supabase

## �� Support

For issues or questions, please open an issue on GitHub.

---

**Made with ❤️ for railway travelers**
