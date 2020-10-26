from flask import Flask, make_response,request,render_template
from flask_pymongo import PyMongo
from flask import abort, jsonify, redirect
from flask import url_for
from fooApp.forms import ProductForm
from bson.objectid import ObjectId
import bson
from flask_login import LoginManager, current_user
from flask_login import login_user, logout_user
from flask_login import login_required
from fooApp.forms import LoginForm
from fooApp.models import User


app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'foodb'
app.config['MONGO_URI'] = 'mongodb+srv://newuser1:1029384756@cluster0.8hivd.mongodb.net/foodb?retryWrites=true'
#app.config['MONGO_URI'] = 'mongodb://localhost:27017/foodb'
app.config['SECRET_KEY'] = '894257m4dewEEr' # Create your own.
app.config['SESSION_PROTECTION'] = 'strong'

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
  """Flask-Login hook to load a User instance from ID."""
  u = mongo.db.users.find_one({"username": user_id})
  if not u:
  	return None
  return User(u['username'])

@app.before_request
def callme_before_every_request():
  # Demo only: the before_request hook.
  app.logger.debug(dump_request_detail(request))

@app.after_request
def callme_after_every_response(response):
  # Demo only: the after_request hook.
  app.logger.debug('# After Request #\n' + repr(response))
  return response

@app.route('/login/', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('products_list'))
  form = LoginForm(request.form)
  error = None
  if request.method == 'POST' and form.validate():
    username = form.username.data.lower().strip()
    password = form.password.data.lower().strip()
    user = mongo.db.users.find_one({"username": form.username.data})
    if user and User.validate_login(user['password'], form.password.data):  
      user_obj = User(user['username'])
      login_user(user_obj)
      return redirect(url_for('products_list'))
    else:
      error = 'Incorrect username or password.'
  return render_template('user/login.html',
      form=form, error=error)

@app.route('/logout/')
def logout():
  logout_user()
  return redirect(url_for('products_list'))

mongo = PyMongo(app)

@app.errorhandler(404)
def error_not_found(error):
  return render_template('error/not_found.html'), 404

@app.errorhandler(bson.errors.InvalidId)
def error_not_found(error):
  return render_template('error/not_found.html'), 404  

@app.route('/products/')
def products_list():
  """Provide HTML listing of all Products."""
  # Query: Get all Products objects, sorted by date.
  products = mongo.db.products.find()[:]
  return render_template('product/index.html',
    products=products)

@app.route('/products/create/', methods=['GET', 'POST'])
@login_required
def product_create():
  """Provide HTML form to create a new product."""
  form = ProductForm(request.form)
  if request.method == 'POST' and form.validate():
    mongo.db.products.insert_one(form.data)
    # Success. Send user back to full product list.
    return redirect(url_for('products_list'))
  # Either first load or validation error at this point.
  return render_template('product/edit.html', form=form)

@app.route('/products/<product_id>/')
def product_detail(product_id):
  """Provide HTML page with a given product."""
  # Query: get Product object by ID.
  product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })
  print(product)
  if product is None:
    # Abort with Not Found.
    abort(404)
  return render_template('product/detail.html',
    product=product)

@app.route( 
  '/products/<product_id>/edit/',
  methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
  product = mongo.db.products.find_one({ "_id": ObjectId(product_id) })
  if product is None:
    # Abort with Not Found.
    abort(404)
  form = ProductForm(request.form)
  if request.method == 'POST' and form.validate():
    mongo.db.products.update({"_id": ObjectId(product_id)},form.data)
    # Success. Send user back to full product list.
    return redirect(url_for('products_list'))
  # Either first load or validation error at this point.
  return render_template('product/editprod.html', form=form,product=product)


@app.route('/products/<product_id>/delete/', methods=['DELETE'])
@login_required
def product_delete(product_id):
  """Delete record using HTTP DELETE, respond with JSON."""
  result = mongo.db.products.delete_one({ "_id": ObjectId(product_id) })
  if result.deleted_count == 0:
    # Abort with Not Found, but with simple JSON response.
    response = jsonify({'status': 'Not Found'})
    response.status = 404
    return response
  return jsonify({'status': 'OK'})

@app.route('/')
def index():
  return redirect(url_for('products_list'))

def dump_request_detail(request):
  request_detail = """
## Request INFO ##
request.endpoint: {request.endpoint}
request.method: {request.method}
request.view_args: {request.view_args}
request.args: {request.args}
request.form: {request.form}
request.user_agent: {request.user_agent}
request.files: {request.files}

## request.headers ##
{request.headers}
  """.format(request=request).strip()
  return request_detail

if __name__ == '__main__':
    app.run(debug=True)