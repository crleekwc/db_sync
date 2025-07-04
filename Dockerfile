# Use UBI9 as the base image
FROM registry.access.redhat.com/ubi9/ubi:latest

# Set working directory
WORKDIR /db_sync

# Install necessary packages
RUN dnf install -y python3.12 python3.12-pip git postgresql-devel openssl gcc pkg-config cmake && \
    # Clone the repository
    git clone https://github.com/crleekwc/db_sync.git . && \
    # Install Python dependencies 
    pip3.12 install --no-cache-dir -r requirements.txt && \
    # Create directory for certificates
    mkdir -p /db_sync/certs && \
    dnf clean all

# Set environment variables for the application
# Source database connection settings
ENV SOURCE_DB_NAME=your_db_name
ENV SOURCE_DB_USER=your_db_user
ENV SOURCE_DB_PASSWORD=your_db_password
ENV SOURCE_DB_HOST=localhost
ENV SOURCE_DB_PORT=5432

# Target database connection settings
ENV TARGET_DB_NAME=your_target_db_name
ENV TARGET_DB_USER=your_target_db_user
ENV TARGET_DB_PASSWORD=your_target_db_password
ENV TARGET_DB_HOST=localhost
ENV TARGET_DB_PORT=5432

# TCP server settings
ENV SERVER_HOST=localhost
ENV SERVER_PORT=443
ENV TARGET_SERVER_HOST=localhost

# Table to sync
ENV TABLE_NAME=your_table_name

# Socket buffer size
ENV BUFFER_SIZE=1024

# Sync interval for client (in seconds)
ENV SYNC_INTERVAL_SECONDS=60

# TLS certificate and key files
ENV SERVER_CERT_FILE=/db_sync/certs/server.crt
ENV SERVER_KEY_FILE=/db_sync/certs/server.key

# Run mode (client or server)
ENV RUN_MODE=client


# Expose port 443 for server mode
EXPOSE 443

# Command to run either client or server based on RUN_MODE environment variable
CMD if [ "$RUN_MODE" = "client" ]; then \
        python3 db_sync/db_sync_client.py; \
    else \
        python3 db_sync/db_sync_server.py; \
    fi
