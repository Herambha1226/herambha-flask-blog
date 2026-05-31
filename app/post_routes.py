import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__),"app"))
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from flask import Flask,jsonify,request,Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField,TextAreaField
from wtforms.validators import length,DataRequired
from werkzeug.datastructures import ImmutableMultiDict
from flask_login import login_required,current_user
from app.extensions import db,login_manager,csrf,mail

# initialize the bluprint
post_bp = Blueprint("post",__name__)

#app = Flask(__name__)
#app.config["SECRET_KEY"] = os.getenv("APP_PASSWORD")
#app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

#db = SQLAlchemy(app)

# user data base table
class USER_POST_db(db.Model):
    __tablename__ = "user_post"
    id = db.Column(db.Integer,primary_key=True)
    post_title = db.Column(db.String(150),nullable=False)
    content =db.Column(db.Text,nullable=False)
    author = db.Column(db.String(100),nullable=False)
    publication_date = db.Column(db.DateTime,nullable=False)

    # one  ->  many table relationship connection 
    comments = db.relationship("COMMENTS",backref="post",lazy=True)
    likes = db.relationship("Likes",backref="post",lazy=True)
    tags = db.relationship("Tags",secondary="post_tags",lazy=True)

    def to_dict(self):
        return {
            "id":self.id,
            "title":self.post_title,
            "content":self.content,
            "author" : self.author,
            "date" : self.publication_date,
            "likes" : len(self.likes),
            "comments":len(self.comments),
            "tags" : [tag.name for tag in self.tags]
        }
    
# comments table 
class COMMENTS(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer,primary_key = True)
    post_title = db.Column(db.String(150),nullable=False)
    comment = db.Column(db.String(500),nullable=False)
    author = db.Column(db.String(100),nullable=False)
    time = db.Column(db.DateTime,nullable=False)

    post_id = db.Column(db.Integer,db.ForeignKey("user_post.id"),nullable=False)

    def to_dict(self):
        return {
            "id" : self.id,
            "comment": self.comment,
            "author" : self.author,
            "date" : self.time,
            "post_id":self.post_id
        }

# likes table
class Likes(db.Model):
    __tablename__ = "likes"
    id = db.Column(db.Integer,primary_key=True)
    author = db.Column(db.String(100),nullable=False)
    post_id = db.Column(db.Integer,db.ForeignKey("user_post.id"),nullable=False)

    __table__args__ = {
        db.UniqueConstraint("author","post_id",name="unique_like"),
    }

# blog post tags
class Tags(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50),nullable=False,unique=True)

# post-tags relationship 
class PostTags(db.Model):
    __tablename__ = "post_tags"
    id = db.Column(db.Integer,primary_key=True)
    post_id = db.Column(db.Integer,db.ForeignKey("user_post.id"),nullable=False)
    tag_id = db.Column(db.Integer,db.ForeignKey("tags.id"),nullable=False)

    __table__args__ = {
        db.UniqueConstraint("post_id","tag_id",name="unique_post_tag")
    }

# Blog Post form 
class User_Post_form(FlaskForm):
    title = StringField("post_title",validators=[DataRequired()])
    content = TextAreaField("post_content",validators=[DataRequired()])


# it uses the post sending 
@post_bp.route("/api/publish_post",methods=["POST"])
@csrf.exempt
@login_required
def post():
    data = request.get_json()
    form = User_Post_form(ImmutableMultiDict(data),meta={'csrf': False})

    if not form.validate():
        return jsonify({"message":"Please fill Required fields"}),400
    post_data = USER_POST_db(
        post_title=form.title.data,
        content=form.content.data,
        author=current_user.username,
        publication_date = datetime.utcnow(),
    )
    db.session.add(post_data)
    
    tags = data.get("tags",[])
    for tag_name in tags:
        tag_name = tag_name.strip().lower()
        tag = Tags.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tags(name=tag_name)
            db.session.add(tag)
        post_data.tags.append(tag)

    db.session.commit()
    return jsonify({"message":"Post Posted Successful !"}),201

# it post get's by ID
@post_bp.route("/api/post/<int:id>",methods = ["GET"])
def get_post(id):
    post = USER_POST_db.query.get_or_404(id)
    return jsonify(post.to_dict()),200

# it comments the post 
@post_bp.route("/api/post/<int:post_id>/comment",methods=["POST"])
@csrf.exempt
@login_required
def add_comment(post_id):
    post = USER_POST_db.query.get_or_404(post_id)
    data = request.get_json()
    if not data.get("comment"):
        return jsonify({"message":"comment is required"}),400
    new_comment = COMMENTS(
        comment = data["comment"],
        author = current_user.username,
        post_id = post_id,  
        post_title=post.post_title,
        time=datetime.utcnow()
    )

    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"message":"Comment added !"}),201

# get all comments for the post
@post_bp.route("/api/post/<int:post_id>/comments",methods=["GET"])
def get_comments(post_id):
    post = USER_POST_db.query.get_or_404(post_id)
    return jsonify([c.to_dict() for c in post.comments]),200

# like the post
@post_bp.route("/api/post/<int:post_id>/like", methods=["POST"])
@csrf.exempt
@login_required
def like_post(post_id):

    if not current_user.is_authenticated:
        return jsonify({"message": "Login required"}), 401

    USER_POST_db.query.get_or_404(post_id)

    existing = Likes.query.filter_by(
        post_id=post_id,
        author=current_user.username
    ).first()

    if existing:
        return jsonify({"message": "Already liked"}), 400

    db.session.add(Likes(
        post_id=post_id,
        author=current_user.username
    ))
    db.session.commit()

    return jsonify({"message": "Post liked"}), 200

# already liked person uses removing like
@post_bp.route("/api/post/<int:post_id>/unlike",methods=["POST"])
@csrf.exempt
@login_required
def unlike_post(post_id):
    USER_POST_db.query.get_or_404(post_id)
    data = request.get_json()
    like = Likes.query.filter_by(post_id=post_id,author=current_user.username).first_or_404()
    db.session.delete(like)
    db.session.commit()
    return jsonify({"message":"Like removed"}),200

# getting all posts in the table
@post_bp.route("/api/all_posts",methods=["GET"])
def all_posts():
    data = USER_POST_db.query.order_by(USER_POST_db.publication_date.desc()).all()
    return jsonify([p.to_dict() for p in data]),200

# remove or delete the post from the table 
@post_bp.route("/api/post_del/<int:id>",methods=["DELETE"])
@csrf.exempt
@login_required
def delete_post(id):
    data = USER_POST_db.query.get_or_404(id)
    if post.author != current_user.username:
        return jsonify({"message": "Not authorized to delete this post!"}), 403
    COMMENTS.query.filter_by(post_id=id).delete()
    Likes.query.filter_by(post_id=id).delete()

    from sqlalchemy import text
    db.session.execute(text("DELETE FROM post_tags WHERE post_id = :id"),{"id":id})

    db.session.delete(data)
    db.session.commit()
    return jsonify({"message":f"{id} Post deleted Successfully !"}),200

# particular user posts will appears 
@post_bp.route("/api/user/<string:username>/posts",methods=["GET"])
@csrf.exempt
@login_required
def load_user_post(username):
    #print(f"Looking for posts by: '{username}'") 
    data = USER_POST_db.query.filter_by(author=username).order_by(
        USER_POST_db.publication_date.desc()
    ).all()
 
    return jsonify([{
        "id":       p.id,
        "title":    p.post_title,
        "content":  p.content,
        "date":     str(p.publication_date),
        "likes":    len(p.likes),
        "comments": len(p.comments),
        "tags":     [tag.name for tag in p.tags]
    } for p in data]), 200

@post_bp.route("/api/search",methods=["GET"])
def search():
    data = request.args.get("q","").strip().lower()
    if not data:
        return jsonify({"message":"Fill Field !"})
    
    result = USER_POST_db.query.filter(
        db.or_(
            USER_POST_db.post_title.ilike(f"%{data}%"),
            USER_POST_db.content.ilike(f"%{data}%"),
            USER_POST_db.author.ilike(f"%{data}%")
        )
    ).all()

    if not result:
        return jsonify({"message":"Not Found !"})
    return jsonify([p.to_dict() for p in result]),200

# creating SQLALCHEMY file based data
#with app.app_context():
    db.create_all()

#if __name__ == "__main__":
 #   app.run(debug=True)



