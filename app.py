from flask import Flask, render_template, request, redirect, url_for, flash, Response
import mysql.connector
from mysql.connector import Error
import csv, io
from datetime import date

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "hospital_secret_key"   # safe to keep/change

# ---------- DB helper ----------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",          # <-- put your MySQL user
            password="ROOT",      # <-- put your MySQL password
            database="hospital_db"
        )
        return conn
    except Error as e:
        print("DB connection error:", e)
        return None

# ---------- Home / Dashboard ----------
@app.route("/")
def index():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("index.html", counts={}, recent_patients=[], recent_doctors=[])

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS c FROM Patients"); counts_pat = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM Doctors"); counts_doc = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM Appointments"); counts_appt = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM Bills"); counts_bills = cur.fetchone()['c']

    cur.execute("SELECT * FROM Patients ORDER BY patient_id DESC LIMIT 5")
    recent_patients = cur.fetchall()
    cur.execute("SELECT * FROM Doctors ORDER BY doctor_id DESC LIMIT 5")
    recent_doctors = cur.fetchall()

    cur.close(); conn.close()
    counts = {"patients": counts_pat, "doctors": counts_doc, "appointments": counts_appt, "bills": counts_bills}
    return render_template("index.html", counts=counts, recent_patients=recent_patients, recent_doctors=recent_doctors)

# ---------- Patients (list + add) ----------
@app.route("/patients", methods=["GET", "POST"])
def patients():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("patients.html", patients=[])

    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age") or None
        contact = request.form.get("contact", "").strip()
        disease = request.form.get("disease", "").strip()
        try:
            cur.execute("INSERT INTO Patients (name, age, contact, disease) VALUES (%s,%s,%s,%s)",
                        (name, age, contact, disease))
            conn.commit()
            flash("✅ Patient added")
        except Error as e:
            flash(f"❌ {e}")
    cur.execute("SELECT * FROM Patients ORDER BY patient_id DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("patients.html", patients=rows)

# ---------- Doctors (list + add) ----------
@app.route("/doctors", methods=["GET", "POST"])
def doctors():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("doctors.html", doctors=[])

    cur = conn.cursor(dictionary=True)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        specialization = request.form.get("specialization", "").strip()
        try:
            cur.execute("INSERT INTO Doctors (name, specialization) VALUES (%s,%s)", (name, specialization))
            conn.commit()
            flash("✅ Doctor added")
        except Error as e:
            flash(f"❌ {e}")
    cur.execute("SELECT * FROM Doctors ORDER BY doctor_id DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("doctors.html", doctors=rows)

# ---------- Appointments (book + list) ----------
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("appointments.html", patients=[], doctors=[], appts=[])

    cur = conn.cursor(dictionary=True)
    # for dropdowns
    cur.execute("SELECT patient_id, name FROM Patients ORDER BY name")
    patients = cur.fetchall()
    cur.execute("SELECT doctor_id, name, specialization FROM Doctors ORDER BY name")
    doctors = cur.fetchall()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appt_date = request.form.get("date") or date.today().isoformat()
        try:
            cur.execute("SELECT 1 FROM Patients WHERE patient_id=%s", (patient_id,))
            if cur.fetchone() is None:
                flash("❌ Patient does not exist")
            else:
                cur.execute("SELECT 1 FROM Doctors WHERE doctor_id=%s", (doctor_id,))
                if cur.fetchone() is None:
                    flash("❌ Doctor does not exist")
                else:
                    cur.execute("INSERT INTO Appointments (patient_id, doctor_id, date, status) VALUES (%s,%s,%s,'Scheduled')",
                                (patient_id, doctor_id, appt_date))
                    conn.commit()
                    flash("✅ Appointment booked")
        except Error as e:
            flash(f"❌ {e}")

    cur.execute("""
        SELECT A.appointment_id, A.date, A.status,
               P.patient_id, P.name AS patient,
               D.doctor_id, D.name AS doctor, D.specialization
        FROM Appointments A
        JOIN Patients P ON A.patient_id = P.patient_id
        JOIN Doctors D ON A.doctor_id = D.doctor_id
        ORDER BY A.date DESC, A.appointment_id DESC
    """)
    appts = cur.fetchall()
    cur.close(); conn.close()
    return render_template("appointments.html", patients=patients, doctors=doctors, appts=appts)

# ---------- Patient Appointments ----------
@app.route("/patient/<int:patient_id>/appointments")
def patient_appointments(patient_id):
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("patient_appointments.html", appts=[], patient=None)

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Patients WHERE patient_id=%s", (patient_id,))
    patient = cur.fetchone()
    cur.execute("""
        SELECT A.appointment_id, A.date, A.status, D.name AS doctor, D.specialization
        FROM Appointments A JOIN Doctors D ON A.doctor_id = D.doctor_id
        WHERE A.patient_id=%s
        ORDER BY A.date DESC
    """, (patient_id,))
    appts = cur.fetchall()
    cur.close(); conn.close()
    return render_template("patient_appointments.html", appts=appts, patient=patient)

# ---------- Doctor Schedule ----------
@app.route("/doctor/<int:doctor_id>/schedule")
def doctor_schedule(doctor_id):
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("doctor_schedule.html", appts=[], doctor=None)

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Doctors WHERE doctor_id=%s", (doctor_id,))
    doctor = cur.fetchone()
    cur.execute("""
        SELECT A.appointment_id, A.date, A.status, P.name AS patient
        FROM Appointments A JOIN Patients P ON A.patient_id = P.patient_id
        WHERE A.doctor_id=%s
        ORDER BY A.date DESC
    """, (doctor_id,))
    appts = cur.fetchall()
    cur.close(); conn.close()
    return render_template("doctor_schedule.html", appts=appts, doctor=doctor)

# ---------- Bills (create + list) ----------
@app.route("/bills", methods=["GET", "POST"])
def bills():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("bills.html", patients=[], bills=[])

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT patient_id, name FROM Patients ORDER BY name")
    patients = cur.fetchall()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        amount = request.form.get("amount")
        bill_date = request.form.get("date") or date.today().isoformat()
        try:
            cur.execute("SELECT 1 FROM Patients WHERE patient_id=%s", (patient_id,))
            if cur.fetchone() is None:
                flash("❌ Patient does not exist")
            else:
                cur.execute("INSERT INTO Bills (patient_id, amount, date) VALUES (%s,%s,%s)",
                            (patient_id, amount, bill_date))
                conn.commit()
                flash("✅ Bill generated")
        except Error as e:
            flash(f"❌ {e}")

    cur.execute("""
        SELECT B.bill_id, B.amount, B.date, P.name AS patient
        FROM Bills B JOIN Patients P ON B.patient_id = P.patient_id
        ORDER BY B.date DESC, B.bill_id DESC
    """)
    bills = cur.fetchall()
    cur.close(); conn.close()
    return render_template("bills.html", patients=patients, bills=bills)

# ---------- Revenue ----------
@app.route("/revenue")
def revenue():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return render_template("revenue.html", rows=[])

    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT YEAR(date) AS year, MONTH(date) AS month, SUM(amount) AS total
        FROM Bills
        GROUP BY YEAR(date), MONTH(date)
        ORDER BY YEAR(date) DESC, MONTH(date) DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return render_template("revenue.html", rows=rows)

# ---------- Export CSV ----------
@app.route("/export_bills")
def export_bills():
    conn = get_db_connection()
    if not conn:
        flash("❌ Database connection failed")
        return redirect(url_for("bills"))

    cur = conn.cursor()
    cur.execute("SELECT bill_id, patient_id, amount, date FROM Bills ORDER BY date")
    data = cur.fetchall()
    cur.close(); conn.close()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["bill_id", "patient_id", "amount", "date"])
    writer.writerows(data)
    output = si.getvalue()

    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=bills_export.csv"})

if __name__ == "__main__":
    app.run(debug=True)
