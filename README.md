# 📝 Blog App (FastAPI + MySQL)

A clean practice backend project built with **FastAPI** and **MySQL**, featuring:

- 🔐 **JWT Authentication**  
- 👥 **Role-based access**:  
  - **Writer** → can create & read blogs  
  - **Reader** → can only read blogs  
- 📰 **Blog management** (CRUD for writers, read-only for readers)  
- ⚡ **Alembic migrations** for database schema  
- 🗂️ Modular and professional project structure  

---

## 🚀 Tech Stack
- **FastAPI** – web framework  
- **MySQL** – database  
- **SQLAlchemy** – ORM  
- **Alembic** – migrations  
- **Pydantic** – request/response validation  
- **Uvicorn** – ASGI server  

---

## 📂 Project Structure
```
my_blog_app/
└── blog_app/
    ├── app/
    │   ├── alembic/           # Database migrations
    │   │   ├── versions/      
    │   │   ├── env.py
    │   │   └── script.py.mako
    │   │
    │   ├── api/               # API routes
    │   │   ├── auth.py        # Authentication (signup/login)
    │   │   └── blog.py        # Blog CRUD routes
    │   │
    │   ├── core/              # Core utilities
    │   │   ├── database.py    # DB session/engine
    │   │   └── security.py    # JWT & password hashing
    │   │
    │   ├── main.py            # FastAPI entry point
    │   ├── models.py          # SQLAlchemy models
    │   └── schemas.py         # Pydantic schemas
    │
    ├── .env                   # Environment variables
    ├── alembic.ini            # Alembic config
    └── requirements.txt       # Dependencies
```

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone <https://github.com/faizuet/Blogger_writing_app.git>
   cd my_blog_app/blog_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure `.env`**
   ```env
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   DB_USER=bloguser
   DB_PASSWORD=user321
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=blog_app
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🔑 API Overview

### Auth
- `POST /auth/signup` → Register new user  
- `POST /auth/login` → Login & get JWT  

### Blogs
- `POST /blogs/` → Create blog (writers only)  
- `GET /blogs/` → Get all blogs  
- `GET /blogs/{id}` → Get blog by ID  

---

## 🛠️ Notes
- Database: **MySQL**  
- Use **Alembic** for schema changes:  
  ```bash
  alembic revision --autogenerate -m "message"
  alembic upgrade head
  ```
- Default roles:  
  - **reader** (default)  
  - **writer** (set during signup)  

