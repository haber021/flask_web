from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Test

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def hom():
    return render_template('hom.html', user=current_user)

@login_required
def hom():
    test_data = Test.query.all()  # Fetch all data from the Test model
    return render_template('hom.html', user=current_user, test_data=test_data)




