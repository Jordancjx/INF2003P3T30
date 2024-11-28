from flask import Blueprint, render_template, current_app, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import get_db, get_client_and_db
from datetime import datetime, timezone
from bson import ObjectId

forum_bp = Blueprint('forum', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/forum')


# Dashboard
@forum_bp.route('/')
async def index():
    db = await get_db()

    # fetch all threads with user information
    threads = await db.threads.aggregate([
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
                "created_time": 1,
                "user_info.username": 1,
                "user_info._id": 1,
                "edited_time": 1,
            }
        }

    ]).to_list(length=None)

    return render_template('/forum/forum.html', threads=threads)


# Single page for threads
@forum_bp.route('/single/<string:id>', methods=["GET"])
async def single(id):
    db = await get_db()

    try:
        # Fetch single thread with user info
        thread = await db.threads.aggregate([
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
                    "created_time": 1,
                    "users_id": {"$toString": "$users_id"},
                    "user_info.username": 1,
                    "user_info.email": 1,
                    "user_info.profile_pic_url": 1,
                    "user_info.admin_controls": 1,
                    "edited": 1,
                    "edited_time": 1,
                }
            }
        ]).next()

        # Fetch posts for the threads with user info
        posts = await db.posts.aggregate([
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
                    "posted_time": 1,
                    "users_id": {"$toString": "$users_id"},
                    "user_info.username": 1,
                    "user_info.email": 1,
                    "user_info.profile_pic_url": 1,
                    "user_info.admin_controls": 1,
                    "edited": 1,
                    "edited_time": 1,
                }
            }
        ]).to_list(length=None)

        return render_template('/forum/single.html', thread=thread, posts=posts)

    except Exception as e:
        print(e)
        flash('An error has occurred.', 'error')
        return redirect(url_for('forum.index'))


# Create Thread API, Does not render any page
@forum_bp.route('/api/create', methods=["POST"])
async def createThread():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to create a thread.', 'error')
        return redirect(url_for('forum.index'))

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:

                thread_data = {
                    "title": request.form.get("title"),
                    "content": request.form.get("content"),
                    "users_id": ObjectId(session['user_id']),
                    "created_time": datetime.now(timezone.utc),
                    "edited": False
                }
                await db.threads.insert_one(thread_data, session=client_session)
                flash('Your thread has been posted!', 'success')
                return redirect(url_for('forum.index'))

            except Exception as e:
                print(e)
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.index'))


# Reply API, Does not render any page
@forum_bp.route('/api/reply', methods=["POST"])
async def reply():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to reply to this thread.', 'error')
        return redirect(url_for('forum.index'))

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                post_data = {
                    "content": request.form.get("content"),
                    "users_id": ObjectId(session['user_id']),
                    "thread_id": ObjectId(request.form.get("thread_id")),
                    "posted_time": datetime.now(timezone.utc),
                    "edited": False

                }
                await db.posts.insert_one(post_data, session=client_session)
                flash('Your reply has been posted!', 'success')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))

            except Exception as e:
                print(e)
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))


# Delete Thread API, Does not render any page
@forum_bp.route('/api/delete/<string:id>', methods=["GET"])
async def deleteThread(id):
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to delete thread.', 'error')
        return redirect(url_for('forum.index'))

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.threads.delete_one({"_id": ObjectId(id)}, session=client_session)
                await db.posts.delete_many({"thread_id": ObjectId(id)}, session=client_session)
                flash('Your thread has been deleted!', 'success')
                return redirect(url_for('forum.index'))

            except Exception as e:
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.index'))


# Delete Reply API, Does not render any page
@forum_bp.route('/api/deletereply/<string:id>/<string:thread_id>', methods=["GET"])
async def deleteReply(id, thread_id):
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to delete thread.', 'error')
        return redirect(url_for('forum.single', id=thread_id))

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.posts.delete_one({"_id": ObjectId(id)}, session=client_session)
                flash('You reply has been deleted!', 'success')
                return redirect(url_for('forum.single', id=thread_id))

            except Exception as e:
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.single', id=thread_id))


# Edit Thread API, Does not render any page
@forum_bp.route('/api/editThread', methods=["POST"])
async def editThread():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to create a thread.', 'error')
        return redirect(url_for('forum.index'))

    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.threads.update_one(
                    {"_id": ObjectId(request.form.get("thread_id"))},
                    {
                        "$set": {
                            "title": request.form.get("title"),
                            "content": request.form.get("content"),
                            "edited": True,
                            "edited_time": datetime.now(timezone.utc)
                        }
                    }, session=client_session
                )
                flash('Your thread has been updated!', 'success')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))


            except Exception as e:
                print(e)
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))


# Edit Reply API, Does not render any page
@forum_bp.route('/api/editReply', methods=["POST"])
async def editReply():
    client, db = await get_client_and_db()
    # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                # Ensure user is logged in
                if 'user_id' not in session:
                    flash('You must be logged in to create a thread.', 'error')
                    return redirect(url_for('forum.index'))

                await db.posts.update_one(
                    {"_id": ObjectId(request.form.get("post_id"))},
                    {
                        "$set": {
                            "content": request.form.get("content"),
                            "edited": True,
                            "edited_time": datetime.now(timezone.utc)
                        }
                    }, session=client_session
                )
                flash('Your reply has been updated', 'success')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))

            except Exception as e:
                print(e)
                flash('An error has occurred, please try again.', 'error')
                return redirect(url_for('forum.single', id=request.form.get("thread_id")))
