import os
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_mood_key'

# SQLite database setup
DATABASE_URL = 'sqlite:///mobile_social_app.db'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(200), default="కొత్త యూజర్! ఇంకా బయో సెట్ చేయలేదు.")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50), default="Neutral")
    likes = db.Column(db.Integer, default=0)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Basic mood classifier based on Telugu/English keywords
def detect_mood(text):
    text_lower = text.lower()
    happy_words = ['సంతోషం', 'ఆనందం', 'అద్భుతమైన', 'happy', 'joy', 'awesome', 'good', 'బాగుంది', 'సూపర్']
    sad_words = ['వర్షం', 'బాధ', 'sad', 'rain', 'lonely', 'ఏడుపు', 'ఫీలింగ్']
    stressed_words = ['ఒత్తిడి', 'డెడ్‌లైన్', 'stress', 'tension', 'work', 'భయం', 'కష్టం']
    
    if any(w in text_lower for w in happy_words):
        return 'Happy'
    elif any(w in text_lower for w in sad_words):
        return 'Sad'
    elif any(w in text_lower for w in stressed_words):
        return 'Stressed'
    return 'Neutral'

# Combined HTML Template matching UI perfectly
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="te">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mobile Social App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #0d1626;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .app-container {
            max-width: 500px;
            margin: 0 auto;
            background-color: #121f38;
            min-height: 100vh;
            padding-bottom: 50px;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }
        .app-header {
            background-color: #172745;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #1e335a;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .card-custom {
            background-color: #172745;
            border: 1px solid #233a67;
            border-radius: 12px;
            padding: 15px;
            margin: 15px;
        }
        .form-control-custom {
            background-color: #0d1626;
            border: 1px solid #233a67;
            color: white;
            border-radius: 8px;
        }
        .form-control-custom:focus {
            background-color: #0d1626;
            border-color: #3b82f6;
            color: white;
            box-shadow: none;
        }
        .btn-update {
            background-color: #10b981;
            color: white;
            border: none;
            width: 100%;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
        }
        .btn-update:hover { background-color: #059669; }
        .btn-primary-custom {
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }
        .btn-primary-custom:hover { background-color: #2563eb; }
        .post-card {
            background-color: #0d1626;
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 15px;
        }
        .post-card.happy { border-left-color: #eab308; }
        .post-card.sad { border-left-color: #60a5fa; }
        .post-card.stressed { border-left-color: #ef4444; }
        .profile-pic {
            width: 45px;
            height: 45px;
            background-color: #3b82f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .comment-section {
            border-top: 1px solid #1e335a;
            padding-top: 8px;
            margin-top: 8px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>

<div class="app-container">
    {% if not logged_in %}
    <!-- GATEWAY SCREEN (LOGIN / REGISTER) -->
    <div class="app-header">
        🔐 యాప్ గేట్‌వే
    </div>
    
    <div class="p-3">
        {% if error %}
        <div class="alert alert-warning text-center py-2" style="background-color: #fef08a; color: #854d0e; border: none;">
            ⚠️ {{ error }}
        </div>
        {% endif %}

        <!-- SIGN IN FORM -->
        <div class="card-custom">
            <h5 class="mb-3 text-primary">👉 లాగిన్ అవ్వండి (Sign In)</h5>
            <form action="/login" method="POST">
                <div class="mb-3">
                    <input type="text" name="username" class="form-control form-control-custom" placeholder="యూజర్నేమ్ ఎంటర్ చేయండి" required>
                </div>
                <div class="mb-3">
                    <input type="password" name="password" class="form-control form-control-custom" placeholder="పాస్వర్డ్ ఎంటర్ చేయండి" required>
                </div>
                <button type="submit" class="btn btn-primary-custom w-100 py-2">లాగిన్ అవ్వండి</button>
            </form>
        </div>

        <!-- SIGN UP FORM -->
        <div class="card-custom" style="border-color: #10b981;">
            <h5 class="mb-3 text-success">✨ కొత్త ఖాతా సృష్టించండి (Sign Up)</h5>
            <form action="/register" method="POST">
                <div class="mb-3">
                    <input type="text" name="username" class="form-control form-control-custom" placeholder="కొత్త యూజర్నేమ్ ఎంచుకోండి" required>
                </div>
                <div class="mb-3">
                    <input type="password" name="password" class="form-control form-control-custom" placeholder="కొత్త పాస్వర్డ్ ఎంచుకోండి" required>
                </div>
                <button type="submit" class="btn btn-update">ఖాతా సృష్టించు (Register)</button>
            </form>
        </div>
    </div>

    {% else %}
    <!-- MAIN APPLICATION FEED -->
    <div class="app-header d-flex justify-content-between align-items-center px-3">
        <span>📱 Mobile Social App</span>
        <a href="/logout" class="btn btn-sm btn-outline-danger text-decoration-none py-0 px-2" style="font-size:0.8rem;">Logout</a>
    </div>

    <!-- User Profile Widget -->
    <div class="card-custom d-flex align-items-center gap-3">
        <div class="profile-pic">{{ user.username[:2].upper() }}</div>
        <div>
            <div class="fw-bold">@{{ user.username }}</div>
            <div class="text-muted small">{{ user.bio }}</div>
        </div>
    </div>

    <!-- Update Bio Form -->
    <div class="card-custom">
        <h6 class="mb-2"><span class="small">⚙️</span> ప్రొఫైల్ అప్‌డేట్</h6>
        <form action="/update_bio" method="POST" class="d-flex flex-column gap-2">
            <input type="text" name="bio" class="form-control form-control-custom text-white" placeholder="మీ కొత్త స్టేటస్/బయో టైప్ చేయండి...">
            <button type="submit" class="btn btn-update">బయో అప్‌డేట్ చేయి</button>
        </form>
    </div>

    <!-- Create Post Form -->
    <div class="card-custom">
        <h6 class="mb-2">✍️ మీ మనసులోని భావాన్ని పంచుకోండి (Create Post)</h6>
        <form action="/create_post" method="POST" class="d-flex flex-column gap-2">
            <textarea name="content" class="form-control form-control-custom text-white" rows="2" placeholder="ఇక్కడ టైప్ చేయండి..." required></textarea>
            <button type="submit" class="btn btn-primary-custom w-100 py-1">పోస్ట్ చేయి</button>
        </form>
    </div>

    <!-- AI Mood-Based Feed -->
    <div class="mx-3">
        <h6 class="mb-3 text-muted">🧠 AI Mood-Based Feed</h6>
        
        {% for post in posts %}
        <div class="post-card {% if post.mood == 'Happy' %}happy{% elif post.mood == 'Sad' %}sad{% elif post.mood == 'Stressed' %}stressed{% endif %}">
            <div class="fw-bold text-info">@{{ post.username }}</div>
            <div class="my-2">{{ post.content }}</div>
            
            <div class="d-flex align-items-center gap-3 mb-2 small text-muted">
                <form action="/like/{{ post.id }}" method="POST" style="display:inline;">
                    <button type="submit" class="btn btn-sm p-0 border-0 text-danger font-weight-bold">❤️ లైక్ ({{ post.likes }})</button>
                </form>
                <span class="badge bg-secondary">{{ post.mood }}</span>
            </div>

            <!-- Display Comments -->
            {% for comment in comments_dict[post.id] %}
            <div class="comment-section text-light">
                <strong class="text-warning">@{{ comment.username }}:</strong> {{ comment.content }}
            </div>
            {% endfor %}

            <!-- Add Comment Form -->
            <form action="/comment/{{ post.id }}" method="POST" class="d-flex gap-2 mt-2">
                <input type="text" name="comment_text" class="form-control form-control-custom form-control-sm py-1" placeholder="కామెంట్ రాయండి..." required>
                <button type="submit" class="btn btn-sm btn-primary-custom px-3 py-1">పంపు</button>
            </form>
        </div>
        {% else %}
        <div class="text-center text-muted py-4">ఇంకా ఎలాంటి పోస్ట్‌లు లేవు. మొదటి పోస్ట్ చేయండి!</div>
        {% endfor %}
    </div>
    {% endif %}
</div>

</body>
</html>
'''

@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template_string(HTML_TEMPLATE, logged_in=False)
    
    user = User.query.get(session['user_id'])
    posts = Post.query.order_by(Post.id.desc()).all()
    
    comments_dict = {}
    for post in posts:
        comments_dict[post.id] = Comment.query.filter_by(post_id=post.id).all()
        
    return render_template_string(HTML_TEMPLATE, logged_in=True, user=user, posts=posts, comments_dict=comments_dict)

@app.route('/register', method=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if User.query.filter_by(username=username).first():
        return render_template_string(HTML_TEMPLATE, logged_in=False, error="ఈ యూజర్నేమ్ ఇప్పటికే ఉంది!")
        
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    session['user_id'] = new_user.id
    return redirect(url_for('home'))

@app.route('/login', method=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return render_template_string(HTML_TEMPLATE, logged_in=False, error="వివరాలు పూర్తిగా ఎంటర్ చేయండి / తప్పుగా ఉన్నాయి!")
        
    session['user_id'] = user.id
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/update_bio', method=['POST'])
def update_bio():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = User.query.get(session['user_id'])
    new_bio = request.form.get('bio')
    if new_bio:
        user.bio = new_bio
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/create_post', method=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('home'))
        
    user = User.query.get(session['user_id'])
    content = request.form.get('content')
    if content:
        mood = detect_mood(content)
        new_post = Post(username=user.username, content=content, mood=mood)
        db.session.add(new_post)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/like/<int:post_id>', method=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/comment/<int:post_id>', method=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    content = request.form.get('comment_text')
    if content:
        new_comment = Comment(post_id=post_id, username=user.username, content=content)
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed initial sample data matching the screenshot if empty
        if not User.query.filter_by(username='Nagesh').first():
            dummy_users = [
                User(username='Nagesh', bio='కొత్త యూజర్! ఇంకా బయో సెట్ చేయలేదు.'),
                User(username='రాహుల్', bio='Happy and coding!'),
                User(username='సవ్య', bio='Listening to music...'),
                User(username='కిరణ్', bio='Busy weeks ahead.')
            ]
            for u in dummy_users:
                u.password = generate_password_hash('password123', method='pbkdf2:sha256')
                db.session.add(u)
            db.session.commit()
            
            p1 = Post(username='రాహుల్', content='ఈరోజు చాలా సంతోషంగా ఉంది! అద్భుతమైన ఉదయం ☀️', mood='Happy', likes=5)
            p2 = Post(username='సవ్య', content='వర్షం పడుతోంది, ప్రశాంతమైన మెలోడీలు వింటున్నాను 🌧️🎵', mood='Sad', likes=3)
            p3 = Post(username='కిరణ్', content='కొత్త ప్రాజెక్ట్ డెడ్‌లైన్... కొంచెం ఒత్తిడిగా ఉంది ⏳', mood='Stressed', likes=2)
            db.session.add_all([p1, p2, p3])
            db.session.commit()
            
            c1 = Comment(post_id=p2.id, username='రాహుల్', content='సూపర్!')
            db.session.add(c1)
            db.session.commit()

    app.run(host='0.0.0.0', port=8085, debug=True)
