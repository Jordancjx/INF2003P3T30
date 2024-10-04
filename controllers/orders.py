from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from sqlalchemy import text
from config.dbConnect import db
from datetime import datetime
from models.order import Order

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# API to add an order, won't render any page
@orders_bp.route('/api/add', methods=['POST'])
def post_add_order():
    rq = request.form
    movie_id = rq.get('movie_id')

    with current_app.app_context():
        # Check if the user is logged in
        if 'user_id' not in session:
            flash('You need to be logged in to add items to the cart.', 'warning')
            return redirect(url_for('user.login'))

        user_id = session['user_id']

        # Fetch the movie to get the price
        sql = text("SELECT price FROM movies WHERE id = :movie_id")
        result = db.session.execute(sql, {"movie_id": movie_id})
        movie = result.fetchone()

        if movie:
            total_price = movie.price

            # Insert the order into the orders table
            sql_order = text(
                "INSERT INTO orders (movie_id, order_timestamp, total_price, users_id) "
                "VALUES (:movie_id, :order_timestamp, :total_price, :users_id)"
            )
            db.session.execute(sql_order, {
                "movie_id": movie_id,
                "order_timestamp": datetime.utcnow(),
                "total_price": total_price,
                "users_id": user_id
            })
            db.session.commit()

            flash('Movie added to cart successfully.', 'success')
            return redirect(request.referrer)
        else:
            flash('Movie not found.', 'error')
            return redirect(request.referrer)


@orders_bp.route('/api/remove', methods=['POST'])
def remove_movie():
    order_id = request.form.get('order_id')

    if order_id:
        # Query the database to find the order by ID
        order = Order.query.filter_by(id=order_id).first()

        if order:
            # Remove the order from the database
            db.session.delete(order)
            db.session.commit()
            # Redirect back to the cart page after removal
            return redirect(url_for('user.cart'))  # Replace 'cart_page' with the correct view function name

    flash('Order not found', 'error')
    # If order is not found, redirect to the cart page
    return redirect(url_for('user.cart'))  # Replace 'cart_page' with the correct view function name


@orders_bp.route('/api/clear-all', methods=['POST'])
def clear_all():
    if 'user_id' in session:
        user_id = session.get('user_id')
        db.session.query(Order).filter_by(users_id=user_id).delete()
        db.session.commit()

        flash('Cart cleared', 'success')
        return redirect(url_for('user.cart'))

    flash('Please log in', 'error')
    return redirect(url_for('user.cart'))
