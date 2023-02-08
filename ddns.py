import requests
import ipaddress
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
        raise ValueError("Invalid IP version")

    # Verify IP is valid
    try:
        ipaddress.ip_address(public_ip)
    except ValueError:
        raise ValueError("Invalid IP address")

    # Update or create DNS record
    cf = CloudFlare.CloudFlare(token=cloudflare_token)
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
    if len(dns_records) == 0:
        cf.zones.dns_records.post(zone["id"], data=dns_record)
        print(
            f"Successfully created DNS record for {subdomain}.{domain} with {ip_version} address {public_ip}")
    else:
        dns_record["id"] = dns_records[0]["id"]
        cf.zones.dns_records.put(zone["id"], dns_record["id"], data=dns_record)
        print(
            f"Successfully updated DNS record for {subdomain}.{domain} with {ip_version} address {public_ip}")


# Example usage
cloudflare_token = '***'
domain = 'example.com'
subdomain = 'www'

update_dns_record(cloudflare_token, domain, subdomain, 'ipv4')
