import requests
import ipaddress
import socket
import CloudFlare
import time


def update_dns_record(cloudflare_token, domain, subdomain, ip_version):
    # Get public IP
    if ip_version == "ipv4":
        public_ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    elif ip_version == "ipv6":
        public_ip = requests.get('https://ipv6.icanhazip.com').text.strip()
    else:
        raise ValueError("Invalid IP version: %s" % ip_version)

    # Verify IP is valid
    try:
        ipaddress.ip_address(public_ip)
    except ValueError:
        raise ValueError("Invalid IP address: %s" % public_ip)

    # Query subdomain.domain
    try:
        # Use getaddrinfo to query subdomain.domain for both IPv4 and IPv6 addresses
        dns_query_result = [ai[4][0]
                            for ai in socket.getaddrinfo(subdomain + '.' + domain, None)]
    except socket.gaierror as e:
        raise ValueError("DNS lookup failed: %s" % e)

    # Check if public IP is in DNS records
    if public_ip in dns_query_result:
        print("DNS record is already up to date")
    else:
        # Create Cloudflare API client
        cf = CloudFlare.CloudFlare(token=cloudflare_token)

        # Find DNS record
        zone = cf.zones.get(params={"name": domain})
        if len(zone) == 0:
            raise ValueError("No matching domain found")
        zone = zone[0]
        dns_record = {
            "type": "A" if ip_version == "ipv4" else "AAAA",
            "name": subdomain,
            "content": public_ip,
            "ttl": 1,
            "proxied": False
        }
        dns_records = cf.zones.dns_records.get(
            zone["id"], params={"name": subdomain, "type": dns_record["type"]})

        # Update or create DNS record
        if len(dns_records) == 0:
            cf.zones.dns_records.post(zone["id"], data=dns_record)
            print(
                f"Successfully created DNS record for {subdomain}.{domain} with {ip_version} address {public_ip}")
        elif len(dns_records) == 1:
            dns_record["id"] = dns_records[0]["id"]
            cf.zones.dns_records.put(
                zone["id"], dns_record["id"], data=dns_record)
            print(
                f"Successfully updated DNS record for {subdomain}.{domain} with {ip_version} address {public_ip}")
        else:
            raise ValueError("Multiple DNS records found: %s.%s" %
                             (subdomain, domain))


# Example usage
cloudflare_token = '***'
domain = 'example.com'


print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
subdomain = 'ipv4'
update_dns_record(cloudflare_token, domain, subdomain, 'ipv4')
subdomain = 'ipv6'
update_dns_record(cloudflare_token, domain, subdomain, 'ipv6')
print()
