CERT_IP=127.0.0.1
SERVER_HOST=localhost

echo "subjectAltName=IP:$CERT_IP" > /tmp/san.cnf && \
    openssl req -x509 -newkey rsa:4096 -keyout /db_sync/certs/server.key -out /db_sync/certs/server.crt -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=$SERVER_HOST" -config /tmp/san.cnf && \
    rm /tmp/san.cnf