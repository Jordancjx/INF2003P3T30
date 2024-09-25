from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

admin_bp = Blueprint('admin', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/admin')


# Dashboard
@admin_bp.route('/')
def adminIndex():
    users = User.query.all()
    return render_template('/admin/dashboard.html', users=users)


# Delete User API
@admin_bp.route('/delete_user', methods=["POST"])
def deleteUser():
    user = User.query.get_or_404(request.form.get('user_id'))
    db.session.delete(user)  # Delete the user from the database
    db.session.commit()  # Commit changes to the database
    flash('User deleted successfully!')

    return redirect(url_for('admin.adminIndex'))


# Make User Admin
@admin_bp.route('/admin_user', methods=["POST"])
def adminUser():
    user = User.query.get_or_404(request.form.get('user_id'))

    # Change admin_controls to True
    user.admin_controls = True
    db.session.commit()  # Commit changes to the database
    flash('Granted admin privileges successfully!')

    return redirect(url_for('admin.adminIndex'))


# Revoke Admin Access
@admin_bp.route('/revoke_admin', methods=["POST"])
def revokeUser():
    user = User.query.get_or_404(request.form.get('user_id'))

    # Change admin_controls to True
    user.admin_controls = False
    db.session.commit()  # Commit changes to the database
    flash('Revoked admin privileges successfully')

    return redirect(url_for('admin.adminIndex'))
