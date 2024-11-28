from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, url_for, flash
import config.constants
from config.dbConnect import get_db, get_client_and_db

admin_bp = Blueprint('admin', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/admin')


# Dashboard
@admin_bp.route('/')
async def adminIndex():
    db = await get_db()

    users = await db.users.find({}).to_list(length=None)
    return render_template('/admin/dashboard.html', users=users)


# Delete User API
@admin_bp.route('/delete_user', methods=["POST"])
async def deleteUser():
    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.users.delete_one({"_id": ObjectId(id)}, session=client_session)
                flash('User deleted successfully!')
                return redirect(url_for('admin.adminIndex'))

            except Exception:
                flash('Error deleting user', 'error')
                return redirect(url_for('admin.adminIndex'))

# Make User Admin
@admin_bp.route('/admin_user', methods=["POST"])
async def adminUser():
    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.users.update_one({"_id": ObjectId(request.form.get('user_id'))},
                                          {'$set': {"admin_controls": 1}}, session=client_session)

                flash('Granted admin privileges successfully!', 'success')
                return redirect(url_for('admin.adminIndex'))

            except Exception:
                flash('Error granting privileges', 'error')
                return redirect(url_for('admin.adminIndex'))


# Revoke Admin Access
@admin_bp.route('/revoke_admin', methods=["POST"])
async def revokeUser():
    client, db = await get_client_and_db()

    async with await client.start_session() as client_session:
        async with client_session.start_transaction():
            try:
                await db.users.update_one({"_id": ObjectId(request.form.get('user_id'))},
                                          {'$set': {"admin_controls": 0}}, session=client_session)

                flash('Revoked admin privileges successfully', 'success')
                return redirect(url_for('admin.adminIndex'))

            except Exception:
                flash('Error revoking privileges', 'error')
                return redirect(url_for('admin.adminIndex'))
