import asyncio
import aiohttp
import re
import json
from datetime import datetime
import socket
import dns.resolver
from ipinfo import getHandler
import requests

class IPAnalyzer:
    def __init__(self, ipinfo_token=None):
        self.ipinfo_token = ipinfo_token
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def validate_ip(self, ip):
        """Validate IP address format."""
        # IPv4 regex
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        # IPv6 regex (simplified)
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$'
        
        if re.match(ipv4_pattern, ip):
            return 'IPv4'
        elif re.match(ipv6_pattern, ip):
            return 'IPv6'
        else:
            return None
    
    def resolve_domain_to_ip(self, domain):
        """Resolve domain name to IP addresses."""
        try:
            # Get both A and AAAA records
            a_records = []
            aaaa_records = []
            
            try:
                answers = dns.resolver.resolve(domain, 'A')
                a_records = [str(rdata) for rdata in answers]
            except:
                pass
            
            try:
                answers = dns.resolver.resolve(domain, 'AAAA')
                aaaa_records = [str(rdata) for rdata in answers]
            except:
                pass
            
            return {
                'domain': domain,
                'ipv4_addresses': a_records,
                'ipv6_addresses': aaaa_records
            }
        except Exception as e:
            return {'error': f'DNS resolution failed: {str(e)}'}
    
    async def get_ipinfo_details(self, ip):
        """Get detailed IP information using ipinfo.io."""
        try:
            if self.ipinfo_token:
                handler = getHandler(self.ipinfo_token)
                details = handler.getDetails(ip)
                return {
                    'ip': details.ip,
                    'city': details.city,
                    'region': details.region,
                    'country': details.country,
                    'location': details.loc,
                    'org': details.org,
                    'postal': details.postal,
                    'timezone': details.timezone,
                    'hostname': details.hostname,
                    'asn': details.org,
                    'company': details.org
                }
            else:
                # Free tier without token
                url = f"https://ipinfo.io/{ip}/json"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return {'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'error': f'IPInfo lookup failed: {str(e)}'}
    
    async def get_virustotal_info(self, ip, vt_api_key=None):
        """Get VirusTotal information about the IP."""
        if not vt_api_key:
            return {'error': 'VirusTotal API key required'}
        
        try:
            url = f"https://www.virustotal.com/vtapi/v2/ip-address/report"
            params = {
                'apikey': vt_api_key,
                'ip': ip
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'scan_date': data.get('scan_date'),
                        'positives': data.get('positives', 0),
                        'total': data.get('total', 0),
                        'permalink': data.get('permalink'),
                        'detected_urls': data.get('detected_urls', []),
                        'detected_downloaded_samples': data.get('detected_downloaded_samples', [])
                    }
                else:
                    return {'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'error': f'VirusTotal lookup failed: {str(e)}'}
    
    async def get_shodan_info(self, ip, shodan_api_key=None):
        """Get Shodan information about the IP."""
        if not shodan_api_key:
            return {'error': 'Shodan API key required'}
        
        try:
            url = f"https://api.shodan.io/shodan/host/{ip}"
            params = {'key': shodan_api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'country_name': data.get('country_name'),
                        'city': data.get('city'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'org': data.get('org'),
                        'hostnames': data.get('hostnames', []),
                        'domains': data.get('domains', []),
                        'ports': data.get('ports', []),
                        'vulns': data.get('vulns', []),
                        'last_update': data.get('last_update')
                    }
                else:
                    return {'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'error': f'Shodan lookup failed: {str(e)}'}
    
    async def check_open_ports(self, ip, ports=None):
        """Check common open ports on the IP."""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443]
        
        open_ports = []
        
        async def check_port(port):
            try:
                future = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(future, timeout=3)
                writer.close()
                await writer.wait_closed()
                return port
            except:
                return None
        
        tasks = [check_port(port) for port in ports]
        results = await asyncio.gather(*tasks)
        
        open_ports = [port for port in results if port is not None]
        return open_ports
    
    async def get_reverse_dns(self, ip):
        """Get reverse DNS lookup for the IP."""
        try:
            hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(ip)
            return {
                'hostname': hostname,
                'aliases': aliaslist,
                'ip_addresses': ipaddrlist
            }
        except socket.herror:
            return {'error': 'No reverse DNS record found'}
        except Exception as e:
            return {'error': f'Reverse DNS failed: {str(e)}'}
    
    async def analyze_ip(self, ip, vt_api_key=None, shodan_api_key=None, check_ports=False):
        """Perform comprehensive IP analysis."""
        ip_type = self.validate_ip(ip)
        if not ip_type:
            return {'error': 'Invalid IP address format'}
        
        print(f"Analyzing {ip_type} address: {ip}")
        
        # Run all analyses concurrently
        tasks = [
            self.get_ipinfo_details(ip),
            self.get_reverse_dns(ip)
        ]
        
        if check_ports:
            tasks.append(self.check_open_ports(ip))
        
        if vt_api_key:
            tasks.append(self.get_virustotal_info(ip, vt_api_key))
        
        if shodan_api_key:
            tasks.append(self.get_shodan_info(ip, shodan_api_key))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Parse results
        ipinfo_data = results[0] if not isinstance(results[0], Exception) else {'error': str(results[0])}
        reverse_dns = results[1] if not isinstance(results[1], Exception) else {'error': str(results[1])}
        
        analysis = {
            'ip': ip,
            'ip_type': ip_type,
            'analysis_date': datetime.now().isoformat(),
            'ipinfo': ipinfo_data,
            'reverse_dns': reverse_dns
        }
        
        if check_ports and len(results) > 2:
            analysis['open_ports'] = results[2] if not isinstance(results[2], Exception) else []
        
        # Add optional services
        result_index = 3 if check_ports else 2
        if vt_api_key and len(results) > result_index:
            analysis['virustotal'] = results[result_index] if not isinstance(results[result_index], Exception) else {'error': str(results[result_index])}
            result_index += 1
        
        if shodan_api_key and len(results) > result_index:
            analysis['shodan'] = results[result_index] if not isinstance(results[result_index], Exception) else {'error': str(results[result_index])}
        
        return analysis
    
    def format_results(self, results):
        """Format IP analysis results for display."""
        if 'error' in results:
            return f"Error: {results['error']}"
        
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"IP ADDRESS ANALYSIS RESULTS")
        output.append(f"{'='*60}")
        output.append(f"IP Address: {results['ip']} ({results['ip_type']})")
        output.append(f"Analysis Date: {results['analysis_date']}")
        
        # IPInfo Details
        output.append(f"\n{'─'*40}")
        output.append("LOCATION & ISP INFORMATION")
        output.append(f"{'─'*40}")
        
        ipinfo = results.get('ipinfo', {})
        if 'error' in ipinfo:
            output.append(f"IPInfo Error: {ipinfo['error']}")
        else:
            output.append(f"IP: {ipinfo.get('ip', 'Unknown')}")
            output.append(f"Location: {ipinfo.get('city', 'Unknown')}, {ipinfo.get('region', 'Unknown')}, {ipinfo.get('country', 'Unknown')}")
            output.append(f"Coordinates: {ipinfo.get('location', 'Unknown')}")
            output.append(f"Organization: {ipinfo.get('org', 'Unknown')}")
            output.append(f"Postal Code: {ipinfo.get('postal', 'Unknown')}")
            output.append(f"Timezone: {ipinfo.get('timezone', 'Unknown')}")
            output.append(f"Hostname: {ipinfo.get('hostname', 'Unknown')}")
        
        # Reverse DNS
        output.append(f"\n{'─'*40}")
        output.append("REVERSE DNS")
        output.append(f"{'─'*40}")
        
        reverse_dns = results.get('reverse_dns', {})
        if 'error' in reverse_dns:
            output.append(f"Reverse DNS Error: {reverse_dns['error']}")
        else:
            output.append(f"Hostname: {reverse_dns.get('hostname', 'Unknown')}")
            aliases = reverse_dns.get('aliases', [])
            if aliases:
                output.append(f"Aliases: {', '.join(aliases[:3])}")
                if len(aliases) > 3:
                    output.append(f"  ... and {len(aliases) - 3} more")
        
        # Open Ports
        if 'open_ports' in results:
            output.append(f"\n{'─'*40}")
            output.append("OPEN PORTS")
            output.append(f"{'─'*40}")
            
            open_ports = results['open_ports']
            if open_ports:
                port_services = {
                    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
                    80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
                    993: 'IMAPS', 995: 'POP3S', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'
                }
                
                for port in sorted(open_ports):
                    service = port_services.get(port, 'Unknown')
                    output.append(f"  • Port {port} ({service}) - Open")
            else:
                output.append("  No common open ports detected")
        
        # VirusTotal
        if 'virustotal' in results:
            output.append(f"\n{'─'*40}")
            output.append("VIRUSTOTAL ANALYSIS")
            output.append(f"{'─'*40}")
            
            vt = results['virustotal']
            if 'error' in vt:
                output.append(f"VirusTotal Error: {vt['error']}")
            else:
                positives = vt.get('positives', 0)
                total = vt.get('total', 0)
                output.append(f"Detection Ratio: {positives}/{total}")
                output.append(f"Scan Date: {vt.get('scan_date', 'Unknown')}")
                
                if vt.get('detected_urls'):
                    output.append(f"Malicious URLs: {len(vt['detected_urls'])}")
                
                if vt.get('detected_downloaded_samples'):
                    output.append(f"Malicious Samples: {len(vt['detected_downloaded_samples'])}")
                
                if vt.get('permalink'):
                    output.append(f"Full Report: {vt['permalink']}")
        
        # Shodan
        if 'shodan' in results:
            output.append(f"\n{'─'*40}")
            output.append("SHODAN INFORMATION")
            output.append(f"{'─'*40}")
            
            shodan = results['shodan']
            if 'error' in shodan:
                output.append(f"Shodan Error: {shodan['error']}")
            else:
                output.append(f"Country: {shodan.get('country_name', 'Unknown')}")
                output.append(f"City: {shodan.get('city', 'Unknown')}")
                output.append(f"Organization: {shodan.get('org', 'Unknown')}")
                
                hostnames = shodan.get('hostnames', [])
                if hostnames:
                    output.append(f"Hostnames: {', '.join(hostnames[:3])}")
                    if len(hostnames) > 3:
                        output.append(f"  ... and {len(hostnames) - 3} more")
                
                ports = shodan.get('ports', [])
                if ports:
                    output.append(f"Open Ports: {', '.join(map(str, sorted(ports)))}")
                
                vulns = shodan.get('vulns', [])
                if vulns:
                    output.append(f"Vulnerabilities: {len(vulns)} found")
        
        return '\n'.join(output)
