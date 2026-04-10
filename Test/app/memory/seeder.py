import uuid

from vanna import ToolContext
from vanna.core.user import User
from vanna.integrations.local.agent_memory import DemoAgentMemory

QA_PAIRS = [
    # Patient queries
    {"question": "How many patients do we have?",
     "sql": "SELECT COUNT(*) AS total_patients FROM patients"},
    {"question": "List all patients from New York",
     "sql": "SELECT * FROM patients WHERE city = 'New York'"},
    {"question": "Show female patients registered in the last 6 months",
     "sql": "SELECT * FROM patients WHERE gender = 'F' AND registered_date >= date('now', '-6 months')"},
    # Doctor queries
    {"question": "How many appointments does each doctor have?",
     "sql": "SELECT d.name, COUNT(a.id) AS appointment_count FROM doctors d LEFT JOIN appointments a ON d.id = a.doctor_id GROUP BY d.name ORDER BY appointment_count DESC"},
    {"question": "Who is the busiest doctor?",
     "sql": "SELECT d.name, COUNT(a.id) AS appointment_count FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.name ORDER BY appointment_count DESC LIMIT 1"},
    {"question": "List doctors in the Cardiology department",
     "sql": "SELECT name, specialization FROM doctors WHERE department = 'Cardiology Dept'"},
    # Appointment queries
    {"question": "Count appointments by status",
     "sql": "SELECT status, COUNT(*) AS count FROM appointments GROUP BY status"},
    {"question": "Show appointments for the next month",
     "sql": "SELECT * FROM appointments WHERE appointment_date BETWEEN date('now') AND date('now', '+1 month')"},
    {"question": "List appointments for Dr. Smith's patients",
     "sql": "SELECT a.* FROM appointments a JOIN doctors d ON a.doctor_id = d.id WHERE d.name LIKE '%Smith%'"},
    # Financial queries
    {"question": "Show total revenue by doctor",
     "sql": "SELECT d.name, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.name ORDER BY total_revenue DESC"},
    {"question": "What is the total amount of unpaid invoices?",
     "sql": "SELECT SUM(total_amount - paid_amount) AS total_unpaid FROM invoices WHERE status != 'Paid'"},
    {"question": "What is the average cost of a treatment?",
     "sql": "SELECT AVG(cost) AS average_cost FROM treatments"},
    # Time-based queries
    {"question": "Show revenue trends for the last 3 months",
     "sql": "SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS monthly_revenue FROM invoices WHERE invoice_date >= date('now', '-3 months') GROUP BY month ORDER BY month"},
    {"question": "Which city has the most patients?",
     "sql": "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"},
    {"question": "Show the top 5 patients by total spending",
     "sql": "SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spent FROM patients p JOIN invoices i ON p.id = i.patient_id GROUP BY p.id ORDER BY total_spent DESC LIMIT 5"},
]


async def seed_memory_instance(memory: DemoAgentMemory) -> int:
    """Seed the agent memory with known Q&A pairs. Returns the count seeded."""
    seed_user = User(id="default_user", username="Default User", group_memberships=["admin"])
    tool_context = ToolContext(
        user=seed_user,
        conversation_id="seed-" + str(uuid.uuid4()),
        request_id=str(uuid.uuid4()),
        agent_memory=memory,
    )
    count = 0
    for pair in QA_PAIRS:
        try:
            await memory.save_tool_usage(
                pair["question"],
                "run_sql",
                {"sql": pair["sql"]},
                tool_context,
                success=True,
            )
            count += 1
        except Exception as e:
            print(f"[seeder] Failed for '{pair['question']}': {e}")
    return count
