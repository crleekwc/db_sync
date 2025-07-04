import psycopg2
from psycopg2 import Error
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_to_postgres(dbname: str = None, user: str = None, password: str = None, host: str = "localhost", port: str = "5432") -> Optional[psycopg2.extensions.connection]:
    """
    Establish a connection to a PostgreSQL database using environment variables as defaults.
    
    Parameters:
    - dbname (str): The name of the database to connect to. Defaults to env var DB_NAME.
    - user (str): The username for the database. Defaults to env var DB_USER.
    - password (str): The password for the database. Defaults to env var DB_PASSWORD.
    - host (str): The host address of the database server. Defaults to env var DB_HOST or "localhost".
    - port (str): The port number of the database server. Defaults to env var DB_PORT or "5432".
    
    Returns:
    - connection: A connection object to the PostgreSQL database, or None if connection fails.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=dbname or os.getenv("DB_NAME"),
            user=user or os.getenv("DB_USER"),
            password=password or os.getenv("DB_PASSWORD"),
            host=host if host != "localhost" else os.getenv("DB_HOST", "localhost"),
            port=port if port != "5432" else os.getenv("DB_PORT", "5432")
        )
        logger.info("Successfully connected to the PostgreSQL database.")
        return connection
    except Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return None

def query_table(connection: psycopg2.extensions.connection, table_name: str) -> list:
    """
    Query all information from a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query.
    
    Returns:
    - list: A list of tuples containing the rows of data from the table.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Successfully retrieved {len(rows)} rows from table {table_name}.")
        return rows
    except Error as e:
        logger.error(f"Error querying table {table_name}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()

def query_new_rows(connection: psycopg2.extensions.connection, table_name: str, column_name: str = "id", last_value: Optional[int] = None, timestamp_column: Optional[str] = None, time_duration: Optional[str] = None) -> tuple[list, Optional[int]]:
    """
    Query newly added or updated rows from a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to query.
    - column_name (str): The column to use for identifying new rows (default: 'id').
    - last_value: The last known value of the column_name to compare against. 
                  If None and no timestamp filter is provided, returns all rows.
    - timestamp_column (str): The column to use for identifying updated rows based on timestamp.
    - time_duration (str): The duration in PostgreSQL interval format (e.g., '1 hour', '30 minutes')
                           to look back for updated rows. Requires timestamp_column to be set.
    
    Returns:
    - tuple: (list of tuples containing the new or updated rows of data from the table,
              maximum value of the column_name from the queried rows, to be used as last_value in the next call).
    """
    cursor = None
    try:
        cursor = connection.cursor()
        conditions = []
        params = []
        
        if last_value is not None:
            conditions.append(f"{column_name} > %s")
            params.append(last_value)
            
        if timestamp_column and time_duration:
            conditions.append(f"{timestamp_column} >= NOW() - INTERVAL %s")
            params.append(time_duration)
        
        if conditions:
            query = f"SELECT * FROM {table_name} WHERE {' OR '.join(conditions)} ORDER BY {column_name};"
            cursor.execute(query, params)
        else:
            query = f"SELECT * FROM {table_name} ORDER BY {column_name};"
            cursor.execute(query)
            
        rows = cursor.fetchall()
        max_value = None
        if rows and len(rows) > 0:
            # Assuming the column_name is in the first position if it's 'id', adjust if needed
            col_index = 0  # Adjust based on table structure if necessary
            max_value = max(row[col_index] for row in rows)
            logger.info(f"Successfully retrieved {len(rows)} new or updated rows from table {table_name}.")
        else:
            logger.info(f"No new or updated rows found in table {table_name}.")
        return rows, max_value
    except Error as e:
        logger.error(f"Error querying new or updated rows from table {table_name}: {e}")
        return [], None
    finally:
        if cursor:
            cursor.close()

def insert_row(connection: psycopg2.extensions.connection, table_name: str, row_data: dict) -> bool:
    """
    Insert a row of data into a specified table in the PostgreSQL database.
    
    Parameters:
    - connection: A connection object to the PostgreSQL database.
    - table_name (str): The name of the table to insert data into.
    - row_data (dict): A dictionary where keys are column names and values are the data to insert.
    
    Returns:
    - bool: True if the insertion was successful, False otherwise.
    """
    cursor = None
    try:
        cursor = connection.cursor()
        columns = ', '.join(row_data.keys())
        placeholders = ', '.join(['%s'] * len(row_data))
        values = tuple(row_data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Successfully inserted row into table {table_name}.")
        return True
    except Error as e:
        logger.error(f"Error inserting row into table {table_name}: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

# Example usage
if __name__ == "__main__":
    conn = connect_to_postgres()
    if conn:
        try:
            # Query a table
            results = query_table(conn, "your_table_name")
            for row in results:
                logger.info(f"Row data: {row}")
            
            # Query new rows
            new_rows, last_id = query_new_rows(conn, "your_table_name", "id", None)
            for row in new_rows:
                logger.info(f"New row: {row}")
            logger.info(f"Last ID queried: {last_id}")
            
            # Query new or updated rows within the last hour
            updated_rows, last_id_updated = query_new_rows(
                conn, 
                "your_table_name", 
                "id", 
                last_id, 
                timestamp_column="updated_at", 
                time_duration="1 hour"
            )
            for row in updated_rows:
                logger.info(f"New or updated row within last hour: {row}")
            logger.info(f"Last ID queried for updates: {last_id_updated}")
            
            # Insert a new row
            sample_data = {
                "column1": "value1",
                "column2": "value2"
                # Add more columns and values as needed
            }
            insert_success = insert_row(conn, "your_table_name", sample_data)
            if insert_success:
                logger.info("Row insertion was successful.")
            else:
                logger.warning("Row insertion failed.")
        finally:
            conn.close()
            logger.info("Connection closed.")
    else:
        logger.error("Failed to establish database connection.")
