# TaskFlow Backend API

REST API para la aplicación de gestión de tareas TaskFlow. FastAPI + PostgreSQL + SQLAlchemy.

---

# Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL (Supabase)
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
├── auth/
│   ├── dependencies.py
│   ├── hash.py
│   └── jwt_handler.py
├── db/
│   ├── database.py
│   └── dependencies.py
├── models/
│   ├── user.py
│   ├── team_member.py
│   ├── task.py
│   └── backlog.py
├── routes/
│   ├── auth.py
│   ├── team.py
│   ├── task.py
│   └── backlog.py
├── schemas/
│   ├── user.py
│   ├── team.py
│   ├── task.py
│   └── backlog.py
├── main.py
tests/
alembic/
Dockerfile
docker-compose.yml
requirements.txt
.env.example
```

---

# Instalación

```bash
git clone https://github.com/Camilorc05-code/TASKFLOW_BACKEND
cd TASKFLOW_BACKEND
python -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

---

# Variables de entorno

Crear un archivo `.env` (ver `.env.example`):

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

# Ejecutar

```bash
uvicorn app.main:app --reload
```

http://127.0.0.1:8000/docs

---

# Docker

```bash
docker-compose up --build
```

---

# Migraciones

```bash
alembic revision --autogenerate -m "mensaje"
alembic upgrade head
```

---

# Endpoints

| Method | Endpoint            | Descripción         |
| ------ | ------------------- | ------------------- |
| POST   | /register           | Registrar usuario   |
| POST   | /login              | Login               |
| POST   | /change-password    | Cambiar contraseña  |
| POST   | /reset-password/*   | Reset de contraseña |
| PUT    | /users/me           | Actualizar perfil   |
| POST   | /teams/             | Crear equipo        |
| GET    | /teams/             | Listar equipos      |
| DELETE | /teams/{id}         | Eliminar equipo     |
| POST   | /tasks/             | Crear tarea         |
| GET    | /tasks/             | Listar tareas       |
| PUT    | /tasks/{id}         | Actualizar tarea    |
| DELETE | /tasks/{id}         | Eliminar tarea      |
| POST   | /backlog/sprints    | Crear sprint        |
| GET    | /backlog/sprints    | Listar sprints      |
| POST   | /backlog/items      | Crear item backlog  |
| GET    | /backlog/calendar   | Eventos calendario  |

---

# Testing

```bash
PYTHONPATH=. pytest
```

---

# Autor

Camilo Rodriguez

https://github.com/Camilorc05-code
