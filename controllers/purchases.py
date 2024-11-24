from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
import config.constants
from config.dbConnect import get_db
from bson import ObjectId

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


@purchases_bp.route('/api/payment', methods=['POST'])
async def process_payment():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to proceed with payment.", 'error')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    full_name = request.form.get('full_name')
    card_pin = request.form.get('card_pin')

    db = await get_db()

    try:
        # Calculate total_sum based on the user's cart items
        orders = await db.orders.find({"users_id": ObjectId(user_id)}).to_list(length=None)
        total_sum = sum(order["total_price"] for order in orders)

        # Insert the payment into the purchases collection
        new_purchase = {
            "card_number": card_number,
            "expiry_date": expiry_date,
            "full_name": full_name,
            "card_pin": card_pin,
            "amount": total_sum,
            "users_id": ObjectId(user_id),
            "purchase_timestamp": datetime.now()
        }
        purchase_result = await db.purchases.insert_one(new_purchase)
        purchase_id = purchase_result.inserted_id

        # Fetch current user's orders from the orders collection
        cart_items = await db.orders.find({"users_id": ObjectId(user_id)}).to_list(length=None)

        # Insert each order into the history collection
        for order in cart_items:
            movie = await db.Movies.find_one({"_id": ObjectId(order["movie_id"])})
            if movie:
                history_item = {
                    "purchase_id": ObjectId(purchase_id),
                    "movie_id": ObjectId(order["movie_id"]),
                    "movie_name": movie["title"],
                    "price": order["total_price"]
                }
                await db.history.insert_one(history_item)

        # Delete the purchased items from the orders collection
        await db.orders.delete_many({"users_id": ObjectId(user_id)})

        flash('Payment processed successfully.', 'success')
        return redirect(url_for('purchases.view_history'))

    except Exception as e:
        print(e)
        flash('An error occurred during the payment process.', 'error')
        return redirect(url_for('user.cart'))


#order history
@purchases_bp.route('/history')
async def view_history():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your order history.", "error")
        return redirect(url_for('user.login'))

    user_id = session['user_id']

    db = await get_db()

    # Fetch user's order history by joining history and purchases collections
    history_items = await db.history.aggregate([
        {
            "$lookup": {
                "from": "purchases",
                "localField": "purchase_id",
                "foreignField": "_id",
                "as": "purchase_info"
            }
        },
        {
            "$match": {"purchase_info.users_id": ObjectId(user_id)}
        },
        {
            "$unwind": "$purchase_info"
        },
        {
            "$project": {
                "movie_name": 1,
                "price": 1,
                "purchase_timestamp": "$purchase_info.purchase_timestamp"
            }
        }
    ]).to_list(length=None)

    # Render the history.html template, passing the fetched history items
    return render_template('/user/history.html', history_items=history_items)