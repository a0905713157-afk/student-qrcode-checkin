# pyright: reportMissingImports=false
from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import datetime
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

app = Flask(__name__)
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'your_password'),
        database=os.getenv('DB_NAME', 'school_checkin')
    )

@app.route('/')
def home():
    # 渲染首頁 (前端表單)
    return render_template('index.html')

@app.route('/api/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    student_id = data.get('student_id')
    student_name = data.get('student_name')

    if not student_id or not student_name:
        return jsonify({"success": False, "message": "請填寫完整學號與姓名！"}), 400

    now = datetime.datetime.now()
    today_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 嘗試寫入報到紀錄
        insert_query = """
            INSERT INTO checkins (student_id, student_name, checkin_date, checkin_time)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (student_id, student_name, today_date, current_time))
        conn.commit()

        count_query = "SELECT COUNT(*) AS total FROM checkins WHERE student_id = %s"
        cursor.execute(count_query, (student_id,))
        count_result = cursor.fetchone()
        total_count = count_result['total'] if count_result else 1

        return jsonify({
            "success": True,
            "message": f"報到成功！歡迎 {student_name}",
            "total_checkins": total_count,
            "date": today_date,
            "time": current_time
        }), 200

    except mysql.connector.Error as err:
        # 捕捉 1062 錯誤碼：代表違反 UNIQUE 約束 (當日重複報到)
        if err.errno == 1062:
            return jsonify({
                "success": False,
                "message": "您今日已經完成報到了，請勿重複送出！"
            }), 400
        else:
            print(f"Database Error: {err}")
            return jsonify({"success": False, "message": "資料庫處理錯誤！"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    # 開啟開發者模式運行
    app.run(debug=True, port=5000)