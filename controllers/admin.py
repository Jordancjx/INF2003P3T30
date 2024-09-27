from flask import Blueprint, render_template, current_app, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/admin')


# Dashboard
@admin_bp.route('/')
def adminIndex():
    with current_app.app_context():
        sql = text("SELECT * FROM users")
        result = db.session.execute(sql)
        users = result.fetchall()
        return render_template('/admin/dashboard.html', users=users)


# Delete User API
@admin_bp.route('/delete_user', methods=["POST"])
def deleteUser():
    with current_app.app_context():
        sql = text("DELETE FROM users WHERE id = :id")
        db.session.execute(sql, {"id": request.form.get('user_id')})
        db.session.commit()  # Commit changes to the database
        flash('User deleted successfully!')

        return redirect(url_for('admin.adminIndex'))


# Make User Admin
@admin_bp.route('/admin_user', methods=["POST"])
def adminUser():
    with current_app.app_context():
        sql = text("UPDATE users SET admin_controls = 1 WHERE id = :id")
        db.session.execute(sql, {"id": request.form.get('user_id')})
        db.session.commit()
        flash('Granted admin privileges successfully!')

        return redirect(url_for('admin.adminIndex'))


# Revoke Admin Access
@admin_bp.route('/revoke_admin', methods=["POST"])
def revokeUser():
    with current_app.app_context():
        sql = text("UPDATE users SET admin_controls = 0 WHERE id = :id")
        db.session.execute(sql, {"id": request.form.get('user_id')})
        db.session.commit()
        flash('Revoked admin privileges successfully')

        return redirect(url_for('admin.adminIndex'))
