import difflib
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from ai_parser import extract_skills_from_pdf, generate_dynamic_job_requirements, suggest_government_schemes
from db_helper import save_extracted_skills_to_db, create_user, verify_user_login, get_admin_stats

# --- 2-FOLDER ARCHITECTURE CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(basedir, "..", "frontend")

app = Flask(__name__, 
            template_folder=frontend_dir, 
            static_folder=os.path.join(frontend_dir, "static"))

app.secret_key = os.getenv("SECRET_KEY", "skillgo_super_secret_key")

UPLOAD_FOLDER = os.path.join(basedir, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def calculate_real_employability(user_skills, job_reqs):
    missing = []
    total_score = 0
    max_score = 0
    safe_user_skills = {k.lower().strip(): v for k, v in user_skills.items()}

    for skill, details in job_reqs.items():
        req_prof = details["req_prof"]
        weight = details["weight"]
        safe_skill_name = skill.lower().strip()
        max_score += req_prof * weight
        user_prof = 0
        
        if safe_skill_name in safe_user_skills:
            user_prof = safe_user_skills[safe_skill_name]
        else:
            for u_skill, u_prof in safe_user_skills.items():
                if u_skill in safe_skill_name or safe_skill_name in u_skill:
                    user_prof = max(user_prof, u_prof)
            if user_prof == 0:
                close_matches = difflib.get_close_matches(safe_skill_name, safe_user_skills.keys(), n=1, cutoff=0.5)
                if close_matches:
                    user_prof = safe_user_skills[close_matches[0]]

        if user_prof < req_prof:
            missing.append(skill)
        total_score += min(user_prof, req_prof) * weight

    final_score = (total_score / max_score) * 100 if max_score > 0 else 0
    return round(final_score, 2), missing

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if create_user(request.form["name"], request.form["email"], request.form["password"], request.form["education"], request.form["city"]):
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))
        else:
            flash("Email already exists.")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = verify_user_login(request.form["email"], request.form["password"])
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/assessment")
def assessment():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("assessment.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    results = session.get("latest_results", [])
    return render_template("dashboard.html", results=results, name=session.get("user_name"))

@app.route("/schemes")
def schemes():
    if "user_id" not in session:
        return redirect(url_for("login"))
    missing_skills = session.get("latest_missing_skills", [])
    target_job = session.get("target_job", "Professional")
    if not missing_skills:
        return render_template("schemes.html", schemes=[], target_job=target_job)
    dynamic_schemes = suggest_government_schemes(target_job, missing_skills)
    return render_template("schemes.html", schemes=dynamic_schemes, target_job=target_job)

@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    if "user_id" not in session:
        return redirect(url_for("login"))
    file = request.files["resume_file"]
    target_job = request.form["target_job"]
    if file.filename == "":
        return redirect(url_for("assessment"))
        
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    user_skills_dict = extract_skills_from_pdf(filepath)
    os.remove(filepath)
    save_extracted_skills_to_db(session["user_id"], user_skills_dict)
    
    dynamic_job_reqs = generate_dynamic_job_requirements(target_job)
    results = []
    all_missing = set()

    for job_name, job_reqs in dynamic_job_reqs.items():
        score, missing = calculate_real_employability(user_skills_dict, job_reqs)
        results.append({"job": job_name, "gap": 100 - score, "missing": missing})
        all_missing.update(missing)

    session["latest_results"] = results
    session["latest_missing_skills"] = list(all_missing)
    session["target_job"] = target_job
    return redirect(url_for("dashboard"))

@app.route("/admin")
def admin():
    real_stats = get_admin_stats()
    return render_template("admin.html", stats=real_stats)

if __name__ == "__main__":
    app.run(debug=True)