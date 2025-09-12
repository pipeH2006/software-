import mysql.connector

def login(username, password, conn=None):
    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT is_admin FROM usuarios WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            if user:
                return True, bool(user["is_admin"])
            else:
                return False, False
        finally:
            cursor.close()
    else:
        users = {
            "admin": "admin123",
            "user": "user123"
        }
        if username in users and users[username] == password:
            return True, username == "admin"
        return False, False

def logout():
    pass