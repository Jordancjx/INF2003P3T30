from flask import Blueprint, render_template, current_app, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from datetime import datetime, timezone
from bson import ObjectId

forum_bp = Blueprint('forum', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/forum')


# Dashboard
@forum_bp.route('/')
def index():
    db = current_app.mongo.db

    #fetch all threads with user information
    threads = list(db.threads.aggregate([
        {
            "$lookup": {
                "from": "users",
                "localField": "users_id",
                "foreignField": "_id",
                "as": "user_info"
            }
        },
        {
            "$unwind": "$user_info"
        },
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "content": 1,
                "created_at": 1,
                "user_info.username": 1,
                "user_info._id": 1
            }
        }

    ]))

    return render_template('/forum/forum.html', threads = threads)

    # with current_app.app_context():
    #     sql = text("SELECT threads.*, users.id as user_id, users.username as username FROM threads LEFT JOIN users ON users.id = threads.users_id")
    #     result = db.session.execute(sql)
    #     threads = result.fetchall()
    

# Single page for threads
@forum_bp.route('/single/<string:id>', methods = ["GET"])
def single(id):
    db = current_app.mongo.db

    try:  
        #Fetch single thread with user info
        thread = db.threads.aggregate([
            {"$match": {"_id": ObjectId(id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "users_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {
            "$unwind": "$user_info"
            },
            {
                "$project": {
                    "_id": 1,
                    "title": 1,
                    "content": 1,
                    "created_at": 1,
                    "user_info.username": 1,
                    "user_info.email": 1,
                    "user_info.profile_pic_url": 1,
                    "user_info.admin_controls": 1
                }
            }
        ]).next()

        #Fetch posts for the threads with user info
        posts = list(db.posts.aggregate([
            {"$match": {"thread_id": ObjectId(id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "users_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {
            "$unwind": "$user_info"
            },
            {
                "$project": {
                    "content": 1,
                    "created_at": 1,
                    "user_info.username": 1,
                    "user_info.email": 1,
                    "user_info.profile_pic_url": 1,
                    "user_info.admin_controls": 1
                }
            }
        ]))

        return render_template('/forum/single.html', thread = thread, posts = posts)

    except Exception as e:
            print(e)
            flash('An error has occurred.', 'error')
            return redirect(url_for('forum.index'))
    
    #with current_app.app_context():
    # sql = text("SELECT threads.*, users.id as user_id, users.username as username, users.email as email, users.profile_pic_url as profile_pic_url, users.admin_controls as admin_controls FROM threads LEFT JOIN users ON users.id = threads.users_id WHERE threads.id = :thread_id")
            # result = db.session.execute(sql, {"thread_id":id})
            # thread = result.fetchone()
            
            # sql = text("SELECT posts.*,users.id as user_id, users.username as username, users.email as email, users.profile_pic_url as profile_pic_url, users.admin_controls as admin_controls FROM posts LEFT JOIN users ON users.id = posts.users_id WHERE thread_id = :id")
            # result = db.session.execute(sql, {"id":id})
            # posts = result.fetchall()
        
        
        
# Create Thread API, Does not render any page
@forum_bp.route('/api/create', methods = ["POST"])
def createThread():
    db = current_app.mongo.db

    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to create a thread.', 'error')
            return redirect(url_for('forum.index'))

        thread_data = {
            "title": request.form.get("title"),
            "content": request.form.get("content"),
            "users_id": ObjectId(session['user_id']),
            "created_time": datetime.now(timezone.utc),
            "edited": False
        }
        db.threads.insert_one(thread_data)
        flash('Your thread has been posted!', 'success')
        return redirect(url_for('forum.index'))
            
    except Exception as e:
        print(e)
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.index'))
    
    #with current_app.app_context():
    # sql = text("INSERT INTO Threads (title, content, users_id, edited) VALUES (:title, :content, :users_id, 0)")
    # db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"), "users_id":session['user_id']})
    # db.session.commit()
    # flash('Your thread has been posted!.', 'success')
    # return redirect(url_for('forum.index'))

# Reply API, Does not render any page
@forum_bp.route('/api/reply', methods = ["POST"])
def reply():
    db = current_app.mongo.db
    
    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to reply to this thread.', 'error')
            return redirect(url_for('forum.index'))
        
        post_data = {
            "content": request.form.get("content"),
            "users_id": ObjectId(session['user_id']),
            "thread_id": ObjectId(request.form.get("thread_id")),
            "posted_time": datetime.now(timezone.utc),
            "edited": False
            
        }
        db.posts.insert_one(post_data)
        flash('Your reply has been posted!', 'success')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        
            
    except Exception as e:
        print(e)
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))
    
    #with current_app.app_context():
    # sql = text("INSERT INTO posts (content, users_id, thread_id, edited) VALUES (:content, :users_id, :thread_id, 0)")
    # db.session.execute(sql, {"content":request.form.get("content"), "users_id":session['user_id'], "thread_id":request.form.get("thread_id")})
    # db.session.commit()
    # flash('Your reply has been posted!.', 'success')
    # return redirect(url_for('forum.single', id=request.form.get("thread_id")))

# Delete Thread API, Does not render any page
@forum_bp.route('/api/delete/<int:id>', methods = ["GET"])
def deleteThread(id):
    db = current_app.mongo.db
    
    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to delete thread.', 'error')
            return redirect(url_for('forum.index'))
        
        db.threads.delete_one({"_id": ObjectId(id)})
        db.posts.delete_many({"thread_id": ObjectId(id)})
        flash('Your thread has been deleted!', 'success')
        return redirect(url_for('forum.index'))
            
        
    except Exception as e:
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.index'))
    
    #with current_app.app_context():
    # sql = text("DELETE FROM Threads WHERE id = :id")
    #         db.session.execute(sql, {"id":id})
    #         db.session.commit()
            
    #         sql = text("DELETE FROM posts WHERE thread_id = :id")
    #         db.session.execute(sql, {"id":id})
    #         db.session.commit()
            
    #         flash('Your thread has been deleted!.', 'success')
    #         return redirect(url_for('forum.index'))


# Delete Reply API, Does not render any page
@forum_bp.route('/api/deletereply/<int:id>/<int:thread_id>', methods = ["GET"])
def deleteReply(id, thread_id):
    db = current_app.mongo.db
    #with current_app.app_context():
    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to delete thread.', 'error')
            return redirect(url_for('forum.single', id=thread_id))
        
        db.posts.delete_one({"_id": ObjectId(id)})
        flash('You reply has been deleted!', 'success')
        return redirect(url_for('forum.single', id=thread_id))
        
    except Exception as e:
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.single', id=thread_id))
    
     # sql = text("DELETE FROM posts WHERE id = :id")
            # db.session.execute(sql, {"id":id})
            # db.session.commit()
            
            # flash('Your reply has been deleted!.', 'success')
            # return redirect(url_for('forum.single', id=thread_id))


# Edit Thread API, Does not render any page
@forum_bp.route('/api/editThread', methods = ["POST"])
def editThread():
    db = current_app.mongo.db
    
    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to create a thread.', 'error')
            return redirect(url_for('forum.index'))
    
        db.threads.update_one(
            {"_id": ObjectId(request.form.get("thread_id"))},
            {
                "$set": {
                "title": request.form.get("title"),
                "content": request.form.get("content"),
                "edited": True,
                "edited_time": datetime.now(timezone.utc)
                }
            }
        )  
        flash('Your thread has been updated!', 'success')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))
            
    
    except Exception as e:
        print(e)
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))

    #current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #with current_app.app_context():
    # sql = text("UPDATE Threads SET title = :title, content = :content, edited = 1, edited_time = :edited_time WHERE id = :id")
    #         db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"),"edited_time":current_time, "id":request.form.get("thread_id")})
    #         db.session.commit()
    #         flash('Your thread has been updated!.', 'success')
    #         return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        
        
# Edit Reply API, Does not render any page
@forum_bp.route('/api/editReply', methods = ["POST"])
def editReply():
    db = current_app.mongo.db
    # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # with current_app.app_context():
    try:
        # Ensure user is logged in
        if 'user_id' not in session:
            flash('You must be logged in to create a thread.', 'error')
            return redirect(url_for('forum.index'))
        
        db.posts.update_one(
            {"_id": ObjectId(request.form.get("post_id"))},
            {
                "$set": {
                "content": request.form.get("content"),
                "edited": True,
                "edited_time": datetime.now(timezone.utc)
                }
            }
        )  
        flash('Your reply has been updated', 'success')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))
            
    except Exception as e:
        print(e)
        flash('An error has occurred, please try again.', 'error')
        return redirect(url_for('forum.single', id=request.form.get("thread_id")))


    # sql = text("UPDATE posts SET content = :content, edited = 1, edited_time = :edited_time WHERE id = :id")
    #         db.session.execute(sql, {"title":request.form.get("title"), "content":request.form.get("content"),"edited_time":current_time, "id":request.form.get("post_id")})
    #         db.session.commit()
    #         flash('Your reply has been updated!.', 'success')
    #         return redirect(url_for('forum.single', id=request.form.get("thread_id")))
        