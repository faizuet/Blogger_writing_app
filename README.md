# 📝 Blog API (FastAPI + PostgreSQL + Async SQLAlchemy)

A fully asynchronous, production-ready Blog API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**, featuring authentication, blog posts, comments, reactions, and a social friends system. Designed with clean architecture, type safety, and modern async patterns.

---

## 🚀 Features

### 🧠 Core
- Full **CRUD** operations for blogs
- Async **SQLAlchemy ORM** with PostgreSQL
- Authentication with **JWT tokens**
- Role-based access control (Admin/User)
- Secure password hashing with `bcrypt`

### 💬 Social Features
- Friend requests (send, accept, decline, cancel)
- Comment system with nested comments
- Like/Dislike system for blogs
- User profiles and relationships

### 🛠️ Developer Features
- **Alembic** migrations for schema management
- Modular folder structure
- `.env` configuration
- Fully asynchronous backend

---

## 🧩 Tech Stack

| Category | Technology |
|-----------|-------------|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy (async) |
| Auth | JWT (python-jose) |
| Passwords | Passlib + bcrypt |
| Migrations | Alembic |
| Env Management | python-dotenv |
| Validation | Pydantic v2 |

---

## 📁 Project Structure

```
my_blog_app/
└── blog_app
    └── app
        ├── alembic/
        ├── api/
        │   └── routes/
        │       ├── __init__.py
        │       ├── auth.py
        │       ├── blog_utils_v1.py
        │       ├── blog_utils_v2.py
        │       ├── blogs_v1.py
        │       ├── blogs_v2.py
        │       ├── friends_v2.py
        │       └── security_utils.py
        ├── __init__.py
        └── main.py
    ├── core/
    │   ├── __init__.py
    │   ├── database.py
    │   └── security.py
    ├── __init__.py
    ├── main.py
    ├── models.py
    └── schemas.py
venv/
.env
.gitignore
alembic.ini
README.md
requirements.txt

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
```

### 5️⃣ Run database migrations
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 6️⃣ Start the development server
```bash
uvicorn app.main:app --reload
```

### 7️⃣ Open in browser
Go to 👉 **http://127.0.0.1:8000/docs**

---

## 🔄 Alembic Migration Commands

| Command | Description |
|----------|--------------|
| `alembic init app/alembic` | Initialize migrations folder |
| `alembic revision --autogenerate -m "desc"` | Create new migration |
| `alembic upgrade head` | Apply migrations |

---

## 🧠 Future Enhancements (AI Integration Ideas)

- Smart blog tag generation using NLP
- AI-powered friend suggestions
- Comment sentiment analysis
- Auto content moderation

---

## 🧑‍💻 Author

**Muhammad Faiz**  
Backend Software Engineer | Python, FastAPI, Flask, MySQL, Docker, Git & Github | AI & Deep Learning Enthusiast

---

## 📜 License

MIT License © 2025
