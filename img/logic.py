# from flask import Flask, render_template, request, redirect, url_for
# from pymongo import MongoClient

# # Create a Flask application
# App = Flask(__name__, static_url_path='/static')

# # MongoDB setup (replace with your MongoDB connection details)
# client = MongoClient('mongodb://127.0.0.1:27017/')
# db = client['SIH2023']
# users_collection = db['users']

# @app.route('/')
# def homepage():
#     # Render the homepage HTML template
#     return render_template('main.html')

# @app.route('/login', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         # Get user data from the form
#         name = request.form['name']
#         email = request.form['email']
#         dob = request.form['dob']
#         pib_id = request.form['pib_id']
#         password = request.form['password']  # You should hash this in production

#         # Create a user document and insert it into MongoDB
#         user_data = {
#             'name': name,
#             'email': email,
#             'date_of_birth': dob,
#             'pib_id': pib_id,
#             'password': password
#         }
#         users_collection.insert_one(user_data)

#         # Redirect to the homepage after successful registration
#         return redirect(url_for('homepage'))

#     # Render the registration form HTML template
#     return render_template('dashboardContent.html')

# if __name__ == '__main__':
#     app.run(debug=True)
