"""from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

conn = psycopg2.connect(
    host='localhost',
    database='fastapi',
    user='postgres',
    password='intern',
    cursor_factory=RealDictCursor
)
cur = conn.cursor()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/form", response_class=HTMLResponse)
def show_form(request: Request, message: str = None, error: str = None):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "message": message,
        "error": error
    })

@app.post("/posts")
def create_post(request: Request, title: str = Form(...), content: str = Form(...)):
    try:
        cur.execute("INSERT INTO post (title, content) VALUES (%s, %s)", (title, content))
        conn.commit()

        return RedirectResponse(url="/form?message=Post created successfully!", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/form?error={str(e)}", status_code=303)

@app.get("/blog", response_class=HTMLResponse)
def read_blog(request: Request):
    cur.execute("SELECT * FROM post")
    posts = cur.fetchall()
    return templates.TemplateResponse("success.html", {"request": request, "posts": posts})


# Routes
@app.get("/",response_class=HTMLResponse)
def read_root(request:Request):
    return templates.TemplateResponse("form.html",{"request":request})

@app.get("/posts", response_class=HTMLResponse)
def read_posts(request: Request):
    cur.execute("SELECT * FROM post")
    posts = cur.fetchall()
    return templates.TemplateResponse("form.html", {"request": request, "posts": posts})"""

from fastapi import Depends, FastAPI, HTTPException, Request, Form,Query, Response,UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import shutil
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')
templates = Jinja2Templates(directory="templates")

conn = psycopg2.connect(
    host='localhost',
    database='fastapi',
    user='postgres',
    password='intern',
    cursor_factory=RealDictCursor
)
cur = conn.cursor()

# Login page for Admin
@app.get("/login/admin", response_class=HTMLResponse)
def login_admin(request: Request):
    return templates.TemplateResponse("login_admin.html", {"request": request})

@app.post("/login/admin")
def login_admin_post(request: Request, username: str = Form(...), password: str = Form(...)):
    cur.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    if user:
        request.session["admin_username"] = username
        return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("login_admin.html", {"request": request, "error": "Invalid credentials"})

# Login page for Author
@app.get("/login/author", response_class=HTMLResponse)
def login_author(request: Request):
    return templates.TemplateResponse("login_author.html", {"request": request})

@app.post("/login/author")
def login_author_post(request: Request, username: str = Form(...), password: str = Form(...)):
    cur.execute("SELECT * FROM authors WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    if user:
        request.session["author_username"] = username
        return RedirectResponse("/author/dashboard", status_code=302)
    return templates.TemplateResponse("login_author.html", {"request": request, "error": "Invalid credentials"})

# Login page for User
@app.get("/login/user", response_class=HTMLResponse)
def login_user(request: Request):
    return templates.TemplateResponse("login_user.html", {"request": request})

# Login POST route 
@app.post("/login/user")
def login_user_post(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        if user:
            # Save username in session or cookie - you'll need session middleware for this
            request.session["user_username"] = username
            return RedirectResponse("/user/dashboard", status_code=302)
        return templates.TemplateResponse("login_user.html", {"request": request, "error": "Invalid credentials"})
    except Exception as e:
        conn.rollback()
        print("Error executing query:", e)

# Registration page for Author
@app.get("/register/author", response_class=HTMLResponse)
def register_author(request: Request):
    return templates.TemplateResponse("register_author.html", {"request": request})

@app.post("/register/author")
def register_author_post(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    cur.execute("INSERT INTO authors (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
    conn.commit()
    return RedirectResponse("/login/author", status_code=302)

# Registration page for User
@app.get("/register/user", response_class=HTMLResponse)
def register_user(request: Request):
    return templates.TemplateResponse("register_user.html", {"request": request})

@app.post("/register/user")
def register_user_post(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error inserting user:", e)
        return HTMLResponse(f"Error adding user: {str(e)}", status_code=500)
    return RedirectResponse("/login/user", status_code=302)

# Logout route (works for all roles)
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/profile-selection", status_code=302)

@app.get("/")
def root():
    return RedirectResponse("/profile-selection")
@app.get("/profile-selection", response_class=HTMLResponse)
def profile_selection(request: Request):
    return templates.TemplateResponse("profile_selection.html", {"request": request})

# Admin Dashboard
@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    cur.execute("SELECT id, title, category,ingredients,instructions,status FROM recipes")
    recipes = cur.fetchall()
    print("Fetched recipes:", recipes) 
    return templates.TemplateResponse("dash_admin.html", {
        "request": request,
        "username": "admin",
        "recipes": recipes
    })

@app.post("/admin/delete-recipe/{recipe_id}")
def delete_recipe(recipe_id: int):
    cur.execute("DELETE FROM comments WHERE id = %s", (recipe_id,))
    cur.execute("DELETE FROM recipes WHERE id = %s", (recipe_id,))
    conn.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.get("/author/recipe/edit/{recipe_id}", response_class=HTMLResponse)
def edit_recipe_form(recipe_id: int, request: Request):
    author_id = get_logged_in_author_id(request)
    if not author_id:
        return RedirectResponse("/login/author", status_code=302)

    cur.execute("SELECT * FROM recipes WHERE id = %s AND author_id = %s", (recipe_id, author_id))
    recipe = cur.fetchone()
    if not recipe:
        return RedirectResponse("/author/dashboard", status_code=302)

    return templates.TemplateResponse("edit.html", {"request": request, "recipe": recipe})

@app.post("/author/recipe/edit/{recipe_id}")
def edit_recipe(recipe_id: int, request: Request, title: str = Form(...), category: str = Form(...), ingredients: str = Form(...), instructions: str = Form(...)):
    author_id = get_logged_in_author_id(request)
    if not author_id:
        return RedirectResponse("/login/author", status_code=302)

    # Check ownership
    cur.execute("SELECT id FROM recipes WHERE id = %s AND author_id = %s", (recipe_id, author_id))
    if not cur.fetchone():
        return RedirectResponse("/author/dashboard", status_code=302)

    cur.execute("""
        UPDATE recipes SET title=%s, category=%s, ingredients=%s, instructions=%s WHERE id=%s
    """, (title, category, ingredients, instructions, recipe_id))
    conn.commit()
    return RedirectResponse("/author/dashboard", status_code=302)

def get_logged_in_author_id(request: Request):
    username = request.session.get("author_username")
    if not username:
        return None
    cur.execute("SELECT id FROM authors WHERE username = %s", (username,))
    author = cur.fetchone()
    if not author:
        return None
    return author["id"]

@app.get("/author/recipe/add", response_class=HTMLResponse)
def add_recipe_form(request: Request):
    if not request.session.get("author_username"):
        return RedirectResponse("/login/author", status_code=302)
    return templates.TemplateResponse("add.html", {"request": request})

UPLOAD_DIR = "static/uploads"
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/author/recipe/add")
def add_recipe(
    request: Request,
    title: str = Form(...),
    category: str = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        username = request.session.get("author_username")
        if not username:
            return HTMLResponse("Session expired. Please login again.", status_code=403)

        cur.execute("SELECT id FROM authors WHERE username = %s", (username,))
        author = cur.fetchone()
        if not author:
            return HTMLResponse("Author not found in database.", status_code=404)

        # Save uploaded image
        filename = image.filename
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Store image path in DB
        image_path = f"/static/uploads/{filename}"

        # Insert into DB
        cur.execute("""
            INSERT INTO recipes (author_id, title, category, ingredients, instructions, image_path)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (author["id"], title, category, ingredients, instructions, image_path))
        
        conn.commit()
        return RedirectResponse("/author/dashboard", status_code=302)

    except Exception as e:
        conn.rollback()
        print("Error inserting recipe:", e)
        return HTMLResponse(f"Error adding recipe: {str(e)}", status_code=500)

@app.get("/user/dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request):
    if "user_username" not in request.session:
        return RedirectResponse("/login/user", status_code=302)

    # Always fetch all recipes
    query = """
        SELECT id, author_id, title, category, ingredients, instructions, created_at,image_path
        FROM recipes where status = 'approved'
        ORDER BY created_at DESC
    """
    cur.execute(query)
    recipes = cur.fetchall()

    recipes_list = [dict(recipe) for recipe in recipes]

    return templates.TemplateResponse("recipes.html", {
        "request": request,
        "username": request.session["user_username"],
        "recipes": recipes_list
    })

@app.get("/user/search", response_class=HTMLResponse)
def filter_recipe(request: Request, title:str = Query(...)):
    cur = conn.cursor()
    try:
        if "user_username" not in request.session:
            return RedirectResponse("/login/user", status_code=302)
        recipes_list = []
        if title:
            cur.execute(
                """
                SELECT id, author_id, title, category, ingredients, instructions, created_at
                FROM recipes
                WHERE title ILIKE %s OR category ILIKE %s and status = 'approved'
                """,
                (f"%{title.strip()}%", f"%{title.strip()}%")
            )
            searched = cur.fetchall()
            recipes_list = [dict(recipe) for recipe in searched]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

    return templates.TemplateResponse("recipes.html", {
        "request": request,
        "username": request.session["user_username"],
        "recipes": recipes_list
    })

@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(request: Request, recipe_id: int):
    cur.execute("SELECT * FROM recipes WHERE id = %s AND status = 'approved'", (recipe_id,))
    recipe = cur.fetchone()

    if not recipe:
        return HTMLResponse("Recipe not found", status_code=404)

    cur.execute("SELECT comment, rating FROM comments WHERE id = %s", (recipe_id,))
    comments = cur.fetchall()

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "recipe": recipe,
        "comments": comments,  # Renamed to match template
    })

@app.get("/recip/{recipe_id}", response_class=HTMLResponse)
def recipe_detail(request: Request, recipe_id: int):
    cur.execute("SELECT * FROM recipes WHERE id = %s and status = 'approved' ", (recipe_id,))
    recipe = cur.fetchone()
    if not recipe:
        return HTMLResponse("Recipe not found", status_code=404)
    return templates.TemplateResponse("admin_detail.html", {
        "request": request,
        "recipe": recipe
    })


def get_logged_in_user_id(request: Request):
    username = request.session.get("user_username")  # or "author_username" as per your session key
    if not username:
        return None

    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            return None
        if isinstance(user, dict):
            return user["id"]
        else:
            return user[0]
    finally:
        cur.close()


@app.get("/comment/{recipe_id}", response_class=HTMLResponse)
def comment_page(request: Request, recipe_id: int):
    user_id = get_logged_in_user_id(request)
    cur.execute("""
        SELECT comments.id, comments.comment,comments.cid, comments.reply, users.username
        FROM comments
        INNER JOIN users ON users.id = comments.user_id
        WHERE comments.id = %s
    """, (recipe_id,))
    comments = cur.fetchall()
    return templates.TemplateResponse("comment.html", {
        "request": request,
        "comments": comments,
        "recipe_id": recipe_id

    })




@app.post("/comment/post", response_class=HTMLResponse)
def post_comment(
    request: Request,
    recipe_id: int = Form(...),
    comment: str = Form(...),
    rating: int = Form(...)
):
    user_id = get_logged_in_user_id(request)
    if not user_id:
        return RedirectResponse("/login/user", status_code=302)

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO comments (id, comment, rating, user_id)
            VALUES (%s, %s, %s, %s)
        """, (recipe_id, comment, rating, user_id))
        conn.commit()
    finally:
        cur.close()

    return RedirectResponse("/user/dashboard", status_code=302)


@app.get("/author/dashboard", response_class=HTMLResponse)
def author_dashboard(request: Request):
        author_id = get_logged_in_author_id(request)
        if not author_id:
            return RedirectResponse("/login/author", status_code=302)
            
        cur.execute("""
            SELECT r.id AS recipe_id, r.title, r.category, r.image_path, c.comment, c.rating,c.cid
            FROM recipes r
            LEFT JOIN comments c ON r.id = c.id
            WHERE r.author_id = %s 
            ORDER BY r.id
        """, (author_id,))
        rows = cur.fetchall()

        recipe_dict = {}
        for row in rows:
            rid = row['recipe_id']
            if rid not in recipe_dict:
                recipe_dict[rid] = {
                    'id': rid,
                    'title': row['title'],
                    'category': row['category'],
                    'image_path': row['image_path'], 
                    'comments': []
                }
            if row['comment']:  # Only add if comment exists
                recipe_dict[rid]['comments'].append({
                    'cid': row['cid'], 
                    'comment': row['comment'], 
                    'rating': row['rating']
                })

        return templates.TemplateResponse("dash_author.html", {
            "request": request,
            "username": request.session.get("author_username"),
            "recipes": list(recipe_dict.values())
        })

@app.get("/del-user",response_class=HTMLResponse)
def view_comments(request: Request):
    cur.execute("select * from recipes")
    comm=cur.fetchall()
    return templates.TemplateResponse("rem_user.html", {
        "request": request,
        "comments":comm
    })

@app.post("/admin/recipe-approve/{id}", response_class=HTMLResponse)
def update_recipe_status(request: Request,id: int):
    cur.execute("SELECT id FROM recipes WHERE id = %s", (id,))
    if not cur.fetchone():
        return HTMLResponse("Recipe not found", status_code=404)

    cur.execute("UPDATE recipes SET status = 'approved' WHERE id = %s", (id,))
    conn.commit()
    return RedirectResponse(url="/del-user", status_code=303)
    

@app.post("/admin/recipe-dis/{id}", response_class=HTMLResponse)
def disapprove_recipe(id: int):
    cur.execute("SELECT id FROM recipes WHERE id = %s", (id,))
    if not cur.fetchone():
        return HTMLResponse("Recipe not found", status_code=404)

    cur.execute("UPDATE recipes SET status = 'disapproved' WHERE id = %s", (id,))
    conn.commit()
    return RedirectResponse(url="/del-user", status_code=303)

from fastapi import Form, Path

@app.post("/add/comm/{cid}",response_class=HTMLResponse)
def add_reply(cid: int, reply: str = Form(...)):
    try:
        cur.execute("UPDATE comments SET reply = %s WHERE cid = %s", (reply, cid))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("DB error:", e)
    return RedirectResponse(url="/author/dashboard", status_code=303)

@app.post("/save/{id}", response_class=HTMLResponse)
def save_later(id: int, request: Request):
    user_username = request.session.get("user_username")
    if not user_username:
        return RedirectResponse("/login/user", status_code=302)

    # Get the user's ID from the session or DB
    cur.execute("SELECT id FROM users WHERE username = %s", (user_username,))
    user = cur.fetchone()
    if not user:
        return RedirectResponse("/login/user", status_code=302)
    user_id = user['id']
    try:
        cur.execute("""
            INSERT INTO saved_recipes (user_id, recipe_id) 
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (user_id, id))
        conn.commit()
    except Exception as e:
        print("DB error on save:", e)
        conn.rollback()
    return RedirectResponse("/user/dashboard", status_code=303)

@app.get("/saved-recipes", response_class=HTMLResponse)
def view_saved_recipes(request: Request):
    user_username = request.session.get("user_username")
    if not user_username:
        return RedirectResponse("/login/user", status_code=302)

    # Fetch user ID
    cur.execute("SELECT id FROM users WHERE username = %s", (user_username,))
    user = cur.fetchone()
    if not user:
        return RedirectResponse("/login/user", status_code=302)
    user_id = user['id']

    # Get saved recipes (join to get recipe details)
    cur.execute("""
        SELECT distinct r.id, r.title, r.category, r.image_path
        FROM recipes r
        JOIN saved_recipes s ON r.id = s.recipe_id
        WHERE s.user_id = %s
    """, (user_id,))
    all_rec = cur.fetchall()

    return templates.TemplateResponse("save.html", {
        "request": request,
        "all_rec": all_rec
    })

@app.post("/report_comment", response_class=HTMLResponse)
def report_comment(request:Request,
    comment_id: int = Form(...)
):
    cur.execute("""
        INSERT INTO reports (cid)
        VALUES (%s)
    """, (comment_id,))
    conn.commit()
    return RedirectResponse("/user/dashboard", status_code=302)

@app.get("/rem-user", response_class=HTMLResponse)
def reported_users(request: Request):
    cur = conn.cursor()
    cur.execute("""
        SELECT comments.user_id, COUNT(*) as report_count
        FROM reports
        JOIN comments ON comments.cid = reports.cid
        GROUP BY comments.user_id
    """)
    users = cur.fetchall()
    print(users)
    cur.close()
    return templates.TemplateResponse("reported.html", {
        "request": request,
        "reported_users": users
    })


@app.post("/remove_user", response_class=HTMLResponse)
def delete_users(user_id: int = Form(...)):
    cur = conn.cursor()
    try:
        # Check if the user exists
        cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found.")

        # Proceed with deletion
        cur.execute("DELETE FROM comments WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM saved_recipes WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        cur.close()

    return RedirectResponse(url="/rem-user", status_code=303)






















        











	

































    














    
"""@app.post("/posts")

def create_posts(post: Post):
    cur.execute(
        "INSERT INTO post (title, content) VALUES (%s, %s)",
        (post.title, post.content)
    )
    conn.commit()
    return {"message": "New post added successfully"}
@app.delete("/posts/{id}")
def delete_post(id: int):
    cur.execute("DELETE FROM post WHERE id = %s", (id,))
    conn.commit()
    return {"message": "Post deleted successfully"}"""

   


