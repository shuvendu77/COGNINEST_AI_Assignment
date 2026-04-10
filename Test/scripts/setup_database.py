import sqlite3
import random
from datetime import datetime, timedelta

def setup_database():
    # If running from inside Test/, the path should be clinic.db
    # If running from Assignment/, it's Test/clinic.db
    # Using relative path that works when run from Assignment/ or Test/
    import os
    db_path = 'clinic.db' if os.path.basename(os.getcwd()) == 'Test' else 'Test/clinic.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    ''')

    # Dummy Data Generation
    specializations = ['Dermatology', 'Cardiology', 'Orthopedics', 'General', 'Pediatrics']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
    first_names = ['John', 'Jane', 'Michael', 'Emily', 'Chris', 'Sarah', 'David', 'Anna', 'James', 'Linda', 'Robert', 'Barbara', 'William', 'Elizabeth', 'Joseph', 'Susan']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas']
    statuses = ['Scheduled', 'Completed', 'Cancelled', 'No-Show']
    invoice_statuses = ['Paid', 'Pending', 'Overdue']

    # Insert Doctors
    doctors_data = []
    for i in range(15):
        spec = specializations[i % len(specializations)]
        doctors_data.append((f"Dr. {random.choice(first_names)} {random.choice(last_names)}", spec, f"{spec} Dept", f"555-{random.randint(1000, 9999)}"))
    cursor.executemany('INSERT INTO doctors (name, specialization, department, phone) VALUES (?, ?, ?, ?)', doctors_data)

    # Insert Patients
    patients_data = []
    for _ in range(200):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}@example.com" if random.random() > 0.1 else None
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}" if random.random() > 0.1 else None
        dob = (datetime.now() - timedelta(days=random.randint(365*18, 365*80))).date().isoformat()
        gender = random.choice(['M', 'F'])
        city = random.choice(cities)
        reg_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date().isoformat()
        patients_data.append((fn, ln, email, phone, dob, gender, city, reg_date))
    cursor.executemany('INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', patients_data)

    # Insert Appointments
    appointments_data = []
    patient_ids = list(range(1, 201))
    doctor_ids = list(range(1, 16))
    
    # Weight some doctors and patients
    weighted_patients = patient_ids[:20] * 5 + patient_ids[20:]
    weighted_doctors = doctor_ids[:5] * 3 + doctor_ids[5:]

    for _ in range(500):
        p_id = random.choice(weighted_patients)
        d_id = random.choice(weighted_doctors)
        app_date = (datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23), minutes=random.randint(0, 59))).isoformat()
        status = random.choice(statuses)
        notes = "Checkup" if random.random() > 0.5 else None
        appointments_data.append((p_id, d_id, app_date, status, notes))
    cursor.executemany('INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes) VALUES (?, ?, ?, ?, ?)', appointments_data)

    # Insert Treatments for Completed Appointments
    cursor.execute("SELECT id FROM appointments WHERE status = 'Completed'")
    completed_app_ids = [row[0] for row in cursor.fetchall()]
    
    treatments_data = []
    treatment_names = ['Routine Checkup', 'Blood Test', 'X-Ray', 'Consultation', 'MRI', 'Physical Therapy', 'Stitch Removal']
    for _ in range(350):
        if not completed_app_ids: break
        app_id = random.choice(completed_app_ids)
        name = random.choice(treatment_names)
        cost = round(random.uniform(50, 5000), 2)
        duration = random.randint(15, 120)
        treatments_data.append((app_id, name, cost, duration))
    cursor.executemany('INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes) VALUES (?, ?, ?, ?)', treatments_data)

    # Insert Invoices
    invoices_data = []
    for _ in range(300):
        p_id = random.choice(patient_ids)
        inv_date = (datetime.now() - timedelta(days=random.randint(0, 365))).date().isoformat()
        total = round(random.uniform(100, 10000), 2)
        status = random.choice(invoice_statuses)
        paid = total if status == 'Paid' else (round(random.uniform(0, total), 2) if status == 'Pending' else 0)
        invoices_data.append((p_id, inv_date, total, paid, status))
    cursor.executemany('INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status) VALUES (?, ?, ?, ?, ?)', invoices_data)

    conn.commit()
    
    # Print Summary
    cursor.execute("SELECT COUNT(*) FROM patients")
    num_patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM doctors")
    num_doctors = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments")
    num_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM treatments")
    num_treatments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM invoices")
    num_invoices = cursor.fetchone()[0]

    print(f"Created {num_patients} patients, {num_doctors} doctors, {num_appointments} appointments, {num_treatments} treatments, {num_invoices} invoices.")
    
    conn.close()

if __name__ == "__main__":
    setup_database()
