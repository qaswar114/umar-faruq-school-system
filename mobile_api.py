from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


mobile_api = Blueprint("mobile_api", __name__)


def create_mobile_token(app, user):
    serializer = URLSafeTimedSerializer(app.secret_key)

    return serializer.dumps({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "school_id": user.school_id
    })


def verify_mobile_token(app, token, max_age=60 * 60 * 24 * 30):
    serializer = URLSafeTimedSerializer(app.secret_key)

    try:
        return serializer.loads(token, max_age=max_age)

    except SignatureExpired:
        return None

    except BadSignature:
        return None


@mobile_api.route("/api/mobile/login", methods=["POST"])
def api_mobile_login():
    from app import app, User, School

    data = request.get_json() or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({
            "success": False,
            "message": "Wrong username or password."
        }), 401

    school = School.query.get(user.school_id) if user.school_id else None

    if not school:
        return jsonify({
            "success": False,
            "message": "School account not found."
        }), 403

    if not school.is_active or school.subscription_status != "active":
        return jsonify({
            "success": False,
            "message": "This school account is not active."
        }), 403

    if not user.is_active:
        return jsonify({
            "success": False,
            "message": "This user account is disabled."
        }), 403

    if not check_password_hash(user.password_hash, password):
        return jsonify({
            "success": False,
            "message": "Wrong username or password."
        }), 401

    token = create_mobile_token(app, user)

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "assigned_grade": user.assigned_grade,
            "school_id": user.school_id,
            "school_name": school.school_name
        }
    })
