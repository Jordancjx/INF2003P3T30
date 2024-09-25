from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import config.constants
from config.dbConnect import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'public/profile_pics'  # Ensure this folder exists
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

user_bp = Blueprint('user', __name__, template_folder=config.constants.template_dir,
                     static_folder=config.constants.static_dir, static_url_path='/public', url_prefix='/user')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Register
@user_bp.route('/register')
def register():
    return render_template('/user/register.html')

#Login
@user_bp.route('/login')
def login():
    return render_template('/user/login.html')

    
#Logout
@user_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin', None)
    return redirect(url_for('index.index'))

#Profile
@user_bp.route('/profile')
def getProfile():
    # Check if user is logged in
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "error")
        return redirect(url_for('user.login'))
    
    user = User.query.get_or_404(session['user_id']) 
    
    return render_template('/user/profile.html', user = user)


#Register API; Does not render any page
@user_bp.route('/api/register', methods = ["POST"])
def register_process():
    hashed_password = generate_password_hash(request.form.get('password'),method='pbkdf2:sha256', salt_length=16)

    existing_user = User.query.filter((User.username == request.form.get('username')) | (User.email == request.form.get('email'))).first()
    
    if existing_user:
        flash("Username or Email already exists", "error")
        return redirect(url_for('user.register'))
    
    new_user = User(
        username = request.form.get('username'),
        fname = request.form.get('fname'),
        lname = request.form.get('lname'),
        email = request.form.get('email'),
        password = hashed_password,
        # profile_pic_url = data.get('profile_pic_url', None),
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully!')
        return redirect(url_for('user.login'))
    except Exception as e:
        db.session_rollback()
        flash("An error has occurred", "error")
        return redirect(url_for('user.register'))
    

#Login API; Does not render any page
@user_bp.route('/api/login', methods = ["POST"])
def login_process():
    identifier = request.form.get('username')  # This could be either email or username
    password = request.form.get('password')
    
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
    if user and check_password_hash(user.password, password):
        if user.admin_controls == True:
            session['admin'] = True
        session['user_id'] = user.id
        return redirect(url_for('index.index'))
    else:
        flash("Invalid Username/email or Password", "error")
        return redirect(url_for('user.login'))

@user_bp.route('/api/update_profile', methods = ["POST"])
def update_profile():
    if 'user_id' not in session:
        flash("Please log in to update your profile.", "error")
        return redirect(url_for('user.login'))
    
    user = User.query.get_or_404(session['user_id'])
    user.fname = request.form.get('fname')
    user.lname = request.form.get('lname')
    user.email = request.form.get('email')
    
    # Update password if provided
    password = request.form.get('password')
    if password:
        user.password = generate_password_hash(password)
    
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        
        if file.filename != '':
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                user.profile_pic_url = f"/{file_path}"
                
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('user.getProfile'))