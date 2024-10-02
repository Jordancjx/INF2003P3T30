from flask import Blueprint, render_template, current_app, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from datetime import datetime

forum_bp = Blueprint('forum', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/forum')


# Dashboard
@forum_bp.route('/')
def index():
    with current_app.app_context():
        sql = text("SELECT threads.*, users.id as user_id, users.username as username FROM threads LEFT JOIN users ON users.id = threads.users_id")
        result = db.session.execute(sql)
        threads = result.fetchall()
        return render_template('/forum/forum.html', threads = threads)

# Single page for threads
@forum_bp.route('/single/<int:id>', methods = ["GET"])
def single(id):
     with current_app.app_context():
        try:  
            sql = text("SELECT threads.*, users.id as user_id, users.username as username, users.email as email, users.profile_pic_url as profile_pic_url, users.admin_controls as admin_controls FROM threads LEFT JOIN users ON users.id = threads.users_id WHERE threads.id = :thread_id")
            result = db.session.execute(sql, {"thread_id":id})
            thread = result.fetchone()
            
            sql = text("SELECT posts.*,users.id as user_id, users.username as username, users.email as email, users.profile_pic_url as profile_pic_url, users.admin_controls as admin_controls FROM posts LEFT JOIN users ON users.id = posts.users_id WHERE thread_id = :id")
            result = db.session.execute(sql, {"id":id})
            posts = result.fetchall()
            return render_template('/forum/single.html', thread = thread, posts = posts)
        
        except Exception as e:
            print(e)
            flash('An error has occurred.', 'error')
            return redirect(url_for('forum.index'))
        
# Create Thread API, Does not render any page
@forum_bp.route('/api/create', methods = ["POST"])
def createThread():
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to create a thread.', 'error')
                return redirect(url_for('forum.index'))
            
            sql = text("INSERT INTO Threads (title, content, users_id, edited) VALUES (:title, :content, :users_id, 0)")
            db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"), "users_id":session['user_id']})
            db.session.commit()
            flash('Your thread has been posted!.', 'success')
            return redirect(url_for('forum.index'))
        
        except Exception as e:
            print(e)
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.index'))

# Reply API, Does not render any page
@forum_bp.route('/api/reply', methods = ["POST"])
def reply():
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to reply to this thread.', 'error')
                return redirect(url_for('forum.index'))
            
            sql = text("INSERT INTO posts (content, users_id, thread_id, edited) VALUES (:content, :users_id, :thread_id, 0)")
            db.session.execute(sql, {"content":request.form.get("content"), "users_id":session['user_id'], "thread_id":request.form.get("thread_id")})
            db.session.commit()
            flash('Your reply has been posted!.', 'success')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        except Exception as e:
            print(e)
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))

# Delete Thread API, Does not render any page
@forum_bp.route('/api/delete/<int:id>', methods = ["GET"])
def deleteThread(id):
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to delete thread.', 'error')
                return redirect(url_for('forum.index'))
            
            sql = text("DELETE FROM Threads WHERE id = :id")
            db.session.execute(sql, {"id":id})
            db.session.commit()
            
            sql = text("DELETE FROM posts WHERE thread_id = :id")
            db.session.execute(sql, {"id":id})
            db.session.commit()
            
            flash('Your thread has been deleted!.', 'success')
            return redirect(url_for('forum.index'))
        
        except Exception as e:
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.index'))

# Delete Thread API, Does not render any page
@forum_bp.route('/api/deletereply/<int:id>/<int:thread_id>', methods = ["GET"])
def deleteReply(id, thread_id):
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to delete thread.', 'error')
                return redirect(url_for('forum.single', id=thread_id))

            sql = text("DELETE FROM posts WHERE id = :id")
            db.session.execute(sql, {"id":id})
            db.session.commit()
            
            flash('Your reply has been deleted!.', 'success')
            return redirect(url_for('forum.single', id=thread_id))
        
        except Exception as e:
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.single', id=thread_id))

# Edit Thread API, Does not render any page
@forum_bp.route('/api/editThread', methods = ["POST"])
def editThread():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to create a thread.', 'error')
                return redirect(url_for('forum.index'))
            
            sql = text("UPDATE Threads SET title = :title, content = :content, edited = 1, edited_time = :edited_time WHERE id = :id")
            db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"),"edited_time":current_time, "id":request.form.get("thread_id")})
            db.session.commit()
            flash('Your thread has been updated!.', 'success')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        
        except Exception as e:
            print(e)
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        
# Edit Reply API, Does not render any page
@forum_bp.route('/api/editReply', methods = ["POST"])
def editReply():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with current_app.app_context():
        try:
            # Ensure user is logged in
            if 'user_id' not in session:
                flash('You must be logged in to create a thread.', 'error')
                return redirect(url_for('forum.index'))
            
            sql = text("UPDATE posts SET content = :content, edited = 1, edited_time = :edited_time WHERE id = :id")
            db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"),"edited_time":current_time, "id":request.form.get("post_id")})
            db.session.commit()
            flash('Your reply has been updated!.', 'success')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        
        except Exception as e:
            print(e)
            flash('An error has occurred, please try again.', 'error')
            return redirect(url_for('forum.single', id=request.form.get("thread_id")))