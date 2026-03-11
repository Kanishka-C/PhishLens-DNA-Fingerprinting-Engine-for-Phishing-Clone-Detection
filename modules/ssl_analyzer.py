import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any
import certifi

def analyze_ssl_certificate(url: str) -> Dict[str, Any]:
    """
    Connects to the server and retrieves SSL certificate details.
    """
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    
    # Handle ports if specified (e.g., example.com:8443)
    if ':' in hostname:
        hostname, port_str = hostname.split(':')
        port = int(port_str)
    else:
        port = 443

    # If it's not HTTPS, SSL analysis isn't applicable
    if parsed_url.scheme != 'https':
        return {
            "has_ssl": False,
            "error": "URL does not use HTTPS"
        }

    context = ssl.create_default_context()
    # We want to get the cert even if it's invalid so we can analyze it, but typical sockets will fail to connect.
    # To just read the cert, we can bypass verification temporarily for the socket connection.
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    cert_info = {
        "has_ssl": False,
        "valid_cert": False,
    }

    try:
        with socket.create_connection((hostname, port), timeout=5.0) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert(binary_form=True)
                
                # To get detailed readable info, we need the dict form. Re-wrap with verification to get parsed cert,
                # but catch verification errors
    except Exception as e:
        cert_info["error"] = f"Failed to connect for SSL reading: {str(e)}"
        return cert_info

    # Now let's try to get the parsed certificate dictionary
    # Use certifi to ensure we have a robust set of root CA certificates (especially on Windows)
    parsed_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with socket.create_connection((hostname, port), timeout=5.0) as sock:
            with parsed_context.wrap_socket(sock, server_hostname=hostname) as ssock:
                der_cert = ssock.getpeercert()
                
                issuer = dict(x[0] for x in der_cert.get('issuer', []))
                subject = dict(x[0] for x in der_cert.get('subject', []))
                
                cert_info["has_ssl"] = True
                cert_info["valid_cert"] = True
                cert_info["issuer"] = issuer.get('organizationName', issuer.get('commonName', 'Unknown'))
                cert_info["subject"] = subject.get('commonName', 'Unknown')
                cert_info["expires"] = der_cert.get('notAfter', 'Unknown')
                
                # Check expiration manually roughly
                if 'notAfter' in der_cert:
                    try:
                        expire_date = datetime.strptime(der_cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        cert_info["days_until_expiry"] = (expire_date - datetime.utcnow()).days
                    except Exception:
                        pass

    except ssl.SSLCertVerificationError as e:
        cert_info["has_ssl"] = True
        cert_info["valid_cert"] = False
        cert_info["error"] = f"Certificate verification failed: {e.verify_message}"
    except Exception as e:
        cert_info["error"] = str(e)

    return cert_info
