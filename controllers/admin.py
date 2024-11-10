from bson import ObjectId
from flask import Blueprint, render_template, current_app, request, jsonify, session, redirect, url_for, flash
import config.constants

admin_bp = Blueprint('admin', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/admin')


# Dashboard
@admin_bp.route('/')
def adminIndex():
    db = current_app.mongo.db
    with current_app.app_context():
        users = list(db.users.find({}))
        return render_template('/admin/dashboard.html', users=users)


# Delete User API
@admin_bp.route('/delete_user', methods=["POST"])
def deleteUser():
    db = current_app.mongo.db
    with current_app.app_context():
        result = db.users.delete_one({"_id": ObjectId(id)})

        if result.deleted_count > 0:
            flash('User deleted successfully!')

        else:
            flash('Error deleting user')

        return redirect(url_for('admin.adminIndex'))


# Make User Admin
@admin_bp.route('/admin_user', methods=["POST"])
def adminUser():
    db = current_app.mongo.db
    with current_app.app_context():
        db.users.update_one({"_id": ObjectId(request.form.get('user_id'))},
                            {'$set': {"admin_controls": 1}})

        flash('Granted admin privileges successfully!')

        return redirect(url_for('admin.adminIndex'))


# Revoke Admin Access
@admin_bp.route('/revoke_admin', methods=["POST"])
def revokeUser():
    db = current_app.mongo.db
    with current_app.app_context():
        db.users.update_one({"_id": ObjectId(request.form.get('user_id'))},
                            {'$set': {"admin_controls": 0}})

        flash('Revoked admin privileges successfully')

        return redirect(url_for('admin.adminIndex'))
