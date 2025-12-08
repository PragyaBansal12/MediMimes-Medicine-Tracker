from chatbot.state import State
import sqlite3
from datetime import datetime, timedelta


# ------------------db_Query Node--------------------------
from datetime import datetime, timedelta

def db_query_node(state: dict, conn):
    """
    Safe, read-only DB query node for medication adherence.
    Works with your actual SQLite schema.
    
    INPUTS:
      state['query_type']  -> determined by Intent Classifier
      state['user_id']     -> authenticated user
    
    OUTPUTS:
      {
        "db_query_result": {...},  # structured data
        "route": "response_generation_node"
      }
    """

    query_type = state.get("query_type")
    user_id = state.get("user_id")

    cursor = conn.cursor()

    result_payload = {"query_type": query_type, "result": None}


    # =============================================
    # 1. LAST MISSED DOSE
    # =============================================
    if query_type == "last_missed_dose":

        cursor.execute("""
            SELECT 
                dl.id,
                m.pill_name,
                datetime(dl.scheduled_time),
                datetime(dl.timestamp),
                dl.status
            FROM medicines_doselog dl
            JOIN medicines_medication m
                ON dl.medication_id = m.id
            WHERE dl.user_id = ?
              AND dl.status = 'missed'
            ORDER BY dl.scheduled_time DESC
            LIMIT 1;
        """, (user_id,))

        row = cursor.fetchone()

        if row:
            result_payload["result"] = {
                "dose_id": row[0],
                "medication": row[1],
                "scheduled_time": row[2],
                "logged_time": row[3],
                "status": row[4]
            }


    # =============================================
    # 2. WEEKLY SUMMARY (taken/missed count)
    # =============================================
    elif query_type == "weekly_summary":

        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        cursor.execute("""
            SELECT status, COUNT(*)
            FROM medicines_doselog
            WHERE user_id = ?
              AND timestamp >= ?
            GROUP BY status;
        """, (user_id, seven_days_ago))

        rows = cursor.fetchall()

        summary = {"taken": 0, "missed": 0, "pending": 0}

        for status, count in rows:
            summary[status] = count

        result_payload["result"] = summary


    # =============================================
    # 3. DID I TAKE MY DOSE YESTERDAY?
    # =============================================
    elif query_type == "dose_taken_yesterday":

        yesterday = datetime.utcnow() - timedelta(days=1)

        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end   = yesterday.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

        cursor.execute("""
            SELECT 
                m.pill_name,
                dl.status,
                datetime(dl.scheduled_time),
                datetime(dl.timestamp)
            FROM medicines_doselog dl
            JOIN medicines_medication m
                ON dl.medication_id = m.id
            WHERE dl.user_id = ?
              AND dl.scheduled_time BETWEEN ? AND ?
            ORDER BY dl.scheduled_time DESC
            LIMIT 1;
        """, (user_id, start, end))

        row = cursor.fetchone()

        if row:
            result_payload["result"] = {
                "medication": row[0],
                "status": row[1],
                "scheduled_time": row[2],
                "logged_time": row[3]
            }


    # =============================================
    # 4. TODAY'S DOSES
    # =============================================
    elif query_type == "today_schedule":

        cursor.execute("""
            SELECT 
                m.pill_name,
                m.dosage,
                m.times,
                dl.status,
                datetime(dl.scheduled_time),
                datetime(dl.timestamp)
            FROM medicines_medication m
            LEFT JOIN medicines_doselog dl
                ON dl.medication_id = m.id
                AND date(dl.scheduled_time) = date('now')
                AND dl.user_id = ?
            WHERE m.user_id = ?
            ORDER BY dl.scheduled_time ASC;
        """, (user_id, user_id))

        rows = cursor.fetchall()

        result_payload["result"] = [
            {
                "medication": r[0],
                "dosage": r[1],
                "scheduled_times": r[2],  # may be JSON or CSV
                "status": r[3],
                "scheduled_time": r[4],
                "logged_time": r[5]
            }
            for r in rows
        ]


    # =============================================
    # 5. UPCOMING DOSES (NEXT 5)
    # =============================================
    elif query_type == "upcoming_doses":

        cursor.execute("""
            SELECT 
                m.pill_name,
                m.dosage,
                datetime(dl.scheduled_time),
                dl.status
            FROM medicines_doselog dl
            JOIN medicines_medication m
                ON dl.medication_id = m.id
            WHERE dl.user_id = ?
              AND dl.scheduled_time > datetime('now')
            ORDER BY dl.scheduled_time ASC
            LIMIT 5;
        """, (user_id,))

        rows = cursor.fetchall()

        result_payload["result"] = [
            {
                "medication": r[0],
                "dosage": r[1],
                "scheduled_time": r[2],
                "status": r[3]
            }
            for r in rows
        ]


    # =============================================
    # 6. RECENT HISTORY (LAST 10 EVENTS)
    # =============================================
    elif query_type == "recent_history":

        cursor.execute("""
            SELECT 
                m.pill_name,
                datetime(dl.scheduled_time),
                datetime(dl.timestamp),
                dl.status
            FROM medicines_doselog dl
            JOIN medicines_medication m
                ON dl.medication_id = m.id
            WHERE dl.user_id = ?
            ORDER BY dl.scheduled_time DESC
            LIMIT 10;
        """, (user_id,))

        rows = cursor.fetchall()

        result_payload["result"] = [
            {
                "medication": r[0],
                "scheduled_time": r[1],
                "logged_time": r[2],
                "status": r[3]
            }
            for r in rows
        ]


    # =============================================
    # 7. DEFAULT — NO MATCH
    # =============================================
    else:
        result_payload["result"] = None


    cursor.close()

    
    state["db_query_result"]= result_payload
    return state
    # state["route"] ="response_generation_node"
    
