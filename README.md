# DB Sync Project

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

DB Sync is a Python-based project designed to synchronize data between PostgreSQL databases across different hosts using TCP socket communication. This tool is particularly useful for scenarios where data needs to be extracted from a source database on one host, transferred securely over a network, and inserted into a target database on another host, even in disconnected environments.

## Features

- **Database Connectivity**: Connects to PostgreSQL databases using the `psycopg2` library with configurable credentials via environment variables.
- **Data Synchronization**: Queries data from a source database table and transfers it to a target database through a client-server architecture.
- **Socket Communication**: Utilizes TCP sockets for reliable data transfer between hosts, handling large datasets by chunking data to prevent buffer overflow.
- **Logging**: Comprehensive logging to track operations, errors, and data transfers for debugging and monitoring.
- **Environment Configuration**: Supports environment variables for secure and flexible configuration of database and server settings.
- **Offline Deployment**: Guidance provided for packaging dependencies for disconnected environments.

## Project Structure

- **`db_sync.py`**: Core utility functions for PostgreSQL database operations including connection, querying, and data insertion.
- **`db_sync_client.py`**: Client script to connect to a source database, query data, and send it to a target server over TCP.
- **`db_sync_server.py`**: Server script to listen for incoming data over TCP and insert it into a target database.
- **`create-db.yaml`**: Ansible playbook for setting up a PostgreSQL server and database on Red Hat Linux systems.

## Requirements

- Python 3.6 or later (recommended: Python 3.8+)
- Dependencies:
  - `psycopg2-binary` for PostgreSQL database connectivity

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/crleekwc/db_sync.git
   cd db_sync
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   For a disconnected environment, follow the offline installation guide below.

## Usage

### Environment Variables

Configure the following environment variables for database and server settings (you can use a `.env` file with a library like `python-dotenv` or set them directly):

- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host address (source or target)
- `DB_PORT`: Database port (default: 5432)
- `SOURCE_DB_HOST`: Source database host for client
- `TARGET_DB_HOST`: Target database host for server
- `SERVER_HOST`: TCP server host address
- `SERVER_PORT`: TCP server port (default: 443)
- `TARGET_SERVER_HOST`: Target server host for client
- `TABLE_NAME`: Database table to sync
- `BUFFER_SIZE`: Socket buffer size for receiving data (default: 4096)

### Running the Server (on Host B)

Start the server to listen for incoming data and insert it into the target database:

```bash
python db_sync_server.py
```

### Running the Client (on Host C)

Run the client to connect to the source database, query data, and send it to the server:

```bash
python db_sync_client.py
```

### Ansible Playbook for Database Setup

Use the provided Ansible playbook to set up a PostgreSQL server and database on Red Hat Linux:

```bash
ansible-playbook create-db.yaml
```

## Offline Deployment for Disconnected Environments

To deploy this project in a disconnected environment without internet access:

1. **Generate `requirements.txt`**:
   ```bash
   pip freeze > requirements.txt
   ```
   Or manually create it with just `psycopg2-binary`.

2. **Download Dependencies**:
   ```bash
   pip download -r requirements.txt -d packages
   ```
   If you encounter errors for specific packages (e.g., development versions), edit `requirements.txt` to use stable versions or exclude unnecessary dependencies.

3. **Package Project Files**:
   Bundle project files and the `packages` directory into a ZIP file or transfer them directly.

4. **Install Offline**:
   In the disconnected environment, install dependencies from the local directory:
   ```bash
   pip install --no-index --find-links=packages -r requirements.txt
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue on GitHub.

## Contact

For questions or support, please contact the project maintainer via GitHub Issues.
