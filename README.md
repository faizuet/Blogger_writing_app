# 📝 Blog App (FastAPI + MySQL)

A fully **async backend application** built with **FastAPI** and **MySQL**, featuring **role-based access**, **blogs**, **comments**, **reactions**, and **enhanced metadata** in V2. Designed for **high performance, scalability**, and **modern async practices**.

---

## 🌟 Features

### 1. **Authentication & Authorization**

* **JWT Authentication** – secure login and access.
* **Role-based access**:

  * **Reader** → Read blogs, view/add comments, react.
  * **Writer** → CRUD own blogs, add comments, react.
  * **Admin** → CRUD any blog, comment, or reaction.

---

### 2. **Blogs V1 vs V2 Comparison**

| Feature               | V1             | V2                                             |
| --------------------- | -------------- | ---------------------------------------------- |
| CRUD                  | ✅ Writer/Admin | ✅ Writer/Admin                                 |
| Async endpoints       | ✅              | ✅                                              |
| Soft delete           | ✅              | ✅                                              |
| Timestamps            | ❌              | ✅ (`created_at`, `updated_at`)                 |
| Comments count        | ❌              | ✅                                              |
| Reaction summary      | ❌              | ✅ (per emoji & total)                          |
| Current user reaction | ❌              | ✅                                              |
| `is_owner` flag       | ❌              | ✅                                              |
| Sorting               | ❌              | ✅ (`newest`, `most_commented`, `most_reacted`) |
| Bulk endpoints        | ❌              | ✅ (`bulk-comments`, `bulk-reactions`)          |

---

### 3. **Comments**

* Add, view, and soft delete comments (`deleted=True`).
* Role-based access: Owner or admin can delete comments.
* **V2 enhancements**:

  * Async endpoints
  * `created_at` & `updated_at`
  * Owner info included
* Bulk fetching supported for multiple blogs.

---

### 4. **Reactions**

* React to blogs using emojis: 👍 Like, ❤️ Love, 😂 Haha, 😲 Wow, 😢 Sad, 😡 Angry.
* Add, update, or remove reactions.
* Role-based access: Admin → manage any reaction, Users → manage own reaction.
* **V2 enhancements**:

  * Reaction summary per emoji
  * Total reaction count
  * Current user reaction
  * Bulk fetching for multiple blogs

---

### 5. **Other Features**

* Fully **async endpoints** for all operations.
* Soft delete mechanism for blogs and comments.
* Modular project structure with helper utilities:

  * `blog_utils_v1.py` & `blog_utils_v2.py`
* Optimized queries for comment counts and reactions.
* Pydantic validation for requests/responses.
* Alembic migrations for database schema management.

---

## 🛠️ Tech Stack

* **FastAPI** – Web framework
* **MySQL** – Database
* **SQLAlchemy (Async)** – ORM
* **Alembic** – Database migrations
* **Pydantic** – Validation
* **Uvicorn** – ASGI server

---

## 📂 Project Structure

```
my_blog_app/
└── blog_app/
    ├── app/
    │   ├── alembic/
    │   │   ├── versions/
    │   │   ├── env.py
    │   │   └── script.py.mako
    │   │
    │   ├── api/
    │   │   ├── auth.py
    │   │   └── routes/
    │   │       ├── blogs_v1.py
    │   │       ├── blogs_v2.py
    │   │       ├── blog_utils_v1.py
    │   │       └── blog_utils_v2.py
    │   │
    │   ├── core/
    │   │   ├── database.py
    │   │   └── security.py
    │   │
    │   ├── main.py
    │   ├── models.py
    │   └── schemas.py
    │
    ├── .env
    ├── alembic.ini
    └── requirements.txt
```

---

## ⚡ Setup Instructions

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

## 🔗 API Overview

### Auth

* `POST /auth/signup` → Register new user
* `POST /auth/login` → Login & get JWT token

### Blogs

* V1 → CRUD (Writer/Admin), read-only for readers
* V2 → Async CRUD + metadata + bulk endpoints + sorting

### Comments

* `POST /v{1|2}/blogs/{id}/comments` → Add comment
* `GET /v{1|2}/blogs/{id}/comments` → List comments
* `DELETE /v{1|2}/blogs/{id}/comments/{comment_id}` → Soft delete comment

### Reactions

* `POST /v{1|2}/blogs/{id}/reactions` → Add or update reaction
* `GET /v{1|2}/blogs/{id}/reactions` → List reactions (V2 includes summary & current user reaction)
* `DELETE /v{1|2}/blogs/{id}/reactions` → Remove reaction (owner/admin)

### Bulk Endpoints (V2)

* `GET /v2/blogs/bulk-comments?blog_ids=...`
* `GET /v2/blogs/bulk-reactions?blog_ids=...`

---

## 💡 Notes

* **All endpoints are fully async**
* Soft delete for blogs/comments
* Default roles: `reader` (default), `writer`, `admin`
* Use Alembic for migrations:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

* V2 enhancements: metadata aggregation, sorting, bulk fetching, reaction summaries, timestamps, `is_owner` flag

