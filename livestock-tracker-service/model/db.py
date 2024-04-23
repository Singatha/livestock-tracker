import psycopg

# Connect to an existing database
with psycopg.connect("host=psql-livestock-tracker-service-db dbname=livestockTrackerDB user=postgres password=example") as conn:

    # Open a cursor to perform database operations
    with conn.cursor() as cur:

        # Execute a command: this creates a new table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS livestock(
                livestock_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                livestock_type VARCHAR(255) NOT NULL,
                health_status VARCHAR(255) NOT NULL,
                group_name VARCHAR(255) NOT NULL,
                age INT,
                expected_growth,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

        # Make the changes to the database persistent
        conn.commit()
