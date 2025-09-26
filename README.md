# 📝 Blog App (FastAPI + MySQL)

A clean practice backend project built with **FastAPI** and **MySQL**, featuring:

* 🔐 **JWT Authentication**
* 👥 **Role-based access**:

  * **Writer** → can create, read, update, delete blogs
  * **Reader** → can only read blogs
* 📰 **Blog management**:

  * V1: CRUD for writers, read-only for readers
  * V2: CRUD with timestamps, comment count, reaction summary, and current user reaction
* 💬 **Comment system**: readers & writers can comment on blogs
* ⚡ **Reactions**: readers & writers can react to blogs (`like`, `love`, `haha`, `wow`, `sad`, `angry`)
* 🗂️ **Modular project structure**
* 🏗️ **Alembic migrations** for database schema
* 🧪 **Postman-ready API collection** for full testing

---

## 🚀 Tech Stack

* **FastAPI** – web framework
* **MySQL** – database
* **SQLAlchemy** – ORM
* **Alembic** – migrations
* **Pydantic** – request/response validation
* **Uvicorn** – ASGI server

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
    │   │   ├── v1_blog.py     # Blog, comment & reaction routes for V1
    │   │   └── v2_blog.py     # Blog, comment & reaction routes for V2 with timestamps
    │   │
    │   ├── core/              # Core utilities
    │   │   ├── database.py    # DB session/engine
    │   │   └── security.py    # JWT & password hashing
    │   │
    │   ├── main.py            # FastAPI entry point
    │   ├── models.py          # SQLAlchemy models (User, Blog, Comment, Reaction)
    │   └── schemas.py         # Pydantic schemas (User, Blog, Comment, Reaction)
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

* `POST /auth/signup` → Register new user (role: `reader` or `writer`)
* `POST /auth/login` → Login & get JWT token

### Blogs V1

* `POST /v1/blogs/` → Create blog (writers only)
* `GET /v1/blogs/` → Get all blogs
* `GET /v1/blogs/{id}` → Get blog by ID
* `PUT /v1/blogs/{id}` → Update blog (owner only)
* `DELETE /v1/blogs/{id}` → Delete blog (owner only)

### Blogs V2

* `POST /v2/blogs/` → Create blog (writers only)
* `GET /v2/blogs/` → Get all blogs with timestamps, comment count, reaction summary
* `GET /v2/blogs/{id}` → Get blog by ID with extra metadata
* `DELETE /v2/blogs/{id}` → Delete blog (owner only)

### Comments V1 & V2

* `POST /v{1|2}/blogs/{id}/comments` → Add comment
* `GET /v{1|2}/blogs/{id}/comments` → Get all comments
* `DELETE /v{1|2}/blogs/{id}/comments/{comment_id}` → Delete comment (owner only)

### Reactions V1 & V2

* `POST /v{1|2}/blogs/{id}/reactions` → Add or update reaction
* `GET /v{1|2}/blogs/{id}/reactions` → Get all reactions
* `DELETE /v{1|2}/blogs/{id}/reactions` → Remove your reaction

---

## 🛠️ Notes

* Database: **MySQL**

* Use **Alembic** for schema changes:

  ```bash
  alembic revision --autogenerate -m "message"
  alembic upgrade head
  ```

* Default roles:

  * **reader** (default)
  * **writer** (set during signup)

* **Reactions** allowed: `like 👍`, `love ❤️`, `haha 😂`, `wow 😲`, `sad 😢`, `angry 😡`

* **V2 Enhancements**: timestamps (`created_at`, `updated_at`), comment counts, reaction summaries, current user reaction

