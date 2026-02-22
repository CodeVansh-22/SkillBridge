import os
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", ""),
        database=os.getenv("DB_NAME", "skillbridge_db")
    )

def create_user(name, email, password, education, city):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_pw = generate_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, education, city) VALUES (%s, %s, %s, %s, %s)",
            (name, email, hashed_pw, education, city)
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        cursor.close()
        conn.close()

def verify_user_login(email, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return user
    return None

def save_extracted_skills_to_db(user_id, skills_dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for skill_name, proficiency in skills_dict.items():
            cursor.execute("INSERT IGNORE INTO skills (name) VALUES (%s)", (skill_name,))
            cursor.execute("SELECT id FROM skills WHERE name = %s", (skill_name,))
            skill_record = cursor.fetchone()
            
            if skill_record:
                skill_id = skill_record[0]
                insert_query = """
                    INSERT INTO user_skills (user_id, skill_id, proficiency) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE proficiency = VALUES(proficiency)
                """
                cursor.execute(insert_query, (user_id, skill_id, proficiency))

        conn.commit()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    stats = {"total_users": 0, "top_skill": "None", "total_skills_logged": 0}
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM users")
        stats["total_users"] = cursor.fetchone()["total"]
        
        cursor.execute("""
            SELECT s.name, COUNT(us.skill_id) as frequency 
            FROM user_skills us 
            JOIN skills s ON us.skill_id = s.id 
            GROUP BY s.name 
            ORDER BY frequency DESC 
            LIMIT 1
        """)
        top_skill_row = cursor.fetchone()
        if top_skill_row:
            stats["top_skill"] = top_skill_row["name"]
            
        cursor.execute("SELECT COUNT(*) as total FROM user_skills")
        stats["total_skills_logged"] = cursor.fetchone()["total"]
        
    except Exception as e:
        print("Admin Stat Error:", e)
    finally:
        cursor.close()
        conn.close()
        
    return stats