# 📝 Blog API (FastAPI + PostgresSQL + Celery + Redis + Async SQLAlchemy)

A fully asynchronous, production-ready Blog API built with **FastAPI**, **SQLAlchemy**, and **PostgresSQL**, featuring authentication, email verification, blog posts, comments, reactions, and a social friends system.  
Designed with clean architecture, type safety, and modern async patterns.

---

## 🚀 Features

### 🧠 Core
- Full **CRUD** operations for blogs  
- Async **SQLAlchemy ORM** with PostgresSQL  
- Authentication with **JWT tokens**  
- Role-based access control (Admin/User)  
- Secure password hashing with `bcrypt`

### 💬 Social Features
- Friend requests (send, accept, decline, cancel)  
- Comment system with nested comments  
- Like/Dislike system for blogs  
- User profiles and relationships  

### 📧 Email & Background Tasks
- Email verification system using **Celery + Redis**  
- Async email sending with **FastAPI-Mail**  
- Token-based verification links  
- Configurable task queues for background jobs  

### 🛠️ Developer Features
- **Alembic** migrations for schema management  
- Modular folder structure  
- `.env` configuration  
- Fully asynchronous backend  

---

## 🧩 Tech Stack

| Category       | Technology         |
|----------------|--------------------|
| Framework      | FastAPI            |
| Database       | PostgresSQL        |
| ORM            | SQLAlchemy (async) |
| Auth           | JWT (python-jose)  |
| Passwords      | Passlib + bcrypt   |
| Migrations     | Alembic            |
| Env Management | python-dotenv      |
| Task Queue     | Celery + Redis     |
| Email          | FastAPI-Mail       |
| Validation     | Pydantic v2        |

---

## 📁 Project Structure

```
📂 Project Structure

blog_app/
├── 📁 app/
│   ├── 📁 alembic/
│   ├── 📁 api/
│   │   ├── 📁 routes/
│   │   │   ├── 📁 utils/
│   │   │   │   ├── 📄 __init__.py
│   │   │   │   ├── 📄 blog_utils_v1.py
│   │   │   │   ├── 📄 blog_utils_v2.py
│   │   │   │   └── 📄 security_utils.py
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 auth.py
│   │   │   ├── 📄 blogs_v1.py
│   │   │   ├── 📄 blogs_v2.py
│   │   │   └── 📄 friends_v2.py
│   │   ├── 📄 __init__.py
│   │   └── 📄 main.py
│   ├── 📁 core/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 database.py
│   │   └── 📄 security.py
│   ├── 📄 __init__.py
│   ├── 📄 main.py
│   ├── 📄 models.py
│   └── 📄 schemas.py
├── 📁 venv/
├── ⚙️ .env
├── ⚙️ .gitignore
├── 📄 __init__.py
├── ⚙️ alembic.ini
├── 🐍 celery_app.py
├── 🐍 celery_tasks.py
├── 🐍 email_config.py
├── 📘 README.md
└── 📦 requirements.txt

```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/faizuet/blog_app.git
cd blog_app
```

### 2️⃣ Create & activate a virtual environment
```bash
python -m venv venv
source venv/Scripts/activate  # on Windows
source venv/bin/activate      # on Mac/Linux
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Configure environment variables
Create a `.env` file in the root directory:

```env
DB_USER=bloguser
DB_PASSWORD=user321
DB_HOST=localhost
DB_PORT=5432
DB_NAME=blog_app

JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email settings
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_password
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_TLS=True
MAIL_SSL=False

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
BASE_URL=http://127.0.0.1:8000
```

---

### 5️⃣ Run Redis (make sure Redis is running)
```bash
redis-server
```

### 6️⃣ Run database migrations
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 7️⃣ Start the FastAPI app
```bash
uvicorn app.main:app --reload
```

### 8️⃣ Start the Celery worker
```bash
celery -A celery_app.celery_app worker --loglevel=debug -Q emails,celery -P solo
```

---

## 📬 Email Verification Flow

1. User signs up using `/auth/signup`.  
2. Celery sends an email containing a verification link (`/auth/verify-email?token=...`).  
3. When the user clicks the link:  
   - The token is verified.  
   - User’s `is_verified` flag is updated in the database.  
   - Response: `"Email verified successfully"`.  
4. (Optional) You can add a resend verification route for unverified users.

---

## 🔄 Alembic Migration Commands

| Command                                     | Description                  |
|---------------------------------------------|------------------------------|
| `alembic init app/alembic`                  | Initialize migrations folder |
| `alembic revision --autogenerate -m "desc"` | Create new migration         |
| `alembic upgrade head`                      | Apply migrations             |

---

## 🧠 Future Enhancements (AI Integration Ideas)

- Smart blog tag generation using NLP  
- AI-powered friend suggestions  
- Comment sentiment analysis  
- Auto content moderation  

---

## 🧑‍💻 Author

**Muhammad Faiz**  
Backend Software Engineer | Python, FastAPI, Flask, MySQL, Docker, Git & GitHub | AI & Deep Learning Enthusiast  

---

## 📜 License

MIT License © 2025
