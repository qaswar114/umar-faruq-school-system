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

@mobile_api.route("/api/mobile/teacher_dashboard", methods=["GET"])
def api_mobile_teacher_dashboard():
    from app import app, User, School, Pupil, Attendance, Exam, Announcement, current_school_id
    from datetime import date

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({
            "success": False,
            "message": "Missing mobile token."
        }), 401

    token = auth_header.replace("Bearer ", "").strip()
    token_data = verify_mobile_token(app, token)

    if not token_data:
        return jsonify({
            "success": False,
            "message": "Invalid or expired token."
        }), 401

    if token_data.get("role", "").lower() != "teacher":
        return jsonify({
            "success": False,
            "message": "Teacher access only."
        }), 403

    school_id = token_data.get("school_id")
    user_id = token_data.get("user_id")

    school = School.query.get(school_id)

    if not school or not school.is_active:
        return jsonify({
            "success": False,
            "message": "School account is not active."
        }), 403

    teacher = User.query.filter_by(
        id=user_id,
        school_id=school_id,
        is_active=True
    ).first()

    if not teacher:
        return jsonify({
            "success": False,
            "message": "Teacher account not found."
        }), 404

    assigned_grade = teacher.assigned_grade or ""

    pupils_count = 0
    present = 0
    absent = 0
    late = 0

    today = date.today()

    if assigned_grade:
        pupils_count = Pupil.query.filter_by(
            school_id=school_id,
            grade=assigned_grade,
            status="Active"
        ).count()

        today_attendance = Attendance.query.join(Pupil).filter(
            Attendance.school_id == school_id,
            Attendance.attendance_date == today,
            Pupil.school_id == school_id,
            Pupil.grade == assigned_grade
        ).all()

        present = sum(1 for r in today_attendance if r.status == "Present")
        absent = sum(1 for r in today_attendance if r.status == "Absent")
        late = sum(1 for r in today_attendance if r.status == "Late")

    active_exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).count()

    announcements = Announcement.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(
        Announcement.created_at.desc()
    ).limit(5).all()

    announcement_list = []

    for a in announcements:
        announcement_list.append({
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "audience": a.audience,
            "created_at": str(a.created_at)
        })

    return jsonify({
        "success": True,
        "message": "Teacher dashboard loaded.",
        "data": {
            "school": {
                "id": school.id,
                "name": school.school_name
            },
            "teacher": {
                "id": teacher.id,
                "username": teacher.username,
                "assigned_grade": assigned_grade
            },
            "summary": {
                "pupils_count": pupils_count,
                "present_today": present,
                "absent_today": absent,
                "late_today": late,
                "active_exams": active_exams
            },
            "announcements": announcement_list
        }
    })
