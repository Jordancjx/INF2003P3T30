from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from sqlalchemy import text
from config.dbConnect import db
from datetime import datetime
import config.constants
from models.purchases import Purchases, History
from models.order import Order
from models.movie import Movie 

# Define the Blueprint for purchases
purchases_bp = Blueprint('purchases', __name__, template_folder=config.constants.template_dir,
                         static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/purchases')

# Payment Form
@purchases_bp.route('/api/payment', methods=['GET'])
def payment():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to proceed with payment.", "error")
        return redirect(url_for('user.login'))

    # Get the total sum from the query parameter
    total_sum = request.args.get('total_sum', 0)

    # Render the payment form
    return render_template('/user/payment.html', total_sum=total_sum)

# Process payment
@purchases_bp.route('/api/payment', methods=['POST'])
def process_payment():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to proceed with payment.", 'error')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    full_name = request.form.get('full_name')
    card_pin = request.form.get('card_pin')
    total_sum = request.form.get('total_sum')

    with current_app.app_context():
        try:
            # Insert the payment into the purchases table
            new_purchase = Purchases(
                card_number=card_number,
                expiry_date=expiry_date,
                full_name=full_name,
                card_pin=card_pin,
                amount=total_sum,
                users_id=user_id
            )
            db.session.add(new_purchase)
            db.session.commit()

            # Get the ID of the newly inserted purchase
            purchase_id = new_purchase.id

            # Fetch current user's orders from the orders table
            cart_items = db.session.query(Order, Movie).join(Movie, Order.movie_id == Movie.id).filter(Order.users_id == user_id).all()

            # Insert each order into the history table
            for order, movie in cart_items:
                history_item = History(
                    purchase_id=purchase_id,
                    movie_id=order.movie_id,
                    movie_name=movie.name,
                    price=order.total_price
                )
                db.session.add(history_item)

            # Delete the purchased items from the orders table
            db.session.query(Order).filter_by(users_id=user_id).delete()

            # Commit all changes
            db.session.commit()

            flash('Payment processed successfully.', 'success')
            return redirect(request.referrer)
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during the payment process.', 'error')
            return redirect(url_for('user.cart'))

#order history
@purchases_bp.route('/history')
def view_history():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your order history.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    
    with current_app.app_context():
        # Fetch user's order history by joining history and purchases tables
        history_items = db.session.query(History, Purchases.purchase_timestamp).join(Purchases, History.purchase_id == Purchases.id).filter(Purchases.users_id == user_id).all()

    # Render the history.html template, passing the fetched history items
    return render_template('/user/history.html', history_items=history_items)