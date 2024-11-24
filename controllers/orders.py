from flask import Blueprint, request, redirect, url_for, session, flash, current_app
from config.dbConnect import get_db
from datetime import datetime
from bson import ObjectId

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


# API to add an order, won't render any page
@orders_bp.route('/api/add', methods=['POST'])
async def post_add_order():
    rq = request.form
    movie_id = rq.get('movie_id')
    db = await get_db()

    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to be logged in to add items to the cart.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']

    # Fetch the movie to get the price
    movie = await db.Movies.find_one({"_id": ObjectId(movie_id)}, {"price": 1})

    if movie:
        total_price = movie['price']

        # Insert the order into the orders collection
        order = {
            "movie_id": ObjectId(movie_id),
            "order_timestamp": datetime.now(),
            "total_price": total_price,
            "users_id": ObjectId(user_id)
        }
        await db.orders.insert_one(order)

        flash('Movie added to cart successfully.', 'success')
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