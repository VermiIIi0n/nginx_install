#!/bin/bash

# Function to display error messages and exit
error_exit() {
    echo "Error: $1" >&2
    rm *.key *.pem *.srl *.csr 2>/dev/null
    exit 1
}

# Generate a CA certificate
openssl genrsa -out sample_ca.key 4096 || error_exit "Failed to generate CA private key"
openssl req \
    -new -x509 \
    -days 365 \
    -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=ca.sample.com" \
    -key sample_ca.key \
    -out sample_ca.pem || error_exit "Failed to generate CA certificate"

# Generate a TLS certificate signing request (CSR) with wildcard domain
openssl genrsa -out sample.key 4096 || error_exit "Failed to generate TLS private key"
openssl req -new \
    -keyout sample.key -out sample.csr \
    -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=sample.com" \
    -reqexts SAN \
    -nodes \
    -config <(cat /etc/ssl/openssl.cnf \
        <(printf "\n[SAN]\nsubjectAltName=DNS:sample.com,DNS:*.sample.com")) ||
    error_exit "Failed to generate TLS CSR"

# Sign the TLS certificate with the CA
openssl x509 -req -in sample.csr -CA sample_ca.pem -CAkey sample_ca.key -CAcreateserial -out sample.pem -days 365 || error_exit "Failed to sign TLS certificate"

# Generate a Diffie-Hellman key
openssl dhparam -out dhparam.pem 2048 || error_exit "Failed to generate Diffie-Hellman key"

# Add the CA to Ubuntu trusted CAs
sudo cp -f sample_ca.pem /usr/local/share/ca-certificates/sample_ca.crt || error_exit "Failed to copy CA certificate to trusted CAs"
sudo update-ca-certificates --fresh || error_exit "Failed to update trusted CAs"

# # Copy TLS certificate and keys to designated directory
sudo mkdir -p /usr/local/tls || error_exit "Failed to create directory for TLS certificates"
sudo chmod 660 *.key *pem || error_exit "Failed to change permissions of TLS certificate and keys"
sudo chown www-data:www-data *.key *pem || error_exit "Failed to change ownership of TLS certificate and keys"
sudo cp -f *.key *.pem /usr/local/tls/ || error_exit "Failed to copy TLS certificate and keys"

echo "TLS certificate issued successfully!"
