  CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY,
      first_name TEXT,
      last_name TEXT,
      email TEXT,
      organization TEXT,
      role TEXT
  );

  CREATE TABLE IF NOT EXISTS tenants (
      id SERIAL PRIMARY KEY,
      name TEXT,
      admission_date DATE,
      discharge_date DATE,
      waitlist BOOLEAN
  );

INSERT INTO users (first_name, last_name, email, organization, role) VALUES ('John', 'Doe', 'john.doe@example.com', 'Example Inc.', 'admin');
INSERT INTO tenants (name, admission_date, discharge_date, waitlist) VALUES ('Tenant 1', '2025-01-01', '2025-01-01', false);
