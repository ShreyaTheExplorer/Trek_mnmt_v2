from flask import Blueprint
from auth import api_response, login_required, role_required

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')

@staff_bp.route('/ping', methods=['GET'])
@login_required
@role_required('staff', 'admin')
def ping_staff():
    return api_response(True, "Staff API online.", None, 200)

