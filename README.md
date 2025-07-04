# DB Sync Project

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

DB Sync is a Python-based project designed to synchronize data between PostgreSQL databases across different hosts using TCP socket communication. This tool is particularly useful for scenarios where data needs to be extracted from a source database on one host, transferred securely over a network, and inserted into a target database on another host, even in disconnected environments. It includes advanced features such as schema application before data insertion and continuous monitoring of the source database for real-time synchronization of new data with persistent tracking between script executions.

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

**Source Database (Client):**
- `SOURCE_DB_NAME`: Source database name
- `SOURCE_DB_USER`: Source database username
- `SOURCE_DB_PASSWORD`: Source database password
- `SOURCE_DB_HOST`: Source database host address
- `SOURCE_DB_PORT`: Source database port (default: 5432)

**Target Database (Server):**
- `TARGET_DB_NAME`: Target database name
- `TARGET_DB_USER`: Target database username
- `TARGET_DB_PASSWORD`: Target database password
- `TARGET_DB_HOST`: Target database host address
- `TARGET_DB_PORT`: Target database port (default: 5432)

**Server Settings:**
- `SERVER_HOST`: TCP server host address
- `SERVER_PORT`: TCP server port (default: 443)
- `TARGET_SERVER_HOST`: Target server host for client connection
- `SERVER_CERT_FILE`: Path to server SSL certificate file (default: "server.crt")
- `SERVER_KEY_FILE`: Path to server SSL key file (default: "server.key")

**Other:**
- `TABLE_NAME`: Database table to sync
- `BUFFER_SIZE`: Socket buffer size for receiving data (default: 4096)
- `SYNC_INTERVAL_SECONDS`: Interval in seconds for continuous synchronization (default: 60)

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

## Building the Docker Container Image

To build a Docker container image for the DB Sync project, use the provided `Dockerfile`. This image can be used to deploy either the server or the client components.

1. **Navigate to the Project Directory**:
   Ensure you are in the root directory of the project where the `Dockerfile` is located.

2. **Build the Image**:
   Run the following command to build the Docker image. Replace `db-sync-image` with any name you prefer for the image.
   ```bash
   docker build -t db-sync-image .
   ```

3. **Verify the Image**:
   After the build process completes, you can verify that the image was created successfully by listing your Docker images:
   ```bash
   docker images
   ```

## Deploying with Docker

You can deploy the DB Sync server or client using the Docker image you built. Below are example commands for deploying both components, including how to set up volume mounts for certificates and pickle files.

### Deploying the Server

To deploy the server component, which listens for incoming data and inserts it into the target database, use the following command:

```bash
docker run -d \
  --name db-sync-server \
  -e TARGET_DB_NAME="your_target_db_name" \
  -e TARGET_DB_USER="your_target_db_user" \
  -e TARGET_DB_PASSWORD="your_target_db_password" \
  -e TARGET_DB_HOST="your_target_db_host" \
  -e TARGET_DB_PORT="5432" \
  -e SERVER_HOST="0.0.0.0" \
  -e SERVER_PORT="443" \
  -e SERVER_CERT_FILE="/certs/server.crt" \
  -e SERVER_KEY_FILE="/certs/server.key" \
  -v /path/to/certificates:/certs:ro \
  -v /path/to/server_data:/data \
  db-sync-image \
  python db_sync_server.py
```

- **Environment Variables**: Set the target database credentials and server settings as environment variables.
- **Volume Mount for Certificates**: The `-v /path/to/certificates:/certs:ro` option mounts a directory containing the server certificate and key files (`server.crt` and `server.key`) into the container at `/certs` in read-only mode.
- **Volume Mount for Pickle File**: The `-v /path/to/server_data:/data` option mounts a directory to store the pickle file for persistent tracking between script executions.

### Deploying the Client

To deploy the client component, which connects to the source database and sends data to the server, use the following command:

```bash
docker run -d \
  --name db-sync-client \
  -e SOURCE_DB_NAME="your_source_db_name" \
  -e SOURCE_DB_USER="your_source_db_user" \
  -e SOURCE_DB_PASSWORD="your_source_db_password" \
  -e SOURCE_DB_HOST="your_source_db_host" \
  -e SOURCE_DB_PORT="5432" \
  -e TARGET_SERVER_HOST="your_target_server_host" \
  -e SERVER_PORT="443" \
  -e BUFFER_SIZE="4096" \
  -e SYNC_INTERVAL_SECONDS="60" \
  -e TABLE_NAME="your_table_name" \
  -v /path/to/client_data:/data \
  db-sync-image \
  python db_sync_client.py
```

- **Environment Variables**: Set the source database credentials and server connection details as environment variables.
- **Volume Mount for Pickle File**: The `-v /path/to/client_data:/data` option mounts a directory to store the pickle file for persistent tracking of synchronized data.

**Note**: Replace `/path/to/certificates`, `/path/to/server_data`, and `/path/to/client_data` with the actual paths on your host machine where you want to store the certificates and data files. Ensure that the paths inside the container (`/certs` and `/data`) match the expected paths in your environment variable configurations if they differ from the defaults.

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
