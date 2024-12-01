from flask import Blueprint, request, redirect, url_for, session, flash, current_app
from config.dbConnect import get_db
from datetime import datetime
from bson import ObjectId, Timestamp
import json
import tracemalloc


orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# API to add an order, won't render any page
@orders_bp.route('/api/add', methods=['POST'])
async def post_add_order():
    tracemalloc.start()

    rq = request.form
    movie_id = rq.get('movie_id')
    db = await get_db()

    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to be logged in to add items to the cart.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']

    # Fetch the movie to get the price
    movie_query = {"_id": ObjectId(movie_id)}
    movie_cursor = db.Movies.find(movie_query, {"price": 1})
    
    # Run `explain()` to analyze the query performance
    explain_find = await movie_cursor.explain()
    movie = await movie_cursor.to_list(length=1)  # Fetch the result

    if movie:
        total_price = movie[0]['price']

        # Insert the order into the orders collection
        order = {
            "movie_id": ObjectId(movie_id),
            "order_timestamp": datetime.now(),
            "total_price": total_price,
            "users_id": ObjectId(user_id)
        }
        insert_result = await db.orders.insert_one(order)

        # Run `explain()` to analyze the performance of the insert operation
        explain_insert = await db.orders.find({"_id": insert_result.inserted_id}).explain()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        flash('Movie added to cart successfully.', 'success')

            # get execution stats
        def extract_key_metrics(stats):
            return {
                "executionSuccess": stats.get("executionSuccess"),
                "executionTimeMillis": stats.get("executionTimeMillis"),
                "totalKeysExamined": stats.get("totalKeysExamined"),
                "totalDocsExamined": stats.get("totalDocsExamined")
            }

        # Log only the executionStats section with operation context
        current_app.logger.info(
            "Add to Cart \nFind Query Execution Stats:\n%s",
            json.dumps(extract_key_metrics(explain_find.get("executionStats", {})), indent=4)
        )
        current_app.logger.info(
            "Add to Cart \nInsert Query Execution Stats:\n%s",
            json.dumps(extract_key_metrics(explain_insert.get("executionStats", {})), indent=4)
        )
        current_app.logger.info(f"\n'Add to Cart' Memory Usage: Current = {current / 1024:.2f} KB, Peak = {peak / 1024:.2f} KB\n")

        return redirect(request.referrer)
    else:
        flash('Movie not found.', 'error')
        return redirect(request.referrer)




@orders_bp.route('/api/remove', methods=['POST'])
async def remove_movie():
    order_id = request.form.get('order_id')
    db = await get_db()

    if order_id:
        # Remove the order from the orders collection
        result = await db.orders.delete_one({"_id": ObjectId(order_id)})

        if result.deleted_count > 0:
            flash('Movie removed from cart successfully.', 'success')
            return redirect(url_for('user.cart'))
        else:
            flash('Order not found', 'error')
            return redirect(url_for('user.cart'))


@orders_bp.route('/api/clear-all', methods=['POST'])
async def clear_all():
    db = await get_db()

    if 'user_id' in session:
        user_id = session.get('user_id')
        
        # Remove all orders associated with the user
        await db.orders.delete_many({"users_id": ObjectId(user_id)})

        flash('Cart cleared', 'success')
        return redirect(url_for('user.cart'))

    flash('Please log in', 'error')
    return redirect(url_for('user.cart'))