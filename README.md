# Image Upload Application

A full-stack application with Next.js frontend and FastAPI backend for image uploading.

## Project Structure

```
.
├── frontend/     # Next.js frontend application
└── backend/      # FastAPI backend application
```

## Backend Setup

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server:
```bash
uvicorn app.main:app --reload
```

The backend will be available at http://localhost:8000

## Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Install shadcn/ui:
```bash
npx shadcn-ui@latest init
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## API Endpoints

- `POST /api/upload` - Upload an image file
- `GET /` - Health check endpoint

## Features

- Modern Next.js 14 frontend with App Router
- Tailwind CSS for styling
- shadcn/ui components
- FastAPI backend with image upload support
- CORS configuration for local development 

## TODO
- Add a database
- Add a way to store the uploaded images
- Add a way to store the user's uploads
- Add a way to store the user's profile information
- Add a way to store the user's settings