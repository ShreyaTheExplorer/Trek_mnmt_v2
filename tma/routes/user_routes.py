from flask import Blueprint
from auth import api_response, login_required

user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/ping', methods=['GET'])
def ping_user():
    return api_response(True, "User API online.", None, 200)

