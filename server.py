from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flaskext.mysql import MySQL
import os
from datetime import datetime

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Pr7@sql'
app.config['MYSQL_DATABASE_DB'] = 'fullstackproject'
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

# Helper function to handle database connection
def get_db_connection():
    conn = mysql.connect()
    return conn


@app.route('/homee')
def homee():
    return render_template('home.html')
# Check if a username is already taken
@app.route('/check-username')
def check_username():
    username = request.args.get('username')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"exists": user is not None})

# Check if login credentials are valid
@app.route('/check-login')
def check_login():
    username = request.args.get('username')
    password = request.args.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"valid": user is not None and user[1] == password})

# Display all posts
@app.route('/home')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch posts
    cursor.execute("SELECT * FROM post")
    posts = cursor.fetchall()

    # Fetch replies for each post
    post_replies = {}
    for post in posts:
        post_id = post[0]
        cursor.execute("SELECT user_name, reply_content FROM replies WHERE post_id = %s", (post_id,))
        post_replies[post_id] = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pass both posts and post_replies to the template
    return render_template("display.html", posts=posts, post_replies=post_replies)

# Compose a new post
@app.route('/compose', methods=['GET', 'POST'])
def compose():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        username = request.form.get('username')
        group_preference = request.form.get('group_preference')
        dop = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        img_file = request.files.get('img_file')

        img_path = None
        if img_file:
            if img_file.filename == '':
                flash('No file selected!', 'error')
                return redirect(request.url)
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_file.filename)
            img_file.save(img_path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO post (user_name, date, img_path, content, title, department) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, dop, img_path, content, title, group_preference)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/home')
    return render_template("compose2.html")
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the specific post details
    cursor.execute("SELECT * FROM post WHERE post_id = %s", (post_id,))
    post = cursor.fetchone()

    if not post:
        cursor.close()
        conn.close()
        return "Post not found", 404

    # Fetch replies for the post
    cursor.execute("SELECT user_name, reply_content FROM replies WHERE post_id = %s", (post_id,))
    replies = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("display_detail.html", post=post, replies=replies)


# User signup
@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        interests = request.form.get('interests')
        bio_data = request.form.get('bio_data')
        profile_pic = request.files.get('profile_pic')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check for missing fields
        if not username or not name or not interests or not bio_data or not password or not confirm_password:
            flash("All fields are required!", "error")
            return render_template('singup.html')

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template('singup.html')

        # Check if the username already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            flash("Username already exists!", "error")
            return render_template('singup.html')

        # Save profile picture if provided
        if profile_pic and profile_pic.filename != '':
            if '.' not in profile_pic.filename or profile_pic.filename.rsplit('.', 1)[1].lower() not in {'jpg', 'jpeg', 'png'}:
                flash('Allowed file types are jpg, jpeg, png.', 'error')
                return redirect(request.url)
            pic_filename = os.path.join(app.config['UPLOAD_FOLDER'], username + os.path.splitext(profile_pic.filename)[1])
            profile_pic.save(pic_filename)

        # Store user data in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_name, password) VALUES (%s, %s)",
            (username, password)  # Store plaintext password
        )
        cursor.execute(
            "INSERT INTO profile (user_name, name, interests, bio_data, profile_pic_path) VALUES (%s, %s, %s, %s, %s)",
            (username, name, interests, bio_data, pic_filename)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Sign up successful!", "success")
        return redirect(url_for('home'))

    return render_template('singup.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or user[1] != password:  # Compare plaintext passwords directly
            return render_template('login.html', error_message='Invalid username or password')

        return redirect('/home')

    return render_template("login.html")

# Like a post
@app.route('/like', methods=['POST'])
def like_post():
    post_id = request.args.get('postId')  # Get the post ID from the query parameters

    if not post_id:
        return jsonify({"error": "Missing post ID"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Increment the like count for the post in the database
        cursor.execute("UPDATE post SET likes = likes + 1 WHERE post_id = %s", (post_id,))
        conn.commit()

        # Fetch the updated like count
        cursor.execute("SELECT likes FROM post WHERE post_id = %s", (post_id,))
        updated_likes = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return jsonify({"likes": updated_likes})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/reply', methods=['POST'])
def add_reply():
    post_id = request.json.get('postId')
    username = request.json.get('username')
    reply_content = request.json.get('replyContent')

    if not post_id or not username or not reply_content:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert the reply into the database
        cursor.execute(
            "INSERT INTO replies (post_id, user_name, reply_content) VALUES (%s, %s, %s)",
            (post_id, username, reply_content)
        )
        conn.commit()

        # Fetch all replies for the post
        cursor.execute("SELECT user_name, reply_content FROM replies WHERE post_id = %s", (post_id,))
        replies = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({"replies": replies})
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Simulate login
@app.route('/simulate-login')
def simulate_login():
    session['user_id'] = 1  # Example user ID after login
    return redirect('/home')

# Home page
@app.route('/home1')
def profile_home():
    if 'user_id' not in session:
        return redirect('/simulate-login')
    return render_template('home.html')

# Profile page
@app.route("/profile/<username>", methods=['GET'])
def profile(username):
    conn = mysql.connect()
    cursor = conn.cursor()

    # Fetch profile details by user_name
    cursor.execute("SELECT user_name, interests, bio_data, profile_pic_path FROM profile WHERE user_name = %s", (username,))
    profile = cursor.fetchone()
    
    if not profile:
        app.logger.error(f"Profile not found for user: {username}") 
        return "Profile not found", 404
        
    # Fetch posts made by the user
    cursor.execute("SELECT title, content, date, img_path FROM post WHERE user_name = %s", (username,))
    posts = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("profile.html", profile=profile, posts=posts)
    

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)

