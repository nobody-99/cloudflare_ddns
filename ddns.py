import time
import requests
import ipaddress
import CloudFlare


def update_dns_record(cloudflare_token, domain, subdomain, ip_version):
    # Get public IP
    if ip_version == 4:
        ip_fetch_urls = ['https://ipv4.icanhazip.com',
                         'https://ipv4.wtfismyip.com/text']
    elif ip_version == 6:
        ip_fetch_urls = ['https://ipv6.icanhazip.com',
                         'https://ipv6.wtfismyip.com/text']
    else:
        return "Invalid IP version: %s" % ip_version

    public_ip = None
    for url in ip_fetch_urls:
        try:
            public_ip = requests.get(url, timeout=5).text.strip()
            ipaddress.ip_address(public_ip)
            break
        except (requests.exceptions.RequestException, ValueError):
            pass

    if public_ip is None:
        return "Failed to fetch public IP address"

    # Create Cloudflare API client
    cf = CloudFlare.CloudFlare(token=cloudflare_token)

    # Query subdomain.domain
    zone = cf.zones.get(params={"name": domain})
    if len(zone) == 0:
        return "No matching domain found"
    zone = zone[0]
    dns_record_type = "A" if ip_version == 4 else "AAAA"
    dns_records = cf.zones.dns_records.get(
        zone["id"], params={"name": (subdomain + '.' + domain), "type": dns_record_type})

    # Create or update DNS record
    if len(dns_records) == 0:
        # Create new DNS record
        dns_record = {
            "type": dns_record_type,
            "name": subdomain,
            "content": public_ip,
            "ttl": 1,
            "proxied": False
        }
        cf.zones.dns_records.post(zone["id"], data=dns_record)
        return "DNS record created: %s.%s -> %s" % (subdomain, domain, public_ip)
    elif len(dns_records) == 1:
        # Update existing DNS record if necessary
        dns_record = dns_records[0]
        if dns_record["content"] != public_ip:
            dns_record["content"] = public_ip
            cf.zones.dns_records.put(
                zone["id"], dns_record["id"], data=dns_record)
            return "DNS record updated: %s.%s -> %s" % (subdomain, domain, public_ip)
        else:
            return "DNS record is up to date: %s.%s -> %s" % (subdomain, domain, public_ip)
    else:
        # Delete duplicate DNS records
        for i in range(1, len(dns_records)):
            dns_record_id = dns_records[i]["id"]
            cf.zones.dns_records.delete(zone["id"], dns_record_id)
        # Update remaining DNS record if necessary
        dns_record = dns_records[0]
        if dns_record["content"] != public_ip:
            dns_record["content"] = public_ip
            cf.zones.dns_records.put(
                zone["id"], dns_record["id"], data=dns_record)
            return "DNS record updated: %s.%s -> %s, and duplicate DNS records deleted" % (subdomain, domain, public_ip)
        else:
            return "DNS record is up to date: %s.%s -> %s, and duplicate DNS records deleted" % (subdomain, domain, public_ip)


# Example usage
cloudflare_token = '***'
domain = 'example.com'


print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
print(update_dns_record(cloudflare_token, domain, 'ipv4', 4))
print(update_dns_record(cloudflare_token, domain, 'ipv6', 6))
print()
