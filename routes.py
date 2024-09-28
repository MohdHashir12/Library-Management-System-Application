
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session 
from models import db, User, Category, Section, Request , Feedback
from app import app
from datetime import datetime , timedelta
from flask_apscheduler import APScheduler
from flask import send_file
import os
from werkzeug.utils import secure_filename







scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to login first.')
            return redirect(url_for('login'))
        return func(*args, **kwargs)

    return inner

@app.route('/')
@auth_required
def index():
    return render_template('index.html')

@app.route('/admin')
@auth_required
def admin():
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('You are not authorized to view this page.')
        return redirect(url_for('login'))
    else:
        sections = Section.query.all()
        requests = Request.query.all()  # Fetch all requests
        return render_template('admin.html', user=user, sections=sections, requests=requests)


@app.route('/login')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == '' or password == '':
            flash('Username or password cannot be empty.')
            return redirect(url_for('login'))  # Redirect to login page with flash message
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User does not exist.')
            return redirect(url_for('login'))  # Redirect to login page with flash message
        if not user.check_password(password):
            flash('Incorrect password.')
            return redirect(url_for('login'))  # Redirect to login page with flash message
        session['user_id'] = user.id
        if user.is_admin:
            return redirect(url_for('admin'))
        else:
            
            return redirect(url_for('dashboard'))  # Redirect to dashboard with flash message

    # If the request method is not POST, render the login page without flash message
    return render_template('login.html')

@app.route('/register')
def home2():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    if username == '' or password == '':
        flash('Username or password cannot be empty.')
        return redirect(url_for('register'))
    if User.query.filter_by(username=username).first():
        flash('User with this username already exists. Please choose some other username')
        return redirect(url_for('register'))
    user = User(username=username, password=password, name=name)
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered. ')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please Login')
        return redirect(url_for('login'))
    
    # Query sections from the database
    sections = Section.query.all()
    
    # Assign image URLs for each section
    for section in sections:
        request = Request.query.filter_by(section_id=section.id, granted=True).first()
        if request:
            section.image_url = request.image_path
        else:
            section.image_url = 'default_image.jpg'  # Provide a default image URL if no request found
        
    # Render the template with the sections
    return render_template('dashboard.html', user=User.query.get(session['user_id']), sections=sections)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/category/add')
@auth_required
def add_category():
    return render_template('add_category.html', user=User.query.get(session['user_id']))

@app.route('/category/add/edit')
@auth_required
def edit_category():
    return render_template('edit_category.html')

UPLOAD_FOLDER = 'static/images'
UPLOAD_PDF_FOLDER = 'static/pdfs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/category/add', methods=['POST'])
def add_category_post():
    # Extract form data
    title = request.form.get('section_title')
    author = request.form.get('author')
    section = request.form.get('section')
    description = request.form.get('description')
    date_created_str = request.form.get('date_created')
    image_file = request.files['image']
    pdf_file = request.files['pdf']

    # Validate form data and file uploads
    if (
        title == '' or author == '' or section == '' or description == '' or
        not image_file or image_file.filename == '' or not allowed_file(image_file.filename) or
        not pdf_file or pdf_file.filename == '' or not allowed_file(pdf_file.filename)
    ):
        flash('All fields are required. Please make sure to select valid image and PDF files.')
        return redirect(url_for('add_category'))

    try:
        date_created = datetime.strptime(date_created_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.')
        return redirect(url_for('add_category'))

    # Save image file
    image_filename = secure_filename(image_file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image_file.save(image_path)

    # Save PDF file
    pdf_filename = secure_filename(pdf_file.filename)
    pdf_path = os.path.join(app.config['UPLOAD_PDF_FOLDER'], pdf_filename)
    pdf_file.save(pdf_path)

    # Create new section object
    new_section = Section(
        title=title,
        author=author,
        section=section,
        description=description,
        date_created=date_created,
        image_path=image_path,
        pdf_path=pdf_path
    )

    # Add new section to the database
    db.session.add(new_section)
    db.session.commit()

    flash('Section added successfully.')
    return redirect(url_for('admin'))


@app.route('/section/edit/<int:id>', methods=['POST'])
def edit_section_post(id):
    section = Section.query.get_or_404(id)
    section.title = request.form.get('title')
    section.section = request.form.get('section')
    section.description = request.form.get('description')
    db.session.commit()
    flash('Section updated successfully.')
    return redirect(url_for('admin'))

@app.route('/section/edit/<int:id>')
def edit_section(id):
    section = Section.query.get_or_404(id)
    return render_template('edit_section.html', section=section)

@app.route('/delete_section/<int:id>', methods=['POST'])
def delete_section(id):
    section = Section.query.get_or_404(id)
    db.session.delete(section)
    db.session.commit()
    flash('Section deleted successfully.', 'success')
    return redirect(url_for('admin'))

@app.route('/librarian')
def librarian():
    # Query all requests
    requests = Request.query.all()
    return render_template('librarian.html', requests=requests)

@app.route('/grant_request/<int:request_id>', methods=['POST'])  # Make sure to include methods=['POST']
@auth_required
def grant_request(request_id):
    request_obj = Request.query.get(request_id)
    if request_obj:
        # Update the request status
        request_obj.granted = True
        # Set the path to the image file (replace 'path_to_image_file.jpg' with the actual path)
        request_obj.image_path = '/static/images/book1.jpeg'

        db.session.commit()
        flash('Request granted successfully.', 'success')
    else: 
        flash('Request not found.', 'error')

    return redirect(url_for('librarian'))  # Redirect to librarian route

@app.route('/reject_request/<int:request_id>', methods=['POST'])  # Make sure to include methods=['POST']
@auth_required
def reject_request(request_id):
    request_obj = Request.query.get(request_id)
    if request_obj:
        db.session.delete(request_obj)  # Delete the request object
        db.session.commit()
        flash('Request rejected and deleted successfully.', 'success')  # Flash message for success
    else:
        flash('Request not found.', 'error')

    return redirect(url_for('librarian'))  # Redirect to librarian route







def revoke_expired_requests():
    # Get the current date
    current_date = datetime.utcnow()
    # Define the duration after which requests should be automatically revoked (e.g., 7 days)
    duration = timedelta(days=7)
    # Calculate the threshold date
    threshold_date = current_date - duration
    # Query requests older than the threshold date and not revoked yet
    expired_requests = Request.query.filter(Request.requested_at <= threshold_date, Request.revoked == False).all()
    # Revoke expired requests
    for req in expired_requests:
        req.revoked = True
    db.session.commit()

@app.route('/revoke_request/<int:request_id>', methods=['POST'])
@auth_required
def revoke_request(request_id):
    request_obj = Request.query.get(request_id)
    if request_obj:
        # Delete the request from the database
        db.session.delete(request_obj)
        db.session.commit()

        # Remove access to the associated image file
        image_path = request_obj.image_path
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        flash('Request revoked successfully.', 'success')
    else:
        flash('Request not found.', 'error')

    return redirect(url_for('librarian'))
MAX_SECTIONS_PER_USER = 5

@app.route('/request_section/<int:section_id>', methods=['POST'])
def request_section(section_id):
    if 'user_id' not in session:
        flash('Please log in to request a section.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    # Check if the user has already requested 5 sections
    user_requests_count = Request.query.filter_by(user_id=user_id).count()
    if user_requests_count >= MAX_SECTIONS_PER_USER:
        flash('You have already requested the maximum allowed number of sections.')
        return redirect(url_for('user_dashboard'))

    section = Section.query.get(section_id)
    if not section:
        flash('Section not found.')
        return redirect(url_for('dashboard'))
    
    # Check if the book has already been granted
    existing_request = Request.query.filter_by(user_id=user_id, section_id=section_id, granted=True).first()
    if existing_request:
        flash('This book has already been issued to you.')
        return redirect(url_for('dashboard'))
    existing_request = Request.query.filter_by(user_id=user_id, section_id=section_id).first()
    if existing_request:
        flash('You have already requested this section.', 'error')
        return redirect(url_for('dashboard'))

    days_requested_str = request.form.get('days_requested')
    if not days_requested_str or not days_requested_str.isdigit():
        flash('Please enter a valid number of days for the request.')
        return redirect(url_for('dashboard'))

    days_requested = int(days_requested_str)
    if days_requested <= 0:
        flash('Please enter a valid number of days for the request.')
        return redirect(url_for('dashboard'))

    return_date = datetime.utcnow() + timedelta(days=days_requested)
    new_request = Request(
        user_id=user_id,
        section_id=section_id,
        return_date=return_date
    )
    db.session.add(new_request)
    db.session.commit()
    flash('Book requested successfully.')
    return redirect(url_for('user_dashboard'))


@app.route('/auto_revoke_expired_requests', methods=['POST'])
def auto_revoke_expired_requests():
    current_date = datetime.utcnow()
    expired_requests = Request.query.filter(Request.return_date <= current_date, Request.revoked == False).all()
    for request in expired_requests:
        request.revoked = True
    db.session.commit()
    flash('Expired requests automatically revoked.', 'success')  # Flash message for success
    return redirect(url_for('librarian'))  # Redirect to librarian route


@app.route('/user_dashboard')
def user_dashboard():
    # Get the current user's ID from the session
    user_id = session.get('user_id')
    if user_id:
        # Query requests associated with the current user
        user_requests = Request.query.filter_by(user_id=user_id).all()
        return render_template('user_dashboard.html', user_requests=user_requests)
    else:
        flash("Please login to view your dashboard.")
        return redirect(url_for('login'))



@app.route('/image/<path:filename>')
@auth_required  # Only authenticated users can access the image
def serve_image(filename):
    # You may want to implement additional security checks here
    # For example, check if the user is authorized to access this image

    # Serve the image file
    return send_file(filename, mimetype='image/jpeg')  # Adjust mimetype based on your image type

from datetime import datetime

from datetime import datetime

@app.route('/return_request/<int:request_id>', methods=['GET'])
def return_request(request_id):
    # Get the request object from the database within the current session
    request_obj = Request.query.get(request_id)

    # Check if the request exists and is granted
    if request_obj and request_obj.granted:
        # Get the associated section object
        request_section = request_obj.section

        # Check if the request is being returned before the issued date
        if datetime.utcnow() < request_obj.return_date:
            # Delete the request
            db.session.delete(request_obj)

            # Mark the section as available for request again
            request_section.available = True

            # Commit the changes to the database
            db.session.commit()

            flash('Request deleted successfully as it was returned before the issued date. Section is available for request again.', 'success')
        else:
            # Perform actions to handle the return of the request (e.g., update database)
            request_obj.returned = True

            # Commit the changes to the database
            db.session.commit()

            flash('Request returned successfully. Section is available for request again.', 'success')
    else:
        flash('Invalid request or request not granted.', 'error')

    return redirect(url_for('user_dashboard'))


@app.route('/section_details/<int:section_id>', methods=['GET', 'POST'])
def section_details(section_id):
    # Fetch section details from the database based on section_id
    section = Section.query.get(section_id)
    
    if request.method == 'POST':
        feedback_text = request.form.get('feedback')
        if feedback_text:
            # Create a new Feedback object and add it to the database
            feedback = Feedback(section_id=section_id, user_id=session.get('user_id'), text=feedback_text)
            db.session.add(feedback)
            db.session.commit()
            flash('Feedback submitted successfully.', 'success')
        else:
            flash('Please provide feedback before submitting.', 'error')
        return redirect(url_for('section_details', section_id=section_id))

    # Fetch user's name from the session or database
    user_name = session.get('user_name', 'Guest')  # Replace 'Guest' with default if not logged in
    
    # Fetch feedback for the current section
    feedbacks = Feedback.query.filter_by(section_id=section_id).all()
    
    # Pass section details, user's name, and feedbacks to the template
    return render_template('section_details.html', section=section, user_name=user_name, feedbacks=feedbacks)


@app.route('/<path:filename>')
def serve_pdf(filename):
    # Construct the correct file path
    pdf_path = os.path.join(app.config['UPLOAD_PDF_FOLDER'], filename)
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        return "PDF not found", 404
    
    # Serve the PDF file
    return send_file(pdf_path, mimetype='application/pdf')

@app.route('/search', methods=['GET'])
def search():
    search_option = request.args.get('search_option')
    query = request.args.get('q')
    search_results = []

    if search_option == 'section':
        search_results = Section.query.filter(Section.section.ilike(f'%{query}%')).all()
    elif search_option == 'book':
        search_results = Section.query.filter(Section.title.ilike(f'%{query}%')).all()
    elif search_option == 'author':
        search_results = Section.query.filter(Section.author.ilike(f'%{query}%')).all()

    return render_template('search_results.html', search_results=search_results)

@app.route('/delete_request/<int:request_id>', methods=['POST'])
@auth_required
def delete_request(request_id):
    request_obj = Request.query.get(request_id)
    if request_obj:
        # Delete the request from the database
        db.session.delete(request_obj)
        db.session.commit()
        flash('Request deleted successfully.', 'success')
    else:
        flash('Request not found.', 'error')

    return redirect(url_for('user_dashboard'))







if __name__ == '__main__':
   
    app.run(debug=True)