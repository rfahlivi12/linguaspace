from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os
from datetime import datetime

# === Flask setup ===
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisaverysecuresecretkey123'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'linguaspace.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# === Database & Migrations ===
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# === Database Models ===
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# === Helper ===
def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)

# === Routes ===
@app.route('/')
def home():
    print("DEBUG SESSION:", session)  # <<< Debug session
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, user=get_current_user())

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    user = get_current_user()
    if not user:
        flash("Please log in to write a new post.", "warning")
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash("Title and content cannot be empty.", "danger")
            return redirect(url_for('new_post'))
        post = Post(title=title, content=content, author_id=user.id)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been published successfully.", "success")
        return redirect(url_for('home'))
    return render_template('new.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
            return redirect(url_for('register'))
        new_user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        # <<< AUTO LOGIN AFTER REGISTER >>>
        session['user_id'] = new_user.id
        flash("Registration successful! You are now logged in.", "success")
        return redirect(url_for('home'))

    return render_template('register.html', user=get_current_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Login failed. Check your email and password.", "danger")
            return redirect(url_for('login'))
        session['user_id'] = user.id
        flash("Login successful!", "success")
        return redirect(url_for('home'))
    return render_template('login.html', user=get_current_user())

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    author = User.query.get(post.author_id) if post.author_id else None
    return render_template('post.html', post=post, author=author, user=get_current_user())

# === Admin Route ===
@app.route('/admin')
def admin_dashboard():
    user = get_current_user()
    if not user:
        flash("You must log in to access the admin dashboard.", "danger")
        return redirect(url_for('login'))
    
    # Hardcode email developer sebagai admin
    if user.email != 'rfahlivi12@gmail.com':  # Ganti dengan emailmu
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for('home'))
    
    users = User.query.all()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin.html', user=user, users=users, posts=posts)

# === Run the App ===
if __name__ == '__main__':
    # Initialize database automatically if not exists
    if not os.path.exists(os.path.join(BASE_DIR, 'linguaspace.db')):
        with app.app_context():
            db.create_all()
            print("✅ linguaspace.db created successfully (using email login).")
    app.run(host='0.0.0.0', port=5000, debug=True)