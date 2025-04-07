# Arbitrator Investigation Tool

A Flask web application that allows users to browse and investigate arbitrators.

## Features

- View list of available arbitrators
- See detailed information about each arbitrator
- Modern, responsive UI using Tailwind CSS
- SQLite database for data storage

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python seed_data.py
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `app.py`: Main Flask application
- `templates/index.html`: Frontend template
- `seed_data.py`: Script to populate database with sample data
- `arbitrators.db`: SQLite database (created automatically)

## Technology Stack

- Backend: Flask + SQLAlchemy
- Frontend: HTML + JavaScript + Tailwind CSS
- Database: SQLite 