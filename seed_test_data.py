import psycopg2

conn = psycopg2.connect(
    dbname="test_db",
    user="test_user",
    password="test_password",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

cur.execute("INSERT INTO users (first_name, last_name, email, organization, role) VALUES ('John', 'Doe', 'john.doe@example.com', 'Example Inc.', 'admin')"  )
cur.execute("INSERT INTO tenants (name, admission_date, discharge_date, waitlist) VALUES ('Tenant 1', '2025-01-01', '2025-01-01', false)")

conn.commit()

cur.close()
conn.close()