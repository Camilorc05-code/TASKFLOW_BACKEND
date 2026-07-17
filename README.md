# TaskFlow Backend API

Backend REST API built with FastAPI, PostgreSQL, SQLAlchemy, JWT Authentication, Alembic, Docker, and Pytest.

---

# Features

* User registration and login
* JWT authentication
* Password hashing with bcrypt
* Protected routes
* Teams and tasks management
* Task ownership validation
* Pagination and filtering
* PostgreSQL integration
* Alembic migrations
* Docker support
* Automated tests with pytest

---

# Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Docker
* JWT (python-jose)
* Passlib + bcrypt
* Pytest

---

# Project Structure

```bash
app/
│
├── auth/
│   ├── dependencies.py
│   ├── hash.py
│   └── jwt_handler.py
│
├── db/
│   ├── database.py
│   └── dependencies.py
│
├── models/
│   ├── user.py
│   ├── team.py
│   └── task.py
│
├── routes/
│   ├── auth.py
│   ├── team.py
│   └── task.py
│
├── schemas/
│   ├── user.py
│   ├── team.py
│   └── task.py
│
├── main.py
│
tests/
│
alembic/
│
Dockerfile
docker-compose.yml
requirements.txt
.env
README.md
```

---

# Installation

## 1. Clone Repository

```bash
git https://github.com/Camilorc05-code/TASKFLOW_BACKEND
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate virtual environment:

### macOS/Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file (see `.env.example`):

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-us-west-2.pooler.supabase.com:6543/postgres
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=your_email@example.com
BREVO_SENDER_NAME=TaskFlow
APP_URL=https://taskflow-frontend-taupe.vercel.app
```

---

# Run Project

```bash
uvicorn app.main:app --reload
```

Server:

```bash
http://127.0.0.1:8000
```

Swagger Docs:

```bash
http://127.0.0.1:8000/docs
```

---

# Docker Setup

Build and run containers:

```bash
docker-compose up --build
```

---

# Database Migrations

## Create migration

```bash
alembic revision --autogenerate -m "message"
```

## Apply migration

```bash
alembic upgrade head
```

---

# Authentication

This API uses JWT authentication.

## Login

```http
POST /login
```

Example response:

```json
{
  "access_token": "your_token",
  "token_type": "bearer"
}
```

Use the token in Swagger Authorize button:

```bash
Bearer your_token
```

---

# Main Endpoints

## Auth

| Method | Endpoint  | Description   |
| ------ | --------- | ------------- |
| POST   | /register | Register user |
| POST   | /login    | Login user    |

---

## Teams

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST   | /teams/  | Create team |

---

## Tasks

| Method | Endpoint    | Description |
| ------ | ----------- | ----------- |
| POST   | /tasks/     | Create task |
| GET    | /tasks/     | List tasks  |
| GET    | /tasks/{id} | Get task    |
| PUT    | /tasks/{id} | Update task |
| DELETE | /tasks/{id} | Delete task |

---

# Testing

Run tests:

```bash
PYTHONPATH=. pytest
```

Expected result:

```bash
3 passed
```

---

# Future Improvements

* Refresh tokens
* Role-based permissions
* Email verification
* Password reset
* Redis caching
* Background tasks
* CI/CD pipelines

---

# Author

Camilo Rodriguez

GitHub:
https://github.com/TU_USUARIO
