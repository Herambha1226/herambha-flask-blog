import sys
import os 
sys.path.append(os.path.join(os.path.dirname(__file__),"app"))
from flask import Flask,render_template
from dotenv import load_dotenv
load_dotenv()

from app.extensions import db,login_manager,csrf,mail
from app.auth_routes import auth_bp
from app.post_routes import post_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("APP_PASSWORD")

database_url = os.getenv("DATABASE_URL", "sqlite:///blog.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,        
    "pool_recycle": 300,          
    "connect_args": {
        "sslmode": "require"      
    }
}
app.config["MAIL_SERVER"] = os.getenv("EMAIL_SERVER")
app.config["MAIL_PORT"]           = 587  
app.config["MAIL_USE_TLS"]        = True    
app.config["MAIL_USE_SSL"]        = False  
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("BREVO_SMTP_KEY")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("EMAIL_USER")

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
mail.init_app(app)

login_manager.login_view = "login_page"

app.register_blueprint(auth_bp)
app.register_blueprint(post_bp)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/blogs")
def blogs():
    return render_template("blog.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/post")
def post_page():
    return render_template("post.html")

@app.route("/publish")
def publish_page():
    return render_template("publish.html")

@app.route("/dashboard")
def dashbord():
    return render_template("dashboard.html")
if __name__ == "__main__":
    app.run(debug=True)
