import requests
import ipaddress
import socket
import CloudFlare


def update_dns_record(cloudflare_token, domain, subdomain, ip_version):
    # Get public IP
    if ip_version == "ipv4":
        response = requests.get("https://api.ipify.org")
        public_ip = response.text
    elif ip_version == "ipv6":
        response = requests.get("https://api6.ipify.org")
        public_ip = response.text
    else:
        raise ValueError("Invalid IP version: %s" % ip_version)

    # Verify IP is valid
    try:
        ipaddress.ip_address(public_ip)
    except ValueError:
        raise ValueError("Invalid IP address: %s" % public_ip)

    # Query subdomain.domain
    try:
        # Use local DNS to query subdomain.domain
        dns_record = socket.gethostbyname(subdomain + '.' + domain)
    except socket.gaierror as e:
        raise ValueError("DNS lookup failed: %s" % e)

    # Update DNS record if necessary
    if dns_record == public_ip:
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
subdomain = 'www'

update_dns_record(cloudflare_token, domain, subdomain, 'ipv4')
