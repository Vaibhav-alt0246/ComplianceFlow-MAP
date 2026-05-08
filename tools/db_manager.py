# Import sqlite3 and the CrewAI tool decorator.
# Create a @tool named 'Create_Compliance_Ticket'.
# It should take these string arguments: task, department, explainability_trigger, and confidence_score.
# It connects to the database, creates a table called 'tickets' if it doesn't exist,
# and inserts the arguments into the table with a current timestamp.
# Return a success message with the inserted task name.


import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from crewai.tools import tool

# Get the absolute path to the database directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "compliance_tickets.db")
TICKET_DB_PATH = DB_PATH


@tool
def create_compliance_ticket(
    task: str,
    department: str,
    explainability_trigger: str,
    confidence_score: str,
) -> str:
    """
    Create a compliance ticket in the database.

    Args:
        task: The task description.
        department: The department responsible.
        explainability_trigger: The explainability trigger for the task.
        confidence_score: The confidence score as a string.

    Returns:
        Success message with the inserted task name.
    """
    db_path = TICKET_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            department TEXT NOT NULL,
            explainability_trigger TEXT NOT NULL,
            confidence_score TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    timestamp = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO tickets (task, department, explainability_trigger, confidence_score, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task, department, explainability_trigger, confidence_score, timestamp),
    )

    conn.commit()
    conn.close()

    return f"Success: Ticket '{task}' created and inserted into database."


DB_PATH = "compliance_tickets.db"


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the database with the schema required by the IT Dispatcher task.
    Creates two tables: it_tickets and audit_trail.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS it_tickets (
            ticket_id TEXT PRIMARY KEY,
            map_id TEXT NOT NULL,
            action_title TEXT NOT NULL,
            action_description TEXT NOT NULL,
            target_department TEXT NOT NULL,
            priority TEXT NOT NULL,
            deadline TEXT,
            success_criteria TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            audit_id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL,
            map_id TEXT NOT NULL,
            clause_id TEXT NOT NULL,
            source_document TEXT NOT NULL,
            source_page INTEGER NOT NULL,
            source_section TEXT NOT NULL,
            verbatim_clause TEXT NOT NULL,
            auditor_verdict TEXT NOT NULL,
            auditor_confidence REAL NOT NULL,
            approver_name TEXT NOT NULL,
            approver_role TEXT NOT NULL,
            approval_timestamp TEXT NOT NULL,
            execution_timestamp TEXT NOT NULL,
            pipeline_version TEXT NOT NULL,
            immutable_flag INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (ticket_id) REFERENCES it_tickets(ticket_id)
        )
    """)

    conn.commit()
    conn.close()


def insert_ticket(
    map_id: str,
    action_title: str,
    action_description: str,
    target_department: str,
    priority: str,
    deadline: Optional[str],
    success_criteria: str,
    status: str = "OPEN",
    created_by: str = "SYSTEM/compliance_pipeline_v1",
) -> str:
    """
    Insert a new IT ticket. Returns the generated ticket_id (UUID).
    """
    ticket_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO it_tickets
        (ticket_id, map_id, action_title, action_description, target_department,
         priority, deadline, success_criteria, status, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            map_id,
            action_title,
            action_description,
            target_department,
            priority,
            deadline,
            success_criteria,
            status,
            created_at,
            created_by,
        ),
    )

    conn.commit()
    conn.close()
    return ticket_id


def insert_audit_trail_entry(
    ticket_id: str,
    map_id: str,
    clause_id: str,
    source_document: str,
    source_page: int,
    source_section: str,
    verbatim_clause: str,
    auditor_verdict: str,
    auditor_confidence: float,
    approver_name: str,
    approver_role: str,
    approval_timestamp: str,
    pipeline_version: str = "compliance_pipeline_v1",
) -> str:
    """
    Insert an immutable audit trail entry. Returns the generated audit_id (UUID).
    """
    audit_id = str(uuid.uuid4())
    execution_timestamp = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audit_trail
        (audit_id, ticket_id, map_id, clause_id, source_document, source_page,
         source_section, verbatim_clause, auditor_verdict, auditor_confidence,
         approver_name, approver_role, approval_timestamp, execution_timestamp,
         pipeline_version, immutable_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            ticket_id,
            map_id,
            clause_id,
            source_document,
            source_page,
            source_section,
            verbatim_clause,
            auditor_verdict,
            auditor_confidence,
            approver_name,
            approver_role,
            approval_timestamp,
            execution_timestamp,
            pipeline_version,
            1,  # immutable_flag
        ),
    )

    conn.commit()
    conn.close()
    return audit_id


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a ticket by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM it_tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_all_tickets() -> List[Dict[str, Any]]:
    """Retrieve all tickets."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM it_tickets ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_audit_trail(ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve audit trail entries. If ticket_id is provided, filter by that ticket.
    Otherwise return all entries ordered by execution_timestamp DESC.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if ticket_id:
        cursor.execute(
            "SELECT * FROM audit_trail WHERE ticket_id = ? ORDER BY execution_timestamp DESC",
            (ticket_id,),
        )
    else:
        cursor.execute("SELECT * FROM audit_trail ORDER BY execution_timestamp DESC")

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def generate_audit_report(ticket_ids: List[str]) -> str:
    """
    Generate a formatted plain-text audit trail report for the given ticket IDs.
    Suitable for PDF export from Streamlit.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("COMPLIANCE AUDIT TRAIL REPORT")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("=" * 80)
    lines.append("")

    for ticket_id in ticket_ids:
        ticket = get_ticket(ticket_id)
        if not ticket:
            continue

        lines.append(f"TICKET: {ticket_id}")
        lines.append(f"MAP ID: {ticket['map_id']}")
        lines.append(f"Action: {ticket['action_title']}")
        lines.append(f"Department: {ticket['target_department']}")
        lines.append(f"Status: {ticket['status']}")
        lines.append(f"Created: {ticket['created_at']}")
        lines.append("-" * 80)

        audit_entries = get_audit_trail(ticket_id)
        for entry in audit_entries:
            lines.append(f"AUDIT ID: {entry['audit_id']}")
            lines.append(f"Clause ID: {entry['clause_id']}")
            lines.append(f"Source: {entry['source_document']} (Page {entry['source_page']}, {entry['source_section']})")
            lines.append(f"Verbatim Clause: {entry['verbatim_clause']}")
            lines.append(f"Auditor Verdict: {entry['auditor_verdict']} (Confidence: {entry['auditor_confidence']})")
            lines.append(f"Approver: {entry['approver_name']} ({entry['approver_role']})")
            lines.append(f"Approval Timestamp: {entry['approval_timestamp']}")
            lines.append(f"Execution Timestamp: {entry['execution_timestamp']}")
            lines.append("-" * 80)

        lines.append("")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)
