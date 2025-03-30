import hashlib
from Helper.db_conn import db  # Import your database connection manager

def add_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Hash the password

    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            print(f"User '{username}' added successfully!")
        except Exception as e:
            print(f"Error: {e}")

def main():
    username = input("Enter username: ")
    password = input("Enter password: ")

    add_user(username, password)

if __name__ == "__main__":
    main()
