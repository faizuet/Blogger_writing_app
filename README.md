# Blogger Writing App

A practice backend project built with **FastAPI** and **MySQL**, featuring:

- **User authentication** with JWT tokens  
- **Role-based access**:  
  - Writer → can read & create blogs  
  - Reader → can only read blogs  
- **Blog management** (CRUD for writers, read-only for readers)  
- **Database migrations** using Alembic  
- Clean project structure with modular APIs

---

## 🚀 Tech Stack
- **FastAPI** – web framework  
- **MySQL** – database  
- **SQLAlchemy ORM** – database interaction  
- **Alembic** – migrations  
- **Pydantic** – data validation  
- **Uvicorn** – ASGI server  

---

## 📂 Project Structure
```
Blogger_writing_app/
│
├── alembic/              # Migration scripts
│   ├── versions/         # Generated migration files
│   └── env.py            # Alembic environment config
│
├── app/
│   ├── Apis/             # API routes
│   │   ├── auth.py       # Authentication routes (login/register)
│   │   └── blog.py       # Blog routes
│   │
│   ├── models.py         # SQLAlchemy models (User, Blog)
│   ├── schema.py         # Pydantic schemas
│   ├── database.py       # Database connection & session
│   ├── security.py       # JWT and password hashing logic
│   └── main.py           # FastAPI entry point
│
├── .env                  # Environment variables
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone <your-repo-url>
   cd Blogger_writing_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate   # on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** in `.env`
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

##  API Overview

###  Auth
- `POST /auth/register` → Register new user  
- `POST /auth/login` → Login and get JWT  

###  Blogs
- `POST /blogs/` → Create blog (writer only)  
- `GET /blogs/` → Get all blogs  
- `GET /blogs/{id}` → Get blog by ID  

---

##  Features to Try
- Register a **writer** and **reader** account  
- Writer: login → create blogs → view them  
- Reader: login → view blogs only  

---

## 🛠️ Notes
- Default database: **MySQL**  
- Use **Alembic** for schema changes (`alembic revision --autogenerate -m "message"` → `alembic upgrade head`)  

