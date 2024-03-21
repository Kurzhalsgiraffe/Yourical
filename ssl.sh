#!/bin/bash

mkdir ssl
cd ssl
openssl genpkey -algorithm RSA -out privatekey.key
openssl req -new -key privatekey.key -out csr.pem
openssl req -x509 -sha256 -days 365 -key privatekey.key -in csr.pem -out certificate.crt