# The webAPP - Influencer Marketing Platform

**The webAPP** is a comprehensive web application designed to connect sponsors with influencers, streamlining the process of creating and managing influencer marketing campaigns.

## Features

- User registration and authentication (Sponsors, Influencers, Admins)
- Campaign creation and management for sponsors
- Influencer search and filtering
- Ad request system for campaign collaborations
- User profiles for both sponsors and influencers
- Admin dashboard for platform management

## Tech Stack

- Backend: Flask (Python)
- Database: SQLite with SQLAlchemy ORM
- Frontend: HTMl and CSS

## Setup and Installation

1. Create and activate a virtual environment:
   ```python
   python -m venv venv
   source venv/bin/activate  
   
   # On Windows, use `venv\Scripts\activate`
   ```

2. Install the required packages:
   ```python
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```python
   python3 database-reset.py
   ```
    This script drops all existing tables and recreates them, effectively resetting the database to its initial state.

4. Create an admin user:
   ```python
   flask create-admin
   ```

5. Run the application:
   ```python
   flask run
   ```
   or
   ```python
   python3 app.py
   ```

6. Access the application at `http://localhost:5000`

## Important Files

- `app.py`: Main application file containing routes and app configuration
- `models.py`: Database models for Users, Sponsors, Influencers, Campaigns, etc.
- `commands.py`: Custom Flask CLI command to create admin
- `database-reset.py`: Script to reset the database

## Custom Commands

### flask create-admin

This command creates an admin user in the database. It's defined in `commands.py` and can be run using:

```
flask create-admin
```

The command checks if an admin user already exists. If not, it creates a new admin user with predefined credentials.

## Database Reset

To reset the database, run:

```
python database-reset.py
```

This script drops all existing tables and recreates them, effectively resetting the database to its initial state.

