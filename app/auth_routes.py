import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),"app"))
import random
from datetime import datetime,timedelta
from dotenv import load_dotenv
load_dotenv()

from flask import Flask,render_template,jsonify,request,Blueprint
from flask_wtf import FlaskForm,CSRFProtect
from wtforms import StringField,PasswordField
from wtforms.validators import DataRequired,length,Email,EqualTo
from flask_login import LoginManager,login_required,login_user,UserMixin,logout_user
from flask_mail import Mail,Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.datastructures import ImmutableMultiDict
from extensions import db,login_manager,csrf,mail
# initialize bluprint 
auth_bp = Blueprint("auth",__name__)

# app instialize 
#app = Flask(__name__)
#app.config["SECRET_KEY"] = os.getenv("APP_PASSWORD")
#app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL","sqlite:///blog.db") # data base connection 

# CSRF if protection method it checks the user is correct ! means :- when you already login but new login request (unknown) comes to server then it rejects with -->> 400
#csrf = CSRFProtect(app=app)

# flask login instialization it stores the user login details in user browser as the form of cache 
#login_manager = LoginManager()
#login_manager.init_app(app=app)
#login_manager.login_view = "login"

# senfing the emails to user 
""" app.config["MAIL_SERVER"] = os.getenv("EMAIL_SERVER")
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")
 """
# initialize the database and mail
""" db = SQLAlchemy(app)
mail = Mail(app)
 """
# Database models 
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(40),unique=True,nullable=False)
    email = db.Column(db.String(60),unique=True,nullable=False)
    password_hash = db.Column(db.String(260),nullable=False)
    is_verified = db.Column(db.Boolean,default=False,nullable=False)

class OTPDB(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    email = db.Column(db.String(60),unique=True,nullable=False)
    otp_ = db.Column(db.String(6),nullable=False)
    expires_at = db.Column(db.DateTime,nullable=False)

class LoginForm(FlaskForm):
    email = StringField("email",validators=[DataRequired(),Email()])
    password = PasswordField("password",validators=[DataRequired(),length(min=6,max=16)])

class RegistrationForm(FlaskForm):
    username = StringField("username",validators=[DataRequired()])
    email = StringField("email",validators=[DataRequired(),Email()])
    otp_ = StringField("OTP",validators=[DataRequired(),length(min=6)]) #  write the otp sending required code 
    password = PasswordField("password",validators=[DataRequired(),length(min=6,max=16,message="Use Strong Password")])
    conform_pass = PasswordField("password",validators=[DataRequired(),EqualTo("password")])


# load the login users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# senf OTP to the user 
def send_otp_email(email : str, otp : str):
    msg = Message(
        subject="Blogging Website OTP",
        sender=os.getenv("EMAIL_USER"),
        recipients=[email],
    )
    msg.body = f"Your OTP is {otp}"

    msg.html = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your OTP Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: Arial, sans-serif; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;">
    <!-- Main Wrapper Table (Centers the email body) -->
    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f6f9; padding: 40px 10px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" class="content-table" border="0" cellspacing="0" cellpadding="0" style="max-width: 440px; background-color: #ffffff; border: 1px solid #e1e4e8; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    
                    <tr>
                        <td align="center" style="padding: 30px 24px 10px 24px;">
                            <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #fafafa; border: 1px dashed #cccccc; border-radius: 8px;">
                                <tr>
                                    <td align="center" style="padding: 20px; font-size: 18px; font-weight: bold; color: #333333; letter-spacing: 0.5px;">
                                        Herambha Blogging
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px 30px 10px 30px; font-size: 15px; color: #555555; line-height: 1.6; text-align: left;">
                            Hello,<br><br>
                            This is a secure automated message from the Blogging website of Herambha. Authentication is required to proceed. 
                            Please use the One-Time Password (OTP) provided below to complete your login.
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 20px 30px;">
                            <table role="presentation" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f3f5; border: 1px solid #ced4da; border-radius: 8px; width: 100%;">
                                <tr>
                                    <td align="center" style="padding: 15px 10px; font-size: 32px; font-weight: bold; color: #111111; letter-spacing: 6px; font-family: 'Courier New', Courier, monospace;">
                                        {otp}
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 20px 30px; font-size: 12px; color: #888888; line-height: 1.4; text-align: left;">
                            If you did not request this code, please ignore this email or secure your account settings. This code is valid for a limited time.
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 35px 30px; font-size: 14px; font-weight: 500; color: #666666; text-align: left; border-top: 1px solid #eeeeee; padding-top: 20px;">
                            Thank You!<br>
                            <span style="font-size: 12px; color: #999999;">The Herambha Team</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """

    mail.send(msg)


@auth_bp.route("/api/otp_sending",methods=["GET","POST"])
@csrf.exempt
def send_otp():
    data = request.get_json()
    user_email = data.get("user_email","").strip()

    if not user_email:
        return jsonify({"message":"Please Field of Email !"}),400
    
    if User.query.filter_by(email=user_email).first():
        return jsonify({"message":"Email already registered !"})
    
    otp_user = random.randint(100000,999999)
    time = datetime.now().strftime("%H:%M:%S")

    OTPDB.query.filter_by(email=user_email).delete()
    db.session.add(OTPDB(
        email=user_email,
        otp_=str(otp_user),
        expires_at = datetime.utcnow() + timedelta(minutes=10)
    ))
    db.session.commit()

    send_otp_email(user_email,otp_user)
    return jsonify({"message":"OTP Sent Successfully !"})



@auth_bp.route("/api/login",methods=["GET","POST"])
@csrf.exempt
def login():
    data = request.get_json()
    form = LoginForm(ImmutableMultiDict(data),meta={'csrf': False})

    if not form.validate():
        return jsonify({"message":"Validation Failed","error":form.errors}),400
    
    user = User.query.filter_by(email=form.email.data).first()

    if not user or not check_password_hash(user.password_hash,form.password.data):
        return jsonify({"message":"Invalid Email or Password"})
    
    login_user(user) # it uses for without loggin every time

    return jsonify({"message":"Login Successfull","username":user.username})


@auth_bp.route("/api/registration",methods=["GET","POST"])
@csrf.exempt
def registration():
    data = request.get_json()
    form = RegistrationForm(ImmutableMultiDict(data),meta={'csrf': False})
    if not form.validate():
        return jsonify({"message":"Fill all fields are properly first !","errors": form.errors}),400
    
    if User.query.filter_by(email=form.email.data).first():
        return jsonify({"message":"Already having Account for this email."})
    user_otp = OTPDB.query.filter_by(email=form.email.data).first()
    if not user_otp:
        return jsonify({"message":"Click OTP button."})
    if (user_otp.otp_ != form.otp_.data):
        return jsonify({"message":"OTP doesn't match !"})
    
    if user_otp.expires_at < datetime.utcnow():
        return jsonify({"message":"OTP expires. So, Try new one !"})
    
    db.session.add(User(
        username = form.username.data,
        email=form.email.data,
        password_hash = generate_password_hash(form.conform_pass.data),
        is_verified = True, 
    ))
    OTPDB.query.filter_by(email=form.email.data,otp_=form.otp_.data).delete()
    db.session.commit()
    return jsonify({"message":"New User Created"}),201

@auth_bp.route("/api/logout",methods=["GET","POST"])
@csrf.exempt
@login_required
def logout():
    logout_user()
    return jsonify({"message":"Successfull Logout !"})
""" 
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
 """