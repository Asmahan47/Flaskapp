import os
import sys
import subprocess

from bson.objectid import ObjectId
from flask import Flask, flash, redirect, render_template, request, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo

# Ensure the directory of the current script is added to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb+srv://purpleblood124:asmahanzeeshan@cluster0.oebsc.mongodb.net/testdb?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)

# Login route
@app.route("/")
def login():
    return render_template("login.html")


# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        name = result["name"]

        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            flash("Email already in use. Please try a different email.")
            return render_template("signup.html", email=email, name=name)

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({"name": name, "email": email, "password": hashed_password})
        flash("Registration successful!")
        return redirect(url_for('login'))

    return render_template("signup.html")


# Login result route
@app.route("/result", methods=["POST"])
def result():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user['password'], password):
            session["is_logged_in"] = True
            session["email"] = email
            session["uid"] = str(user["_id"])
            session["name"] = user["name"]
            return redirect(url_for('welcome'))
        else:
            flash("Login failed. Please check your credentials.")
            return render_template("login.html", email=email)

    return redirect(url_for('login'))


# Welcome page (no posts visible, but accessible through a separate route)
@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    if session.get("is_logged_in"):
        return render_template("welcome_no_posts.html", email=session["email"], name=session["name"])
    return redirect(url_for('login'))


# Page for retrieving posts (this will list the user's posts)
@app.route("/view_posts")
def view_posts():
    if session.get("is_logged_in"):
        posts = list(mongo.db.posts.find({"userId": session["uid"]}))  # Get posts of logged-in user
        return render_template("view_posts.html", posts=posts, email=session["email"], name=session["name"])
    return redirect(url_for('login'))


# Create a new post
@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if session.get("is_logged_in"):
        if request.method == "POST":
            title = request.form["title"]
            description = request.form["description"]
            image = request.files.get("image")

            if title and description and image:
                user_id = session['uid']
                image_filename = image.filename

                if image and allowed_file(image_filename):
                    user_image_dir = f"static/images/{user_id}/"
                    os.makedirs(user_image_dir, exist_ok=True)

                    image_path = os.path.join(user_image_dir, image_filename)
                    image.save(image_path)

                    post_data = {
                        "title": title,
                        "description": description,
                        "imageUrl": f"images/{user_id}/{image_filename}",  # Store the relative path
                        "userId": user_id
                    }
                    mongo.db.posts.insert_one(post_data)
                    flash("Post uploaded successfully!")
                else:
                    flash("Please upload a valid image file.")
            else:
                flash("Please fill in all fields and upload an image.")

        return render_template("create_post.html", email=session["email"], name=session["name"])

    return redirect(url_for('login'))


# Read a specific post
@app.route("/post/<post_id>")
def view_post(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if post:
        return render_template("view_post.html", post=post)
    flash("Post not found.")
    return redirect(url_for('view_posts'))


# Update a post
@app.route("/update_post/<post_id>", methods=["GET", "POST"])
def update_post(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        image = request.files.get("image")

        post_data = {
            "title": title,
            "description": description
        }

        if image:
            image_filename = image.filename
            if allowed_file(image_filename):
                user_image_dir = f"static/images/{session['uid']}/"
                os.makedirs(user_image_dir, exist_ok=True)

                old_image_path = f"static/{post['imageUrl']}"
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

                image_path = os.path.join(user_image_dir, image_filename)
                image.save(image_path)
                post_data["imageUrl"] = f"images/{session['uid']}/{image_filename}"

        mongo.db.posts.update_one({"_id": ObjectId(post_id)}, {"$set": post_data})
        flash("Post updated successfully!")
        return redirect(url_for('view_posts'))

    return render_template("update_post.html", post=post)


# Delete a post
@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted successfully!")
    return redirect(url_for('view_posts'))


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def run_gunicorn():
    """Automatically start Gunicorn when running the app"""
    subprocess.Popen([sys.executable, "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:3047", "FlaskusingMogoDB.main9:app"])



if __name__ == "__main__":
    # Ensure the module is imported correctly before starting Gunicorn
    run_gunicorn()
