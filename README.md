# POIHS Project

This folder contains a ready-to-upload project for your bar inventory system.

## What is inside
- `backend/` = the API and database code
- `frontend/` = the phone-friendly web app

## Before you start
You need these installed on your computer:
1. PostgreSQL
2. Python 3.11+
3. Node.js 18+
4. Git (optional, but helpful)

## Easy setup

### 1. Put the project on your computer
Unzip the folder and open it.

### 2. Create the database
Open a terminal and go into the backend folder.

Mac/Linux:
```bash
cd backend
python3 scripts/setup.py
```

Windows:
```bash
cd backend
python scripts/setup.py
```

This script will:
- check PostgreSQL
- create the database
- load the schema
- create a Python virtual environment
- install backend packages

### 3. Start the backend
Mac/Linux:
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Windows:
```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```

The backend should now run at:
- `http://localhost:8000`
- docs at `http://localhost:8000/docs`

### 4. Start the frontend
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
```

The frontend should now run at:
- `http://localhost:3000`

## Upload to GitHub
1. Create a new empty repository on GitHub.
2. Drag this whole project folder into GitHub Desktop, or upload the files through the GitHub website.
3. Commit the files.
4. Push to GitHub.

## Important note
Some files use placeholder IDs and sample assumptions so you can get the app running first. The next step after startup is connecting your real product data, recipes, and Toast mappings.
