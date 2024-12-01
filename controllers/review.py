from flask import Blueprint, render_template, flash, request, redirect, url_for, session, current_app
import config.constants
from config.dbConnect import get_db, get_client_and_db
from controllers.user import user_bp
from bson import ObjectId, Timestamp
import json
from datetime import datetime
import tracemalloc


reviews_bp = Blueprint('review', __name__, template_folder=config.constants.template_dir,
                       static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/review')



@reviews_bp.route('/api/add', methods=['POST'])
async def add():
    tracemalloc.start()

    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movie_id = request.form.get('movie_id')
    db = await get_db()

    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to be logged in to post a review.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']

    # Fetch existing reviews for this movie (for demonstration purposes)
    review_query = {"movies_id": ObjectId(movie_id)}
    review_cursor = db.reviews.find(review_query, {"body": 1, "rating": 1})

    # Run `explain()` to analyze the query performance
    explain_find = await review_cursor.explain()
    reviews = await review_cursor.to_list(length=1)  # Fetch existing reviews if needed

    # Insert a new review
    review = {
        "body": body,
        "rating": rating,
        "movies_id": ObjectId(movie_id),
        "users_id": ObjectId(user_id),
        "review_timestamp": datetime.now()
    }
    insert_result = await db.reviews.insert_one(review)

    explain_insert = await db.reviews.find({"_id": insert_result.inserted_id}).explain()

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    flash('Review posted successfully!', 'success')

    # get execution stats
    def extract_key_metrics(stats):
        return {
            "executionSuccess": stats.get("executionSuccess"),
            "executionTimeMillis": stats.get("executionTimeMillis"),
            "totalKeysExamined": stats.get("totalKeysExamined"),
            "totalDocsExamined": stats.get("totalDocsExamined")
        }

    # Log simplified execution stats
    current_app.logger.info(
        "Add Review \nFind Query Execution Stats:\n%s",
        json.dumps(extract_key_metrics(explain_find.get("executionStats", {})), indent=4)
    )
    current_app.logger.info(
        "Add Review \nInsert Query Execution Stats:\n%s",
        json.dumps(extract_key_metrics(explain_insert.get("executionStats", {})), indent=4)
    )
    # Log memory usage
    current_app.logger.info(f"\n'Add Review' Memory Usage: Current = {current / 1024:.2f} KB, Peak = {peak / 1024:.2f} KB\n")

    return redirect(url_for('movie.single', id=movie_id))


@reviews_bp.route('/edit/<string:id>', methods=['GET'])
async def edit(id):
    users_id = session.get('user_id')  # Get the current user ID

    db = await get_db()
    review = await db.reviews.find_one(
        {"_id": ObjectId(id), "users_id": ObjectId(users_id)},  # Filter by both _id and user_id
        {"body": 1, "rating": 1, "movies_id": 1, "users_id": 1}  # Fields to return
    )

    if review is None:
        flash('Review not found or you do not have the permission to edit', 'error')
        return redirect(url_for('index.index'))

    return render_template('review/edit.html', review=review)


@reviews_bp.route('/api/update', methods=['POST'])
async def update():
    body = request.form.get('review')
    rating = int(request.form.get('rating'))
    movie_id = ObjectId(request.form.get('movie_id'))
    users_id = ObjectId(session.get('user_id'))  # Get the current user ID
    review_id = ObjectId(request.form.get('review_id'))
    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                review = await db.reviews.find_one({"_id": review_id, "users_id": users_id})

                if review is None:
                    flash("You do not have permission to edit this review.", "error")
                    return redirect(url_for('movie.single', id=movie_id))

                await db.reviews.update_one(
                    {"_id": review_id},  # Find the review by ID
                    {"$set": {"body": body, "rating": rating}}, session=client_session  # Set new body and rating
                )

                flash('Review updated successfully!')
                return redirect(url_for('movie.single', id=movie_id))

            except Exception as e:
                flash("An error occurred while updating the review", "error")
                return redirect(url_for('movie.single', id=movie_id))


@reviews_bp.route('/api/delete/<string:id>', methods=['POST'])
async def delete(id):
    users_id = ObjectId(session.get('user_id'))  # Get the current user ID
    review_id = ObjectId(id)
    movie_id = request.form.get('movie_id')
    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                review = await db.reviews.find_one({"_id": review_id, "users_id": users_id})
                if not review:
                    flash("You do not have permission to edit this review.", "error")
                    return redirect(url_for('movie.single', id=movie_id))

                await db.reviews.delete_one({"_id": review_id, "users_id": users_id}, session=client_session)

                flash('Review deleted successfully!')
                return redirect(url_for('movie.single', id=movie_id))

            except Exception as e:
                flash("An error occurred while updating the review", "error")
                return redirect(url_for('movie.single', id=movie_id))
