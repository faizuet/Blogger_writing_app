# Blog App (FastAPI + MySQL)

A clean backend project built with FastAPI and MySQL, featuring async endpoints for high performance and scalability. Supports role-based access, comments, reactions, and enhanced metadata in V2.

---

## Features

### Authentication & Authorization

* JWT Authentication – secure login and access
* Role-based access:

  * Reader → read blogs, comment, react
  * Writer → CRUD own blogs, comment, react
  * Admin → CRUD any blog, comment, reaction

### Blog Management

* V1: CRUD for writers, read-only for readers
* V2: Async CRUD with:

  * created_at & updated_at timestamps
  * Comments count per blog
  * Reaction summary (per emoji & total count)
  * Current user's reaction
  * is_owner flag
  * Admin privileges to manage any blog
  * Sorting by newest, most_commented, most_reacted
  * Bulk endpoints for multiple blogs:

    * GET /v2/blogs/bulk-comments → fetch all comments
    * GET /v2/blogs/bulk-reactions → fetch reactions, summary, current user reaction

### Comments

* Add, view, and delete comments
* Soft delete implemented (deleted = True)
* Admin can manage all comments
* Async endpoints with timestamps and owner info in V2

### Reactions

* React to blogs using allowed emojis: like 👍, love ❤️, haha 😂, wow 😲, sad 😢, angry 😡
* Add, update, or remove reactions
* V2 includes:

  * Total reaction count
  * Summary per emoji
  * Current user's reaction
  * Admin can manage any reaction
  * Bulk fetching for multiple blogs

### Other Features

* Modular project structure
* Alembic migrations for database schema
* Fully async endpoints for V2
* Optimized queries for comment counts & reactions
* Pydantic validation for request/response models

---

## Tech Stack

* FastAPI – Web framework
* MySQL – Database
* SQLAlchemy – ORM
* Alembic – Migrations
* Pydantic – Validation
* Uvicorn – ASGI server

---

## Project Structure

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
    │   │   ├── v1_blog.py     
    │   │   └── v2_blog.py     
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

## Setup Instructions

1. Clone the repo

```
git clone <https://github.com/faizuet/Blogger_writing_app.git>
cd my_blog_app/blog_app
```

2. Create a virtual environment

```
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Configure `.env`

```
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DB_USER=bloguser
DB_PASSWORD=user321
DB_HOST=localhost
DB_PORT=3306
DB_NAME=blog_app
```

5. Run migrations

```
alembic upgrade head
```

6. Start the server

```
uvicorn app.main:app --reload
```

---

## API Overview

### Auth

* POST /auth/signup → Register new user
* POST /auth/login → Login & get JWT token

### Blogs V1

* CRUD endpoints (writer only for create/update/delete)
* Read-only for readers

### Blogs V2

* Async CRUD endpoints with metadata
* Sorting options: newest, most_commented, most_reacted
* Bulk endpoints:

  * GET /v2/blogs/bulk-comments → Fetch comments for multiple blogs
  * GET /v2/blogs/bulk-reactions → Fetch reactions & summary for multiple blogs

### Comments V1 & V2

* POST /v{1|2}/blogs/{id}/comments → Add comment
* GET /v{1|2}/blogs/{id}/comments → List comments
* DELETE /v{1|2}/blogs/{id}/comments/{comment_id} → Soft delete comment (owner/admin)

### Reactions V1 & V2

* POST /v{1|2}/blogs/{id}/reactions → Add or update reaction
* GET /v{1|2}/blogs/{id}/reactions → Get all reactions (V2 includes summary & current user reaction)
* DELETE /v{1|2}/blogs/{id}/reactions → Remove reaction (owner/admin)

---

## Notes

* Database: MySQL
* Use Alembic for schema changes:

```
alembic revision --autogenerate -m "message"
alembic upgrade head
```

* Default roles: reader (default), writer, admin
* V2 enhancements: timestamps, comment counts, reaction summaries, current user reaction, is_owner flag, admin privileges, bulk endpoints

