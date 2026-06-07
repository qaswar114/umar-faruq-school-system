from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import date, datetime
from xhtml2pdf import pisa
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

app.config["UPLOAD_FOLDER"] = "static/uploads"

database_url = os.environ.get("DATABASE_URL", "sqlite:///school.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

SCHOOL_NAME = "UMAR FARUQ INTEGRATED ACADEMY"
GRADES = ["PP1","PP2","Grade 1","Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7","Grade 8","Grade 9"]
TERMS = ["Term 1","Term 2","Term 3"]
TERM_MONTHS = {
    "Term 1": ["January","February","March"],
    "Term 2": ["May","June","July"],
    "Term 3": ["September","October","November"]
}

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    school_name = db.Column(db.String(200), nullable=False)
    motto = db.Column(db.String(200), default="")

    phone = db.Column(db.String(100), default="")
    email = db.Column(db.String(120), default="")
    address = db.Column(db.Text, default="")

    logo = db.Column(db.String(200), default="logo.png")
    stamp = db.Column(db.String(200), default="")
    headteacher_signature = db.Column(db.String(200), default="")

    primary_color = db.Column(db.String(20), default="#0b5ed7")
    secondary_color = db.Column(db.String(20), default="#ffffff")

    subscription_status = db.Column(db.String(20), default="active")
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    assigned_grade = db.Column(db.String(50), default="")
    assigned_subjects = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True)
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(80), default="")
    email = db.Column(db.String(120), default="")
    id_no = db.Column(db.String(80), default="")
    role = db.Column(db.String(50), nullable=False)
    assigned_subjects = db.Column(db.String(255), default="")
    assigned_grade = db.Column(db.String(50), default="")
    date_joined = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default="Active")
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    username = db.Column(db.String(80), default="")
    role = db.Column(db.String(50), default="")
    action = db.Column(db.String(255), nullable=False)
    module = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(50), default="All")  # All / Parents / Teachers / Students
    created_by = db.Column(db.String(80), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default="Active")

class SMSMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    recipient_name = db.Column(db.String(200), default="")
    phone = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    status = db.Column(db.String(30), default="Pending")
    created_by = db.Column(db.String(80), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), default=SCHOOL_NAME)
    phone = db.Column(db.String(100), default="")
    address = db.Column(db.Text, default="Thank you for choosing us.")

class Pupil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    admission_no = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), default="")
    grade = db.Column(db.String(50), nullable=False)
    guardian_name = db.Column(db.String(200), nullable=False)
    guardian_phone = db.Column(db.String(80), nullable=False)
    home_address = db.Column(db.Text, default="")
    new_admission = db.Column(db.String(10), default="Yes")
    uses_bus = db.Column(db.String(10), default="No")
    photo = db.Column(db.String(255), default="")
    status = db.Column(db.String(30), default="Active")
    created_at = db.Column(db.Date, default=date.today)
class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    academic_year = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    term = db.Column(db.String(30), nullable=False)
    month = db.Column(db.String(30), nullable=True)
    tuition_fee = db.Column(db.Float, default=0)
    bus_fee = db.Column(db.Float, default=0)
    exam_fee = db.Column(db.Float, default=0)
    admission_fee = db.Column(db.Float, default=0)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    receipt_no = db.Column(db.String(120), unique=True, nullable=False)
    pupil_id = db.Column(db.Integer, db.ForeignKey("pupil.id"), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    term = db.Column(db.String(30), nullable=False)
    month = db.Column(db.String(30), nullable=False)
    tuition_paid = db.Column(db.Float, default=0)
    bus_paid = db.Column(db.Float, default=0)
    exam_paid = db.Column(db.Float, default=0)
    admission_paid = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    collected_by = db.Column(db.String(80), nullable=False)
    pupil = db.relationship("Pupil")
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    expense_date = db.Column(db.Date, default=date.today)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, nullable=False)
    recorded_by = db.Column(db.String(80))
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    pupil_id = db.Column(db.Integer, db.ForeignKey("pupil.id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)   # Present / Absent / Late
    pupil = db.relationship("Pupil")
class Discount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    pupil_id = db.Column(db.Integer, db.ForeignKey("pupil.id"), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    term = db.Column(db.String(30), default="All Year")
    amount = db.Column(db.Float, default=0)
    reason = db.Column(db.String(255), default="")
    created_at = db.Column(db.Date, default=date.today)
    created_by = db.Column(db.String(80), default="")
    pupil = db.relationship("Pupil")
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    subject_name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    teacher_name = db.Column(db.String(100), default="")
    status = db.Column(db.String(20), default="Active")
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    exam_name = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    term = db.Column(db.String(30), nullable=False)
    grade = db.Column(db.String(50), nullable=False)
    total_marks = db.Column(db.Float, default=100)
    status = db.Column(db.String(20), default="Active")
class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), default=1)
    pupil_id = db.Column(db.Integer, db.ForeignKey("pupil.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subject.id"), nullable=False)
    marks_obtained = db.Column(db.Float, default=0)
    teacher_remark = db.Column(db.String(255), default="")

    pupil = db.relationship("Pupil")
    exam = db.relationship("Exam")
    subject = db.relationship("Subject")

def money(n):
    return "KES {:,.2f}".format(float(n or 0))

def generate_pdf(html):
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return pdf

def current_year():
    return datetime.now().year

def current_year():
    return datetime.now().year

def term_months(term):
    return TERM_MONTHS.get(term, [])

def get_settings():
    school = current_school()

    if school:
        return school

    s = Setting.query.first()
    if not s:
        s = Setting(school_name=SCHOOL_NAME)
        db.session.add(s)
        db.session.commit()

    return s

def init_database():
    db.create_all()

    if not School.query.first():
        db.session.add(School(
            school_name="Umar Faruq Integrated Academy",
            motto="",
            phone="",
            email="",
            address="Mandera",
            logo="logo.png",
            primary_color="#0b5ed7",
            secondary_color="#ffffff",
            subscription_status="active",
            is_active=True
        ))
        db.session.commit()

    try:
        Subject.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        Exam.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        Mark.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        Staff.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        AuditLog.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        Announcement.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        SMSMessage.__table__.create(db.engine, checkfirst=True)
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE "user" ADD COLUMN school_id INTEGER DEFAULT 1')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text("ALTER TABLE staff ADD COLUMN assigned_subjects VARCHAR(255) DEFAULT ''")
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE pupil ADD COLUMN school_id INTEGER DEFAULT 1')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE payment ADD COLUMN school_id INTEGER DEFAULT 1')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    school_specific_tables = [
        "staff",
        "audit_log",
        "announcement",
        "sms_message",
        "fee_structure",
        "expense",
        "attendance",
        "discount",
        "subject",
        "exam",
        "mark"
    ]

    for table in school_specific_tables:
        try:
            db.session.execute(
                db.text(f"ALTER TABLE {table} ADD COLUMN school_id INTEGER DEFAULT 1")
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE "user" ADD COLUMN assigned_grade VARCHAR(50) DEFAULT \'\'')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE "user" ADD COLUMN assigned_subjects VARCHAR(255) DEFAULT \'\'')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE "user" ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        db.session.execute(
            db.text('ALTER TABLE pupil ADD COLUMN photo VARCHAR(255) DEFAULT \'\'')
        )
        db.session.commit()
    except Exception:
        db.session.rollback()

    if not Setting.query.first():
        db.session.add(Setting(
            school_name=SCHOOL_NAME,
            address="Umar Faruq Integrated Academy"
        ))

    default_users = [
        ("superadmin", "super123", "Super Admin"),
        ("admin", "admin123", "Admin"),
        ("registrar", "reg123", "Registrar"),
        ("bursar", "bursar123", "Bursar"),
        ("reception", "recep123", "Receptionist"),
    ]

    for username, password, role in default_users:
        user = User.query.filter_by(username=username).first()

        if not user:
            db.session.add(User(
                school_id=1,
                username=username,
                password_hash=generate_password_hash(password),
                role=role
            ))
        else:
            user.school_id = user.school_id or 1

        bustani = School.query.filter(
        School.school_name.ilike("%Bustani%")
    ).first()

    if bustani:
        bustani.logo = "bustani_logo.png"

    umar = School.query.filter(
        School.school_name.ilike("%Umar%")
    ).first()

    if umar:
        umar.logo = "logo.png"

    db.session.commit()
def login_required():
    if "username" not in session:
        return False
    return True

def role_allowed(*roles):
    current_role = session.get("role", "").lower()
    allowed_roles = [r.lower() for r in roles]

    # Super Admin can access everything
    if current_role == "super admin":
        return True

    # Admin can access everything except Super Admin-only areas
    if current_role == "admin":
        return True

    return current_role in allowed_roles
def super_admin_required():
    return session.get("role", "").lower() == "super admin"

def current_school_id():
    return session.get("school_id", 1)

def current_school():
    return School.query.get(current_school_id())
    
def save_audit(action, module="System"):
    log = AuditLog(
        school_id=current_school_id(),
        username=session.get("username", ""),
        role=session.get("role", ""),
        action=action,
        module=module
    )
    db.session.add(log)
    db.session.commit()
def next_admission_no():
    school_id = current_school_id()
    count = Pupil.query.filter_by(school_id=school_id).count() + 1

    school = current_school()
    prefix = "SCH"

    if school and school.school_name:
        words = school.school_name.split()
        prefix = "".join([w[0] for w in words[:3]]).upper()

    return f"{prefix}/{current_year()}/{count:04d}"

def receipt_no(year, term):
    school_id = current_school_id()
    term_code = term.replace("Term ", "T")
    count = Payment.query.filter_by(
        school_id=school_id,
        academic_year=year,
        term=term
    ).count() + 1
    return f"UFIA/{year}/{term_code}/{count:05d}"

def get_fee(year, grade, term, month):
    school_id = current_school_id()

    fee = FeeStructure.query.filter_by(
        school_id=school_id,
        academic_year=year,
        grade=grade,
        term=term,
        month=month
    ).first()

    if not fee:
        fee = FeeStructure(
            school_id=school_id,
            academic_year=year,
            grade=grade,
            term=term,
            month=month
        )
        db.session.add(fee)
        db.session.commit()

    return fee
    
def monthly_due(pupil, year, term, month):
    fee = get_fee(year, pupil.grade, term, month)
    return {
        "tuition": fee.tuition_fee,
        "bus": fee.bus_fee if pupil.uses_bus == "Yes" else 0,
        "exam": fee.exam_fee,
        "admission": fee.admission_fee if pupil.new_admission == "Yes" else 0,
    }

def term_due(pupil, year, term):
    total = {"tuition":0,"bus":0,"exam":0,"admission":0}
    months = term_months(term)

    if not months:
        return total

    for m in months:
        d = monthly_due(pupil, year, term, m)
        total["tuition"] += d["tuition"]
        total["bus"] += d["bus"]

    first = months[0]
    d = monthly_due(pupil, year, term, first)
    total["exam"] = d["exam"]
    total["admission"] = d["admission"] if pupil.new_admission == "Yes" else 0

    return total

def year_due(pupil, year):
    total = {"tuition":0,"bus":0,"exam":0,"admission":0}
    for t in TERMS:
        d = term_due(pupil, year, t)
        for k in total:
            total[k] += d[k]
    return sum(total.values())

def paid_year(pupil_id, year):
    rows = Payment.query.filter_by(
        school_id=current_school_id(),
        pupil_id=pupil_id,
        academic_year=year
    ).all()

    return sum((p.tuition_paid + p.bus_paid + p.exam_paid + p.admission_paid) for p in rows)

def paid_month(pupil_id, year, term, month):
    rows = Payment.query.filter_by(
        school_id=current_school_id(),
        pupil_id=pupil_id,
        academic_year=year,
        term=term,
        month=month
    ).all()

    return sum((p.tuition_paid + p.bus_paid + p.exam_paid + p.admission_paid) for p in rows)

def discount_year(pupil_id, year):
    return sum(
        d.amount for d in Discount.query.filter_by(
            school_id=current_school_id(),
            pupil_id=pupil_id,
            academic_year=year
        ).all()
    )

def opening_arrears(pupil, year):
    if year <= 2026:
        return 0

    previous_year_due = year_due(pupil, year - 1)
    previous_year_paid = paid_year(pupil.id, year - 1)
    previous_year_discount = discount_year(pupil.id, year - 1)

    arrears = previous_year_due - previous_year_paid - previous_year_discount

    return max(0, arrears)
def due_until_month(pupil, year, selected_term, selected_month):
    if year < 2026:
        return 0

    total = 0
    started = False

    for term in TERMS:
        for month in term_months(term):
            if year == 2026 and month == "May":
                started = True

            if started:
                d = monthly_due(pupil, year, term, month)
                total += sum(d.values())

            if term == selected_term and month == selected_month:
                return total

    return total

@app.before_request
def setup_once():
    if not hasattr(app, "_database_initialized"):
        init_database()
        app._database_initialized = True

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()

        school = School.query.get(user.school_id) if user else None

        if user and (not school or not school.is_active or school.subscription_status != "active"):
            flash("This school account is not active. Contact system owner.")
            return redirect(url_for("login"))

        if user and not user.is_active:
            flash("This account has been disabled. Contact Admin.")
            return redirect(url_for("login"))

        if user and check_password_hash(user.password_hash, request.form["password"].strip()):
            session["username"] = user.username
            session["role"] = user.role
            session["assigned_grade"] = user.assigned_grade
            session["school_id"] = user.school_id
            session["school_name"] = school.school_name if school else ""
            return redirect(url_for("dashboard"))

        flash("Wrong username or password.")

    return render_template("login.html", settings=get_settings())

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() == "super admin":
        total_schools = School.query.count()
        active_schools = School.query.filter_by(is_active=True).count()
        trial_schools = School.query.filter_by(subscription_status="trial").count()
        expired_schools = School.query.filter_by(subscription_status="expired").count()

        total_pupils = Pupil.query.count()
        total_staff = Staff.query.count()
        total_sms = SMSMessage.query.count()

        total_collected = sum(
            p.tuition_paid + p.bus_paid + p.exam_paid + p.admission_paid
            for p in Payment.query.all()
        )

        recent_schools = School.query.order_by(
            School.created_at.desc()
        ).limit(5).all()

        return render_template(
            "super_dashboard.html",
            settings=get_settings(),
            total_schools=total_schools,
            active_schools=active_schools,
            trial_schools=trial_schools,
            expired_schools=expired_schools,
            total_pupils=total_pupils,
            total_staff=total_staff,
            total_sms=total_sms,
            total_collected=money(total_collected),
            recent_schools=recent_schools
        )

    if session.get("role", "").lower() == "teacher":
        school_id = current_school_id()
        assigned_grade = session.get("assigned_grade", "")

        today = date.today()

        pupils_count = Pupil.query.filter_by(
            school_id=school_id,
            grade=assigned_grade,
            status="Active"
        ).count()

        today_attendance = Attendance.query.join(Pupil).filter(
            Attendance.school_id == school_id,
            Pupil.school_id == school_id,
            Pupil.grade == assigned_grade,
            Attendance.attendance_date == today
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
        ).order_by(Announcement.created_at.desc()).limit(5).all()

        return render_template(
            "teacher_dashboard.html",
            settings=get_settings(),
            assigned_grade=assigned_grade,
            pupils_count=pupils_count,
            present=present,
            absent=absent,
            late=late,
            active_exams=active_exams,
            announcements=announcements
        )

    school_id = current_school_id()
    current_month = date.today().month
    current_year_num = date.today().year

    payments_query = Payment.query.filter_by(school_id=school_id)
    pupils_query = Pupil.query.filter_by(school_id=school_id)

    total_collected = sum(
        p.tuition_paid + p.bus_paid + p.exam_paid + p.admission_paid
        for p in payments_query.all()
    )

    today_collection = sum(
        p.tuition_paid + p.bus_paid + p.exam_paid + p.admission_paid
        for p in Payment.query.filter_by(
            school_id=school_id,
            payment_date=date.today()
        ).all()
    )

    month_collection = 0
    for p in payments_query.all():
        if p.payment_date.month == current_month and p.payment_date.year == current_year_num:
            month_collection += (
                p.tuition_paid +
                p.bus_paid +
                p.exam_paid +
                p.admission_paid
            )

    defaulters = 0
    outstanding = 0

    for pupil in Pupil.query.filter_by(
        school_id=school_id,
        status="Active"
    ).all():
        bal = (
            year_due(pupil, current_year_num)
            - paid_year(pupil.id, current_year_num)
            - discount_year(pupil.id, current_year_num)
        )

        if bal > 0:
            defaulters += 1
            outstanding += bal

    return render_template(
        "dashboard.html",
        settings=get_settings(),
        total_pupils=pupils_query.count(),
        bus_pupils=Pupil.query.filter_by(
            school_id=school_id,
            uses_bus="Yes"
        ).count(),
        total_collected=money(total_collected),
        receipts=payments_query.count(),
        today_collection=money(today_collection),
        month_collection=money(month_collection),
        defaulters=defaulters,
        outstanding=money(outstanding)
    )
@app.route("/schools")
def schools():

    if not login_required():
        return redirect(url_for("login"))

    if not super_admin_required():
        flash("Only Super Admin can manage schools.")
        return redirect(url_for("dashboard"))

    schools = School.query.order_by(School.school_name).all()

    return render_template(
        "schools.html",
        settings=get_settings(),
        schools=schools
    )

@app.route("/create_school", methods=["GET", "POST"])
def create_school():
    if not login_required():
        return redirect(url_for("login"))

    if not super_admin_required():
        flash("Only Super Admin can create schools.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        logo_filename = ""
        stamp_filename = ""
        signature_filename = ""

        logo_file = request.files.get("logo")
        stamp_file = request.files.get("stamp")
        signature_file = request.files.get("headteacher_signature")

        if logo_file and logo_file.filename:
            logo_filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], logo_filename))

        if stamp_file and stamp_file.filename:
            stamp_filename = secure_filename(stamp_file.filename)
            stamp_file.save(os.path.join(app.config["UPLOAD_FOLDER"], stamp_filename))

        if signature_file and signature_file.filename:
            signature_filename = secure_filename(signature_file.filename)
            signature_file.save(os.path.join(app.config["UPLOAD_FOLDER"], signature_filename))

        school = School(
            school_name=request.form["school_name"],
            motto=request.form.get("motto", ""),
            phone=request.form.get("phone", ""),
            email=request.form.get("email", ""),
            address=request.form.get("address", ""),
            logo="uploads/" + logo_filename if logo_filename else "logo.png",
            stamp="uploads/" + stamp_filename if stamp_filename else "",
            headteacher_signature="uploads/" + signature_filename if signature_filename else "",
            primary_color=request.form.get("primary_color", "#0b5ed7"),
            secondary_color=request.form.get("secondary_color", "#ffffff"),
            subscription_status=request.form.get("subscription_status", "trial"),
            is_active=True
        )

        db.session.add(school)
        db.session.commit()

        admin_username = request.form["admin_username"].strip()
        admin_password = request.form["admin_password"].strip()

        existing_user = User.query.filter_by(username=admin_username).first()
        if existing_user:
            flash("That admin username already exists. Choose another username.")
            return redirect(url_for("create_school"))

        school_admin = User(
            school_id=school.id,
            username=admin_username,
            password_hash=generate_password_hash(admin_password),
            role="Admin",
            is_active=True
        )

        db.session.add(school_admin)
        db.session.commit()

        session["school_id"] = school.id
        session["school_name"] = school.school_name

        save_audit(
            f"Created new school: {school.school_name}",
            "Schools"
        )

        flash("School created successfully. You are now managing the new school.")
        return redirect(url_for("dashboard"))

    return render_template("create_school.html", settings=get_settings())
@app.route("/switch_school/<int:school_id>")
def switch_school(school_id):
    if not login_required():
        return redirect(url_for("login"))

    if not super_admin_required():
        flash("Only Super Admin can switch schools.")
        return redirect(url_for("dashboard"))

    school = School.query.get_or_404(school_id)

    session["school_id"] = school.id
    session["school_name"] = school.school_name

    flash(f"Now managing {school.school_name}")
    return redirect(url_for("dashboard"))


@app.route("/edit_school/<int:school_id>", methods=["GET", "POST"])
def edit_school(school_id):
    if not login_required():
        return redirect(url_for("login"))

    if not super_admin_required():
        flash("Only Super Admin can edit schools.")
        return redirect(url_for("dashboard"))

    school = School.query.get_or_404(school_id)

    if request.method == "POST":
        school.school_name = request.form["school_name"]
        school.motto = request.form.get("motto", "")
        school.phone = request.form.get("phone", "")
        school.email = request.form.get("email", "")
        school.address = request.form.get("address", "")
        school.primary_color = request.form.get("primary_color", "#0b5ed7")
        school.secondary_color = request.form.get("secondary_color", "#ffffff")
        school.subscription_status = request.form.get("subscription_status", "active")
        school.is_active = True if request.form.get("is_active") == "active" else False

        logo_file = request.files.get("logo")
        stamp_file = request.files.get("stamp")
        signature_file = request.files.get("headteacher_signature")

        if logo_file and logo_file.filename:
            logo_filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], logo_filename))
            school.logo = "uploads/" + logo_filename

        if stamp_file and stamp_file.filename:
            stamp_filename = secure_filename(stamp_file.filename)
            stamp_file.save(os.path.join(app.config["UPLOAD_FOLDER"], stamp_filename))
            school.stamp = "uploads/" + stamp_filename

        if signature_file and signature_file.filename:
            signature_filename = secure_filename(signature_file.filename)
            signature_file.save(os.path.join(app.config["UPLOAD_FOLDER"], signature_filename))
            school.headteacher_signature = "uploads/" + signature_filename

        db.session.commit()

        if session.get("school_id") == school.id:
            session["school_name"] = school.school_name

        flash("School updated successfully.")
        return redirect(url_for("schools"))

    return render_template(
        "edit_school.html",
        settings=get_settings(),
        school=school
    )
    
@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        expense_date = request.form.get("expense_date")
        category = request.form.get("category")
        description = request.form.get("description")
        amount = float(request.form.get("amount") or 0)

        exp = Expense(
            school_id=school_id,
            expense_date=datetime.strptime(expense_date, "%Y-%m-%d").date() if expense_date else date.today(),
            category=category,
            description=description,
            amount=amount,
            recorded_by=session.get("username")
        )

        db.session.add(exp)
        db.session.commit()

        save_audit(
            f"Recorded expense: {category} - KES {amount:,.2f}",
            "Finance"
        )

        flash("Expense recorded successfully.")
        return redirect(url_for("expenses"))

    rows = Expense.query.filter_by(
        school_id=school_id
    ).order_by(Expense.expense_date.desc()).all()

    return render_template(
        "expenses.html",
        settings=get_settings(),
        rows=rows,
        today=date.today(),
        money=money
    )
    
@app.route("/expense_report")
def expense_report():
    if not login_required():
        return redirect(url_for("login"))

    school_id = current_school_id()

    rows = Expense.query.filter_by(
        school_id=school_id
    ).order_by(
        Expense.expense_date.desc()
    ).all()

    total = sum(r.amount for r in rows)

    return render_template(
        "expense_report.html",
        settings=get_settings(),
        rows=rows,
        total=total,
        money=money
    )
    
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin"):
        flash("Only Admin can edit branding.")
        return redirect(url_for("dashboard"))

    school = current_school()

    if request.method == "POST":
        school.school_name = request.form["school_name"]
        school.phone = request.form.get("phone", "")
        school.address = request.form.get("address", "")

        db.session.commit()

        session["school_name"] = school.school_name

        flash("Branding saved.")
        return redirect(url_for("settings"))

    return render_template("settings.html", settings=school)
    
@app.route("/pupils", methods=["GET","POST"])
def pupils():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("registrar", "receptionist"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        photo_file = request.files.get("photo")
        photo_filename = ""

        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_filename))
        p = Pupil(
            school_id=current_school_id(),
            admission_no=next_admission_no(),
            full_name=request.form["full_name"],
            gender=request.form["gender"],
            dob=request.form.get("dob", ""),
            grade=request.form["grade"],
            guardian_name=request.form["guardian_name"],
            guardian_phone=request.form["guardian_phone"],
            home_address=request.form.get("home_address", ""),
            new_admission=request.form["new_admission"],
            uses_bus=request.form["uses_bus"],
            photo=photo_filename
            
        )
        db.session.add(p)
        db.session.commit()
        
        save_audit(
            f"Registered new pupil: {p.full_name} ({p.admission_no})",
            "Students"
        )
        
        flash(f"Pupil registered: {p.admission_no}")
        return redirect(url_for("pupils"))

    q = request.args.get("q", "")
    selected_grade = request.args.get("grade", "")
    query = Pupil.query.filter_by(school_id=current_school_id())

    if selected_grade:
        query = query.filter(Pupil.grade == selected_grade)

    if q:
        query = query.filter(
            (Pupil.full_name.ilike(f"%{q}%")) |
            (Pupil.admission_no.ilike(f"%{q}%")) |
            (Pupil.grade.ilike(f"%{q}%"))
        )

    return render_template(
        "pupils.html",
        settings=get_settings(),
        grades=GRADES,
        pupils=query.order_by(Pupil.grade, Pupil.full_name).all(),
        q=q,
        selected_grade=selected_grade
    )

@app.route("/edit_pupil/<int:pupil_id>", methods=["GET", "POST"])
def edit_pupil(pupil_id):
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("registrar", "receptionist"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=current_school_id()
    ).first_or_404()

    if request.method == "POST":
        pupil.full_name = request.form["full_name"]
        pupil.gender = request.form["gender"]
        pupil.dob = request.form.get("dob", "")
        pupil.grade = request.form["grade"]
        pupil.guardian_name = request.form["guardian_name"]
        pupil.guardian_phone = request.form["guardian_phone"]
        pupil.uses_bus = request.form["uses_bus"]
        pupil.status = request.form["status"]
        pupil.home_address = request.form.get("home_address", "")

        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_filename))
            pupil.photo = photo_filename

        db.session.commit()
        flash("Pupil updated successfully.")
        return redirect(url_for("pupils"))

    return render_template(
        "edit_pupil.html",
        pupil=pupil,
        grades=GRADES,
        settings=get_settings()
    )
    
@app.route("/student_profile/<int:pupil_id>")
def student_profile(pupil_id):
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("registrar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=current_school_id()
    ).first_or_404()
    year = current_year()

    total_due = due_until_month(pupil, year, "Term 2", "May")
    total_paid = paid_year(pupil.id, year)
    discounts = discount_year(pupil.id, year)
    balance = total_due - total_paid - discounts

    return render_template(
        "student_profile.html",
        settings=get_settings(),
        pupil=pupil,
        year=year,
        total_due=total_due,
        total_paid=total_paid,
        discounts=discounts,
        balance=balance,
        money=money
    )
    
@app.route("/exit_pupil/<int:pupil_id>", methods=["POST"])
def exit_pupil(pupil_id):
    if not login_required():
        return redirect(url_for("login"))

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=current_school_id()
    ).first_or_404()

    pupil.status = "Inactive"

    db.session.commit()

    flash("Pupil marked as inactive successfully.")
    return redirect(url_for("pupils"))
    
@app.route("/delete_pupil/<int:pupil_id>", methods=["POST"])
def delete_pupil(pupil_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can delete pupils.")
        return redirect(url_for("pupils"))

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=current_school_id()
    ).first_or_404()

    existing_payments = Payment.query.filter_by(
        school_id=current_school_id(),
        pupil_id=pupil.id
    ).count()

    if existing_payments > 0:
        flash("Cannot delete this pupil because payment records exist. Mark as Inactive instead.")
        return redirect(url_for("pupils"))

    db.session.delete(pupil)
    db.session.commit()

    flash("Pupil deleted successfully.")
    return redirect(url_for("pupils"))
    
@app.route("/print_pupils")
def print_pupils():
    if not login_required():
        return redirect(url_for("login"))

    selected_grade = request.args.get("grade", "")
    query = Pupil.query.filter_by(school_id=current_school_id())

    if selected_grade:
        query = query.filter(Pupil.grade == selected_grade)

    pupils = query.order_by(Pupil.full_name).all()

    return render_template(
        "print_pupils.html",
        settings=get_settings(),
        pupils=pupils,
        selected_grade=selected_grade,
        today=date.today()
    )
    
@app.route("/inactive_students")
def inactive_students():
    if not login_required():
        return redirect(url_for("login"))

    selected_grade = request.args.get("grade", "")
    query = Pupil.query.filter_by(
         school_id=current_school_id()
    ).filter(Pupil.status != "Active")

    if selected_grade:
        query = query.filter(Pupil.grade == selected_grade)

    pupils = query.order_by(Pupil.grade, Pupil.full_name).all()

    return render_template(
        "inactive_students.html",
        settings=get_settings(),
        pupils=pupils,
        grades=GRADES,
        selected_grade=selected_grade,
        today=date.today()
    )
    
@app.route("/promote_students", methods=["POST"])
def promote_students():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin"):
        flash("Only Admin can promote students.")
        return redirect(url_for("pupils"))

    promotion_map = {
        "PP1": "PP2",
        "PP2": "Grade 1",
        "Grade 1": "Grade 2",
        "Grade 2": "Grade 3",
        "Grade 3": "Grade 4",
        "Grade 4": "Grade 5",
        "Grade 5": "Grade 6",
        "Grade 6": "Grade 7",
        "Grade 7": "Grade 8",
        "Grade 8": "Grade 9"
    }

    count = 0

    for pupil in Pupil.query.filter_by(
           school_id=current_school_id(),
           status="Active"
    ).all():
        if pupil.grade in promotion_map:
            pupil.grade = promotion_map[pupil.grade]
            count += 1

    db.session.commit()

    flash(f"{count} students promoted successfully.")
    return redirect(url_for("pupils"))
    
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("registrar", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = session.get("school_id")

    selected_grade = request.args.get("grade", "")
    attendance_date = request.args.get("attendance_date", str(date.today()))

    if session.get("role", "").lower() == "teacher":
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()
        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade

    pupils = []
    if selected_grade:
        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Pupil.full_name).all()

    if request.method == "POST":
        selected_grade = request.form["grade"]
        attendance_date = request.form["attendance_date"]

        if session.get("role", "").lower() == "teacher":
            current_user = User.query.filter_by(
                username=session.get("username"),
                school_id=school_id
            ).first()
            if current_user and current_user.assigned_grade:
                selected_grade = current_user.assigned_grade

        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).all()

        absent_count = 0
        attendance_day = datetime.strptime(attendance_date, "%Y-%m-%d").date()

        for pupil in pupils:
            status = request.form.get(f"status_{pupil.id}", "Present")

            existing = Attendance.query.filter_by(
                school_id=school_id,
                pupil_id=pupil.id,
                attendance_date=attendance_day
            ).first()

            if existing:
                existing.status = status
            else:
                new_attendance = Attendance(
                    school_id=school_id,
                    pupil_id=pupil.id,
                    attendance_date=attendance_day,
                    status=status
                )
                db.session.add(new_attendance)

            if status == "Absent" and pupil.guardian_phone:
                sms = SMSMessage(
                    school_id=school_id,
                    recipient_name=pupil.guardian_name,
                    phone=pupil.guardian_phone,
                    message=(
                        f"Dear {pupil.guardian_name}, your child {pupil.full_name} "
                        f"has been marked Absent today {attendance_date}. "
                        f"Kindly contact the school if necessary. {get_settings().school_name}"
                    ),
                    category="Attendance Alert",
                    created_by=session.get("username", "")
                )
                db.session.add(sms)
                absent_count += 1

        db.session.commit()

        save_audit(
            f"Saved attendance for {selected_grade} on {attendance_date}. Absence alerts: {absent_count}",
            "Attendance"
        )

        flash(f"Attendance saved successfully. {absent_count} absence alerts saved.")
        return redirect(url_for("attendance", grade=selected_grade, attendance_date=attendance_date))

    return render_template(
        "attendance.html",
        settings=get_settings(),
        grades=GRADES,
        pupils=pupils,
        selected_grade=selected_grade,
        attendance_date=attendance_date
    )
@app.route("/attendance_report")
def attendance_report():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("registrar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    selected_grade = request.args.get("grade", "")
    attendance_date = request.args.get("attendance_date", str(date.today()))

    records = []

    if selected_grade:
        records = Attendance.query.join(Pupil).filter(
            Attendance.school_id == school_id,
            Pupil.school_id == school_id,
            Pupil.grade == selected_grade,
            Attendance.attendance_date == datetime.strptime(attendance_date, "%Y-%m-%d").date()
        ).all()

    present = sum(1 for r in records if r.status == "Present")
    absent = sum(1 for r in records if r.status == "Absent")
    late = sum(1 for r in records if r.status == "Late")

    return render_template(
        "attendance_report.html",
        settings=get_settings(),
        records=records,
        selected_grade=selected_grade,
        attendance_date=attendance_date,
        grades=GRADES,
        present=present,
        absent=absent,
        late=late
    )
@app.route("/report_cards")
def report_cards():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    selected_exam = request.args.get("exam_id", "")
    selected_grade = request.args.get("grade", "")

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade
        else:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

    exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Exam.academic_year.desc()).all()

    pupils = []

    if selected_exam and selected_grade:
        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Pupil.full_name).all()

    return render_template(
        "report_cards.html",
        settings=get_settings(),
        exams=exams,
        grades=GRADES,
        pupils=pupils,
        selected_exam=selected_exam,
        selected_grade=selected_grade
    )
@app.route("/report_card/<int:pupil_id>/<int:exam_id>")
def report_card(pupil_id, exam_id):
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=school_id
    ).first_or_404()

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if not current_user or not current_user.assigned_grade:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

        if pupil.grade != current_user.assigned_grade:
            flash("Access denied. You can only view report cards for your assigned grade.")
            return redirect(url_for("report_cards"))

    exam = Exam.query.filter_by(
        id=exam_id,
        school_id=school_id
    ).first_or_404()

    marks = Mark.query.filter_by(
        school_id=school_id,
        pupil_id=pupil.id,
        exam_id=exam.id
    ).all()

    total = sum(m.marks_obtained for m in marks)
    count = len(marks)
    average = total / count if count > 0 else 0

    grade_letter = "E"
    if average >= 80:
        grade_letter = "A"
    elif average >= 70:
        grade_letter = "B"
    elif average >= 60:
        grade_letter = "C"
    elif average >= 50:
        grade_letter = "D"

    classmates = Pupil.query.filter_by(
        school_id=school_id,
        grade=pupil.grade,
        status="Active"
    ).all()

    ranking_list = []

    for student in classmates:
        student_marks = Mark.query.filter_by(
            school_id=school_id,
            pupil_id=student.id,
            exam_id=exam.id
        ).all()

        student_total = sum(m.marks_obtained for m in student_marks)

        ranking_list.append({
            "pupil_id": student.id,
            "total": student_total
        })

    ranking_list = sorted(
        ranking_list,
        key=lambda x: x["total"],
        reverse=True
    )

    position = "-"
    for index, item in enumerate(ranking_list, start=1):
        if item["pupil_id"] == pupil.id:
            position = index
            break

    class_size = len(ranking_list)

    return render_template(
        "report_card.html",
        settings=get_settings(),
        pupil=pupil,
        exam=exam,
        marks=marks,
        total=total,
        average=average,
        grade_letter=grade_letter,
        position=position,
        class_size=class_size,
        today=date.today()
    )
@app.route("/rankings")
def rankings():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    selected_exam = request.args.get("exam_id", "")
    selected_grade = request.args.get("grade", "")

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade
        else:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

    exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Exam.academic_year.desc()).all()

    rows = []

    if selected_exam and selected_grade:
        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Pupil.full_name).all()

        for pupil in pupils:
            marks = Mark.query.filter_by(
                school_id=school_id,
                pupil_id=pupil.id,
                exam_id=int(selected_exam)
            ).all()

            total = sum(m.marks_obtained for m in marks)
            count = len(marks)
            average = total / count if count > 0 else 0

            rows.append({
                "pupil": pupil,
                "total": total,
                "average": average
            })

        rows = sorted(rows, key=lambda x: x["total"], reverse=True)

    return render_template(
        "rankings.html",
        settings=get_settings(),
        exams=exams,
        grades=GRADES,
        selected_exam=selected_exam,
        selected_grade=selected_grade,
        rows=rows
    )


@app.route("/grade_analysis")
def grade_analysis():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    selected_exam = request.args.get("exam_id", "")
    selected_grade = request.args.get("grade", "")

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade
        else:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

    exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Exam.academic_year.desc()).all()

    rows = []

    if selected_exam and selected_grade:
        subjects = Subject.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Subject.subject_name).all()

        for subject in subjects:
            marks = Mark.query.filter_by(
                school_id=school_id,
                exam_id=int(selected_exam),
                subject_id=subject.id
            ).all()

            total = sum(m.marks_obtained for m in marks)
            count = len(marks)
            average = total / count if count > 0 else 0
            highest = max([m.marks_obtained for m in marks], default=0)
            lowest = min([m.marks_obtained for m in marks], default=0)

            rows.append({
                "subject": subject,
                "count": count,
                "average": average,
                "highest": highest,
                "lowest": lowest
            })

    return render_template(
        "grade_analysis.html",
        settings=get_settings(),
        exams=exams,
        grades=GRADES,
        selected_exam=selected_exam,
        selected_grade=selected_grade,
        rows=rows
    )


@app.route("/teacher_remarks")
def teacher_remarks():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    selected_exam = request.args.get("exam_id", "")
    selected_grade = request.args.get("grade", "")

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade
        else:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

    exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Exam.academic_year.desc()).all()

    rows = []

    if selected_exam and selected_grade:
        rows = Mark.query.join(Pupil).filter(
            Mark.school_id == school_id,
            Pupil.school_id == school_id,
            Mark.exam_id == int(selected_exam),
            Pupil.grade == selected_grade
        ).order_by(Pupil.full_name).all()

    return render_template(
        "teacher_remarks.html",
        settings=get_settings(),
        exams=exams,
        grades=GRADES,
        selected_exam=selected_exam,
        selected_grade=selected_grade,
        rows=rows
    )
@app.route("/marks", methods=["GET", "POST"])
def marks():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    is_teacher = session.get("role", "").lower() == "teacher"

    selected_exam = request.args.get("exam_id", "")
    selected_grade = request.args.get("grade", "")

    if is_teacher:
        current_user = User.query.filter_by(
            username=session.get("username"),
            school_id=school_id
        ).first()

        if current_user and current_user.assigned_grade:
            selected_grade = current_user.assigned_grade
        else:
            flash("You have not been assigned to any grade. Contact Admin.")
            return redirect(url_for("dashboard"))

    exams = Exam.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Exam.academic_year.desc()).all()

    pupils = []
    subjects = []
    existing_marks = {}

    if selected_exam and selected_grade:
        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Pupil.full_name).all()

        subjects = Subject.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Subject.subject_name).all()

        marks_rows = Mark.query.filter_by(
            school_id=school_id,
            exam_id=int(selected_exam)
        ).all()

        for m in marks_rows:
            existing_marks[(m.pupil_id, m.subject_id)] = m

    if request.method == "POST":
        exam_id = int(request.form["exam_id"])
        grade = request.form["grade"]

        if is_teacher:
            current_user = User.query.filter_by(
                username=session.get("username"),
                school_id=school_id
            ).first()

            if current_user and current_user.assigned_grade:
                grade = current_user.assigned_grade
            else:
                flash("You have not been assigned to any grade. Contact Admin.")
                return redirect(url_for("dashboard"))

        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=grade,
            status="Active"
        ).all()

        subjects = Subject.query.filter_by(
            school_id=school_id,
            grade=grade,
            status="Active"
        ).all()

        for pupil in pupils:
            for subject in subjects:
                mark_value = float(request.form.get(f"mark_{pupil.id}_{subject.id}") or 0)
                remark = request.form.get(f"remark_{pupil.id}_{subject.id}", "")

                existing = Mark.query.filter_by(
                    school_id=school_id,
                    pupil_id=pupil.id,
                    exam_id=exam_id,
                    subject_id=subject.id
                ).first()

                if existing:
                    existing.marks_obtained = mark_value
                    existing.teacher_remark = remark
                else:
                    mark = Mark(
                        school_id=school_id,
                        pupil_id=pupil.id,
                        exam_id=exam_id,
                        subject_id=subject.id,
                        marks_obtained=mark_value,
                        teacher_remark=remark
                    )
                    db.session.add(mark)

        db.session.commit()
        flash("All subject marks saved successfully.")
        return redirect(url_for("marks", exam_id=exam_id, grade=grade))

    return render_template(
        "marks.html",
        settings=get_settings(),
        grades=GRADES,
        exams=exams,
        pupils=pupils,
        subjects=subjects,
        selected_exam=selected_exam,
        selected_grade=selected_grade,
        existing_marks=existing_marks
    )
@app.route("/exams", methods=["GET", "POST"])
def exams():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        exam = Exam(
            school_id=school_id,
            exam_name=request.form["exam_name"],
            academic_year=int(request.form["academic_year"]),
            term=request.form["term"],
            grade=request.form["grade"],
            total_marks=float(request.form.get("total_marks") or 100),
            status=request.form.get("status", "Active")
        )

        db.session.add(exam)
        db.session.commit()

        flash("Exam added successfully.")
        return redirect(url_for("exams"))

    rows = Exam.query.filter_by(
        school_id=school_id
    ).order_by(Exam.academic_year.desc(), Exam.term, Exam.grade).all()

    return render_template(
        "exams.html",
        settings=get_settings(),
        grades=GRADES,
        terms=TERMS,
        year=current_year(),
        rows=rows
    )
@app.route("/subjects", methods=["GET", "POST"])
def subjects():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        subject = Subject(
            school_id=school_id,
            subject_name=request.form["subject_name"],
            grade=request.form["grade"],
            teacher_name=request.form.get("teacher_name", ""),
            status=request.form.get("status", "Active")
        )

        db.session.add(subject)
        db.session.commit()

        flash("Subject added successfully.")
        return redirect(url_for("subjects"))

    rows = Subject.query.filter_by(
        school_id=school_id
    ).order_by(Subject.grade, Subject.subject_name).all()

    return render_template(
        "subjects.html",
        settings=get_settings(),
        grades=GRADES,
        rows=rows
    )
@app.route("/edit_subject/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    subject = Subject.query.filter_by(
        id=subject_id,
        school_id=current_school_id()
    ).first_or_404()

    if request.method == "POST":
        subject.subject_name = request.form["subject_name"]
        subject.grade = request.form["grade"]
        subject.teacher_name = request.form.get("teacher_name", "")
        subject.status = request.form.get("status", "Active")

        db.session.commit()
        flash("Subject updated successfully.")
        return redirect(url_for("subjects"))

    return render_template(
        "edit_subject.html",
        settings=get_settings(),
        subject=subject,
        grades=GRADES
    )
@app.route("/fees", methods=["GET","POST"])
def fees():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        academic_year = int(request.form["academic_year"])
        grade = request.form["grade"]
        term = request.form["term"]

        tuition_fee = float(request.form.get("tuition_fee") or 0)
        bus_fee = float(request.form.get("bus_fee") or 0)
        exam_fee = float(request.form.get("exam_fee") or 0)
        admission_fee = float(request.form.get("admission_fee") or 0)

        # Save fees automatically for all months in the term
        for month in TERM_MONTHS.get(term, []):
            fee = get_fee(academic_year, grade, term, month)

            fee.tuition_fee = tuition_fee
            fee.bus_fee = bus_fee

            # Exam fee only once per term
            fee.exam_fee = exam_fee if month == TERM_MONTHS[term][0] else 0

            # Admission fee only once
            fee.admission_fee = admission_fee if month == TERM_MONTHS[term][0] else 0

            db.session.add(fee)

        db.session.commit()

        flash("Fee structure saved successfully.")
        return redirect(url_for("fees"))

    return render_template(
        "fees.html",
        settings=get_settings(),
        grades=GRADES,
        terms=TERMS,
        term_months=TERM_MONTHS,
        year=current_year(),
        fees=FeeStructure.query.filter_by(
            school_id=current_school_id()
      ).order_by(FeeStructure.academic_year.desc()).all(),
        money=money
    )
            

@app.route("/discounts", methods=["GET", "POST"])
def discounts():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        d = Discount(
            school_id=school_id,
            pupil_id=int(request.form["pupil_id"]),
            academic_year=int(request.form["academic_year"]),
            term=request.form["term"],
            amount=float(request.form.get("amount") or 0),
            reason=request.form.get("reason", ""),
            created_by=session["username"]
        )

        db.session.add(d)
        db.session.commit()

        save_audit(
            f"Added discount for pupil ID {d.pupil_id}: KES {d.amount:,.2f}",
            "Finance"
        )

        flash("Discount/waiver added.")
        return redirect(url_for("discounts"))

    pupils = Pupil.query.filter_by(
        school_id=school_id,
        status="Active"
    ).order_by(Pupil.full_name).all()

    discounts = Discount.query.filter_by(
        school_id=school_id
    ).order_by(Discount.id.desc()).all()

    return render_template(
        "discounts.html",
        settings=get_settings(),
        pupils=pupils,
        discounts=discounts,
        year=current_year(),
        money=money
    )
    
@app.route("/payments", methods=["GET","POST"])
def payments():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        year = int(request.form["academic_year"])
        term = request.form["term"]

        pay = Payment(
            school_id=current_school_id(),
            receipt_no=receipt_no(year, term),
            pupil_id=int(request.form["pupil_id"]),
            academic_year=year,
            term=term,
            month=request.form["month"],
            tuition_paid=float(request.form.get("tuition_paid") or 0),
            bus_paid=float(request.form.get("bus_paid") or 0),
            exam_paid=float(request.form.get("exam_paid") or 0),
            admission_paid=float(request.form.get("admission_paid") or 0),
            payment_method=request.form["payment_method"],
            payment_date=datetime.strptime(request.form["payment_date"], "%Y-%m-%d").date(),
            collected_by=session["username"]
        )

        db.session.add(pay)
        db.session.commit()

        pupil = Pupil.query.get(pay.pupil_id)
        school = get_settings()

        amount_paid = (
            pay.tuition_paid +
            pay.bus_paid +
            pay.exam_paid +
            pay.admission_paid
        )

        balance = (
            due_until_month(pupil, pay.academic_year, pay.term, pay.month)
            - paid_year(pupil.id, pay.academic_year)
            - discount_year(pupil.id, pay.academic_year)
        )

        save_audit(
            f"Recorded payment: {pay.receipt_no}",
            "Finance"
        )

        if pupil and pupil.guardian_phone:
            sms = SMSMessage(
                school_id=current_school_id(),
                recipient_name=pupil.guardian_name,
                phone=pupil.guardian_phone,
                message=(
                    f"Dear {pupil.guardian_name}, we have received KES {amount_paid:,.2f} "
                    f"for {pupil.full_name}. Receipt No: {pay.receipt_no}. "
                    f"Balance: KES {balance:,.2f}. Thank you. {school.school_name}"
                ),
                category="Payment Confirmation",
                created_by=session.get("username", "")
            )

            db.session.add(sms)
            db.session.commit()

            save_audit(
                f"Generated payment confirmation SMS: {pay.receipt_no}",
                "Communication"
            )

        return redirect(url_for("receipt", payment_id=pay.id))

    pupils = Pupil.query.filter_by(
        school_id=current_school_id(),
        status="Active"
    ).order_by(Pupil.full_name.asc()).all()

    return render_template(
        "payments.html",
        settings=get_settings(),
        pupils=pupils,
        terms=TERMS,
        term_months=TERM_MONTHS,
        year=current_year(),
        today=date.today(),
        payments=Payment.query.filter_by(
            school_id=current_school_id()
        ).order_by(Payment.id.desc()).all(),
        money=money
    )
 
@app.route("/daily_collections")
def daily_collections():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    selected_date = request.args.get("date", str(date.today()))
    export_pdf = request.args.get("pdf")
    report_date = datetime.strptime(selected_date, "%Y-%m-%d").date()

    payments = Payment.query.filter_by(
        school_id=current_school_id(),
        payment_date=report_date
    ).order_by(Payment.id.desc()).all()

    tuition_total = sum(p.tuition_paid for p in payments)
    bus_total = sum(p.bus_paid for p in payments)
    exam_total = sum(p.exam_paid for p in payments)
    admission_total = sum(p.admission_paid for p in payments)
    total = tuition_total + bus_total + exam_total + admission_total

    if export_pdf:
        html = render_template(
            "daily_collections_pdf.html",
            settings=get_settings(),
            payments=payments,
            selected_date=selected_date,
            tuition_total=tuition_total,
            bus_total=bus_total,
            exam_total=exam_total,
            admission_total=admission_total,
            total=total,
            money=money
        )

        pdf = generate_pdf(html)
        response = make_response(pdf.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "attachment; filename=daily_collections.pdf"
        return response

    return render_template(
        "daily_collections.html",
        settings=get_settings(),
        payments=payments,
        selected_date=selected_date,
        tuition_total=tuition_total,
        bus_total=bus_total,
        exam_total=exam_total,
        admission_total=admission_total,
        total=total,
        money=money
    )
   
@app.route("/monthly_collections")
def monthly_collections():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    selected_month = request.args.get("month", str(date.today())[:7])
    export_pdf = request.args.get("pdf")

    start_date = datetime.strptime(selected_month + "-01", "%Y-%m-%d").date()

    if start_date.month == 12:
        end_date = date(start_date.year + 1, 1, 1)
    else:
        end_date = date(start_date.year, start_date.month + 1, 1)

    payments = Payment.query.filter(
        Payment.school_id == current_school_id(),
        Payment.payment_date >= start_date,
        Payment.payment_date < end_date
    ).order_by(Payment.id.desc()).all()

    tuition_total = sum(p.tuition_paid for p in payments)
    bus_total = sum(p.bus_paid for p in payments)
    exam_total = sum(p.exam_paid for p in payments)
    admission_total = sum(p.admission_paid for p in payments)

    total = tuition_total + bus_total + exam_total + admission_total

    if export_pdf:
        html = render_template(
            "monthly_collections_pdf.html",
            settings=get_settings(),
            payments=payments,
            selected_month=selected_month,
            tuition_total=tuition_total,
            bus_total=bus_total,
            exam_total=exam_total,
            admission_total=admission_total,
            total=total,
            money=money
        )

        pdf = generate_pdf(html)
        response = make_response(pdf.read())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "attachment; filename=monthly_collections.pdf"
        return response

    return render_template(
        "monthly_collections.html",
        settings=get_settings(),
        payments=payments,
        selected_month=selected_month,
        tuition_total=tuition_total,
        bus_total=bus_total,
        exam_total=exam_total,
        admission_total=admission_total,
        total=total,
        money=money
    )
@app.route("/termly_collections")
def termly_collections():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    selected_year = int(request.args.get("year", current_year()))
    selected_term = request.args.get("term", "Term 1")

    payments = Payment.query.filter_by(
        school_id=current_school_id(),
        academic_year=selected_year,
        term=selected_term
    ).order_by(Payment.id.desc()).all()

    tuition_total = sum(p.tuition_paid for p in payments)
    bus_total = sum(p.bus_paid for p in payments)
    exam_total = sum(p.exam_paid for p in payments)
    admission_total = sum(p.admission_paid for p in payments)

    total = tuition_total + bus_total + exam_total + admission_total

    return render_template(
        "termly_collections.html",
        settings=get_settings(),
        payments=payments,
        selected_year=selected_year,
        selected_term=selected_term,
        terms=TERMS,
        tuition_total=tuition_total,
        bus_total=bus_total,
        exam_total=exam_total,
        admission_total=admission_total,
        total=total,
        money=money
    )
@app.route("/yearly_collections")
def yearly_collections():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    selected_year = int(request.args.get("year", current_year()))

    payments = Payment.query.filter_by(
        school_id=current_school_id(),
        academic_year=selected_year
    ).order_by(Payment.id.desc()).all()

    tuition_total = sum(p.tuition_paid for p in payments)
    bus_total = sum(p.bus_paid for p in payments)
    exam_total = sum(p.exam_paid for p in payments)
    admission_total = sum(p.admission_paid for p in payments)

    total = tuition_total + bus_total + exam_total + admission_total

    return render_template(
        "yearly_collections.html",
        settings=get_settings(),
        payments=payments,
        selected_year=selected_year,
        tuition_total=tuition_total,
        bus_total=bus_total,
        exam_total=exam_total,
        admission_total=admission_total,
        total=total,
        money=money
    )
@app.route("/defaulters_report")
def defaulters_report():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    year = int(request.args.get("year", current_year()))
    selected_grade = request.args.get("grade", "")
    selected_term = request.args.get("term", "Term 1")
    selected_month = request.args.get("month", "May")

    query = Pupil.query.filter_by(
         school_id=current_school_id(),
         status="Active"
    )

    if selected_grade:
        query = query.filter_by(grade=selected_grade)

    rows = []

    for p in query.all():
        total_due = due_until_month(p, year, selected_term, selected_month)
        total_paid = paid_year(p.id, year)
        discounts = discount_year(p.id, year)
        balance = total_due - total_paid - discounts

        if balance > 0:
            rows.append({
                "pupil": p,
                "total_due": total_due,
                "total_paid": total_paid,
                "discounts": discounts,
                "balance": balance
            })

    total_defaulters = len(rows)
    total_balance = sum(row["balance"] for row in rows)

    return render_template(
    "defaulters_report.html",
    settings=get_settings(),
    grades=GRADES,
    selected_grade=selected_grade,
    selected_term=selected_term,
    selected_month=selected_month,
    terms=TERMS,
    term_months=TERM_MONTHS,
    total_defaulters=total_defaulters,
    total_balance=total_balance,
    rows=rows,
    year=year,
    money=money
)
@app.route("/receipt/<int:payment_id>")
def receipt(payment_id):
    if not login_required(): return redirect(url_for("login"))
    p = Payment.query.filter_by(
        id=payment_id,
        school_id=current_school_id()
   ).first_or_404()
    pupil = p.pupil
    opening = opening_arrears(pupil, p.academic_year)
    closing = due_until_month(pupil, p.academic_year, p.term, p.month) - paid_year(pupil.id, p.academic_year) - discount_year(pupil.id, p.academic_year)
    return render_template("receipt.html", settings=get_settings(), p=p, pupil=pupil, opening=opening,
                           closing=closing, discounts=discount_year(pupil.id, p.academic_year), money=money)
@app.route("/balances")
def balances():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    year = int(request.args.get("year", current_year()))
    term = request.args.get("term", "Term 1")

    months = TERM_MONTHS.get(term, [])
    month = request.args.get("month", months[0] if months else "")

    rows = []

    for p in Pupil.query.filter_by(
        school_id=current_school_id(),
        status="Active"
    ).all():
        if month:
            md = monthly_due(p, year, term, month)
            month_due = sum(md.values())
            month_paid = paid_month(p.id, year, term, month)
        else:
            month_due = 0
            month_paid = 0

        year_total_due = due_until_month(p, year, term, month)
        year_total_paid = paid_year(p.id, year)
        discounts = discount_year(p.id, year)
        closing = year_total_due - year_total_paid - discounts

        rows.append({
            "pupil": p,
            "opening": 0,
            "month_due": month_due,
            "month_paid": month_paid,
            "discounts": discounts,
            "closing": closing
        })

    return render_template(
        "balances.html",
        settings=get_settings(),
        rows=rows,
        year=year,
        term=term,
        month=month,
        terms=TERMS,
        term_months=TERM_MONTHS,
        money=money
    )
@app.route("/credits")
def credits():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    year = int(request.args.get("year", current_year()))

    rows = []

    for p in Pupil.query.filter_by(
        school_id=current_school_id(),
        status="Active"
    ).all():
        due = year_due(p, year)
        paid = paid_year(p.id, year)
        discounts = discount_year(p.id, year)

        balance = due - paid - discounts

        if balance < 0:
            rows.append({
                "pupil": p,
                "credit": abs(balance)
            })

    return render_template(
        "credits.html",
        settings=get_settings(),
        rows=rows,
        year=year,
        money=money
    )

@app.route("/statement/<int:pupil_id>/<int:year>")
def statement(pupil_id, year):
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    pupil = Pupil.query.filter_by(
        id=pupil_id,
        school_id=current_school_id()
    ).first_or_404()

    entries = []
    bal = opening_arrears(pupil, year)

    if bal > 0:
        entries.append((
            f"01/01/{year}",
            f"Opening Arrears B/F from {year-1}",
            bal,
            0,
            bal
        ))

    for term in TERMS:
        for month in term_months(term):

            if year == 2026 and month not in [
                "May", "June", "July",
                "August", "September", "October",
                "November", "December"
            ]:
                continue

            d = monthly_due(pupil, year, term, month)
            debit = d["tuition"] + d["bus"] + d["exam"] + d["admission"]

            if debit:
                bal += debit
                entries.append((
                    "",
                    f"{month} {term} Fees",
                    debit,
                    0,
                    bal
                ))

            discounts = Discount.query.filter_by(
                school_id=current_school_id(),
                pupil_id=pupil.id,
                academic_year=year
           ).all()

            for pay in payments:
                credit = (
                    pay.tuition_paid +
                    pay.bus_paid +
                    pay.exam_paid +
                    pay.admission_paid
                )

                if credit:
                    bal -= credit
                    entries.append((
                        str(pay.payment_date),
                        f"Payment {pay.receipt_no} ({term}, {month})",
                        0,
                        credit,
                        bal
                    ))

    discounts = Discount.query.filter_by(
        pupil_id=pupil.id,
        academic_year=year
    ).all()

    for d in discounts:
        bal -= d.amount
        entries.append((
            str(d.created_at),
            f"Discount/Waiver: {d.reason}",
            0,
            d.amount,
            bal
        ))

    return render_template(
        "statement.html",
        settings=get_settings(),
        pupil=pupil,
        year=year,
        entries=entries,
        closing=bal,
        money=money
    )

@app.route("/statements")
def statements():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    return render_template(
        "statements.html",
        settings=get_settings(),
        pupils=Pupil.query.filter_by(
        school_id=current_school_id()
        ).order_by(Pupil.full_name).all(),
        year=current_year()
)

@app.route("/fee_reminders", methods=["GET", "POST"])
def fee_reminders():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    year = int(request.args.get("year", current_year()))
    selected_grade = request.args.get("grade", "")
    selected_term = request.args.get("term", "Term 1")
    selected_month = request.args.get("month", "May")

    rows = []

    query = Pupil.query.filter_by(
         school_id=current_school_id(),
         status="Active"
    )

    if selected_grade:
        query = query.filter_by(grade=selected_grade)

    for p in query.order_by(Pupil.grade, Pupil.full_name).all():
        total_due = due_until_month(p, year, selected_term, selected_month)
        total_paid = paid_year(p.id, year)
        discounts = discount_year(p.id, year)
        balance = total_due - total_paid - discounts

        if balance > 0:
            rows.append({
                "pupil": p,
                "balance": balance
            })

    if request.method == "POST":
        count = 0

        for row in rows:
            p = row["pupil"]
            balance = row["balance"]

            if p.guardian_phone:
                message = (
                    f"Dear {p.guardian_name}, your child {p.full_name} "
                    f"has an outstanding fee balance of KES {balance:,.2f}. "
                    f"Kindly clear the balance. {get_settings().school_name}"
                )

                sms = SMSMessage(
                    school_id=current_school_id(),
                    recipient_name=p.guardian_name,
                    phone=p.guardian_phone,
                    message=message,
                    category="Fees",
                    created_by=session.get("username", "")
                )

                db.session.add(sms)
                count += 1

        db.session.commit()

        save_audit(
            f"Created fee reminder SMS for {count} parents",
            "Communication"
        )

        flash(f"Fee reminder SMS saved for {count} parents.")
        return redirect(url_for(
            "fee_reminders",
            year=year,
            grade=selected_grade,
            term=selected_term,
            month=selected_month
        ))

    return render_template(
        "fee_reminders.html",
        settings=get_settings(),
        grades=GRADES,
        terms=TERMS,
        term_months=TERM_MONTHS,
        rows=rows,
        year=year,
        selected_grade=selected_grade,
        selected_term=selected_term,
        selected_month=selected_month,
        money=money
    )

@app.route("/bulk_sms", methods=["GET", "POST"])
def bulk_sms():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher", "receptionist", "bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    selected_grade = request.args.get("grade", "")
    pupils = []

    if selected_grade:
        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=selected_grade,
            status="Active"
        ).order_by(Pupil.full_name).all()

    if request.method == "POST":
        grade = request.form["grade"]
        message = request.form["message"]
        category = request.form.get("category", "General")

        pupils = Pupil.query.filter_by(
            school_id=school_id,
            grade=grade,
            status="Active"
        ).all()

        count = 0

        for p in pupils:
            if p.guardian_phone:
                sms = SMSMessage(
                    school_id=school_id,
                    recipient_name=p.guardian_name,
                    phone=p.guardian_phone,
                    message=message,
                    category=category,
                    created_by=session.get("username", "")
                )
                db.session.add(sms)
                count += 1

        db.session.commit()

        save_audit(
            f"Created bulk SMS for {count} parents in {grade}",
            "Communication"
        )

        flash(f"Bulk SMS saved for {count} parents.")
        return redirect(url_for("bulk_sms", grade=grade))

    return render_template(
        "bulk_sms.html",
        settings=get_settings(),
        grades=GRADES,
        selected_grade=selected_grade,
        pupils=pupils
    )
@app.route("/sms_messages", methods=["GET", "POST"])
def sms_messages():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher", "receptionist", "bursar"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        sms = SMSMessage(
            school_id=school_id,
            recipient_name=request.form.get("recipient_name", ""),
            phone=request.form["phone"],
            message=request.form["message"],
            category=request.form.get("category", "General"),
            created_by=session.get("username", "")
        )

        db.session.add(sms)
        db.session.commit()

        save_audit(
            f"Created SMS message for: {sms.recipient_name} ({sms.phone})",
            "Communication"
        )

        flash("SMS message saved as pending.")
        return redirect(url_for("sms_messages"))

    rows = SMSMessage.query.filter_by(
        school_id=school_id
    ).order_by(SMSMessage.created_at.desc()).all()

    return render_template(
        "sms_messages.html",
        settings=get_settings(),
        rows=rows
    )

@app.route("/announcements", methods=["GET", "POST"])
def announcements():
    if not login_required():
        return redirect(url_for("login"))

    if not role_allowed("admin", "teacher", "receptionist"):
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        ann = Announcement(
            school_id=school_id,
            title=request.form["title"],
            message=request.form["message"],
            audience=request.form["audience"],
            created_by=session.get("username", "")
        )

        db.session.add(ann)
        db.session.commit()

        save_audit(
            f"Created announcement: {ann.title}",
            "Communication"
        )

        flash("Announcement created successfully.")
        return redirect(url_for("announcements"))

    rows = Announcement.query.filter_by(
        school_id=school_id
    ).order_by(
        Announcement.created_at.desc()
    ).all()

    return render_template(
        "announcements.html",
        settings=get_settings(),
        rows=rows
    )
    
@app.route("/staff", methods=["GET", "POST"])
def staff():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can manage staff.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()
    subjects = Subject.query.filter_by(
    school_id=school_id,
    status="Active"
).order_by(
    Subject.grade,
    Subject.subject_name
).all()

    if request.method == "POST":
        selected_subjects = ",".join(
    request.form.getlist("assigned_subjects")
    )
        role = request.form["role"]
        assigned_grade = request.form.get("assigned_grade", "")

        staff_member = Staff(
            school_id=school_id,
            full_name=request.form["full_name"],
            phone=request.form.get("phone", ""),
            email=request.form.get("email", ""),
            id_no=request.form.get("id_no", ""),
            role=role,
            assigned_grade=assigned_grade,
            assigned_subjects=selected_subjects,
            status=request.form.get("status", "Active")
        )

        db.session.add(staff_member)

        if request.form.get("create_login") == "yes":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                flash("Username and temporary password are required when creating a login account.")
                return redirect(url_for("staff"))

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash("Username already exists. Choose another username.")
                return redirect(url_for("staff"))

            new_user = User(
                school_id=school_id,
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                assigned_grade=assigned_grade,
                assigned_subjects=selected_subjects,
                is_active=True
            )

            db.session.add(new_user)

        db.session.commit()

        save_audit(
            f"Added staff member: {staff_member.full_name}",
            "Staff"
        )

        flash("Staff profile added successfully.")
        return redirect(url_for("staff"))

    rows = Staff.query.filter_by(
        school_id=school_id
    ).order_by(Staff.full_name).all()

    return render_template(
       "staff.html",
       settings=get_settings(),
       rows=rows,
       grades=GRADES,
       subjects=subjects
)
    
@app.route("/audit_logs")
def audit_logs():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() not in ["admin", "super admin"]:
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    if session.get("role", "").lower() == "super admin":
        logs = AuditLog.query.order_by(
            AuditLog.created_at.desc()
        ).limit(500).all()
    else:
        logs = AuditLog.query.filter_by(
            school_id=current_school_id()
        ).order_by(
            AuditLog.created_at.desc()
        ).limit(500).all()

    return render_template(
        "audit_logs.html",
        settings=get_settings(),
        logs=logs
    )
    
@app.route("/users", methods=["GET", "POST"])
def users():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    school_id = current_school_id()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        assigned_grade = request.form.get("assigned_grade", "")

        new_user = User(
            school_id=school_id,
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            assigned_grade=assigned_grade
        )

        db.session.add(new_user)
        db.session.commit()

        save_audit(
            f"Created user account: {username}",
            "Security"
        )

        flash("User created successfully.")
        return redirect(url_for("users"))

    all_users = User.query.filter_by(
        school_id=school_id
    ).order_by(User.username).all()

    return render_template(
        "users.html",
        settings=get_settings(),
        users=all_users,
        grades=GRADES
    )


@app.route("/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can edit users.")
        return redirect(url_for("dashboard"))

    user = User.query.filter_by(
        id=user_id,
        school_id=current_school_id()
    ).first_or_404()

    if request.method == "POST":
        user.role = request.form["role"]
        user.assigned_grade = request.form.get("assigned_grade", "")
        user.is_active = bool(int(request.form["is_active"]))

        db.session.commit()

        save_audit(
            f"Updated user account: {user.username}",
            "Security"
        )

        flash("User updated successfully.")
        return redirect(url_for("users"))

    return render_template(
        "edit_user.html",
        settings=get_settings(),
        user=user,
        grades=GRADES
    )


@app.route("/reset_user_password/<int:user_id>", methods=["POST"])
def reset_user_password(user_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() not in ["admin", "super admin"]:
        flash("Only Admin can reset passwords.")
        return redirect(url_for("users"))

    user = User.query.filter_by(
        id=user_id,
        school_id=current_school_id()
    ).first_or_404()

    new_password = request.form["new_password"]
    user.password_hash = generate_password_hash(new_password)

    db.session.commit()

    save_audit(
        f"Reset password for user: {user.username}",
        "Security"
    )

    flash("Password reset successfully.")
    return redirect(url_for("users"))


@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can delete users.")
        return redirect(url_for("dashboard"))

    user = User.query.filter_by(
        id=user_id,
        school_id=current_school_id()
    ).first_or_404()

    if user.username == "admin":
        flash("Main admin cannot be deleted.")
        return redirect(url_for("users"))

    if user.username == session.get("username"):
        flash("You cannot delete your own account while logged in.")
        return redirect(url_for("users"))

    db.session.delete(user)
    db.session.commit()

    save_audit(
        f"Deleted user account: {user.username}",
        "Security"
    )

    flash("User deleted successfully.")
    return redirect(url_for("users"))


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() == "super admin":
        user = User.query.filter_by(
            username=session["username"]
        ).first_or_404()
    else:
        user = User.query.filter_by(
            username=session["username"],
            school_id=current_school_id()
        ).first_or_404()

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user.password_hash, current_password):
            flash("Current password is incorrect.")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for("change_password"))

        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        save_audit(
            f"Changed own password: {user.username}",
            "Security"
        )

        flash("Password changed successfully.")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html", settings=get_settings())
    
@app.route("/reset_payments_may2026")
def reset_payments_may2026():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can reset payments.")
        return redirect(url_for("dashboard"))

    Payment.query.delete()
    db.session.commit()

    flash("All test payments have been cleared. System is ready to start from May 2026.")
    return redirect(url_for("dashboard"))
    
@app.route("/reset_fee_structure_may2026")
def reset_fee_structure_may2026():
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role", "").lower() != "admin":
        flash("Only Admin can reset fee structure.")
        return redirect(url_for("dashboard"))

    FeeStructure.query.delete()
    db.session.commit()

    flash("Old fee structures cleared. You can now enter clean fees from May 2026.")
    return redirect(url_for("fees"))


if __name__ == "__main__":
    with app.app_context():
        init_database()
    app.run(debug=True)
