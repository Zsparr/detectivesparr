import asyncio
import aiohttp
import dns.resolver
import whois
import json
import re
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

class DomainInvestigator:
    def __init__(self):
        self.session = None
        self.results = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def clean_domain(self, domain):
        """Extract and clean domain from URL or plain domain."""
        if not domain:
            return None
        
        # Remove protocol if present
        if '://' in domain:
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove paths and query parameters
        domain = domain.split('/')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, domain):
            return None
            
        return domain.lower()
    
    async def get_whois_info(self, domain):
        """Get WHOIS information for the domain."""
        try:
            w = whois.whois(domain)
            
            # Clean up the WHOIS data
            whois_data = {
                'registrar': getattr(w, 'registrar', 'Unknown'),
                'creation_date': getattr(w, 'creation_date', None),
                'expiration_date': getattr(w, 'expiration_date', None),
                'updated_date': getattr(w, 'updated_date', None),
                'name_servers': getattr(w, 'name_servers', []),
                'status': getattr(w, 'status', []),
                'registrant_name': getattr(w, 'name', None),
                'registrant_org': getattr(w, 'org', None),
                'registrant_country': getattr(w, 'country', None),
                'registrant_email': getattr(w, 'email', None)
            }
            
            # Handle lists and dates
            if isinstance(whois_data['creation_date'], list):
                whois_data['creation_date'] = whois_data['creation_date'][0]
            if isinstance(whois_data['expiration_date'], list):
                whois_data['expiration_date'] = whois_data['expiration_date'][0]
            if isinstance(whois_data['updated_date'], list):
                whois_data['updated_date'] = whois_data['updated_date'][0]
            
            # Format dates
            for date_field in ['creation_date', 'expiration_date', 'updated_date']:
                if whois_data[date_field]:
                    whois_data[date_field] = str(whois_data[date_field])
            
            return whois_data
        except Exception as e:
            return {'error': f'WHOIS lookup failed: {str(e)}'}
    
    async def get_dns_records(self, domain):
        """Get comprehensive DNS records for the domain."""
        dns_records = {}
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                dns_records[record_type] = [str(rdata) for rdata in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                dns_records[record_type] = []
            except Exception as e:
                dns_records[record_type] = [f'Error: {str(e)}']
        
        return dns_records
    
    async def get_subdomains(self, domain):
        """Find subdomains using various techniques."""
        subdomains = set()
        
        # Common subdomain wordlist
        common_subdomains = [
            'www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop', 'forum', 
            'support', 'help', 'test', 'dev', 'staging', 'prod', 'secure',
            'vpn', 'remote', 'portal', 'dashboard', 'app', 'mobile', 'm',
            'cdn', 'static', 'assets', 'media', 'img', 'images', 'js', 'css'
        ]
        
        # Check common subdomains
        tasks = []
        for subdomain in common_subdomains:
            full_domain = f"{subdomain}.{domain}"
            tasks.append(self.check_subdomain_exists(full_domain))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if result and result != False:
                subdomains.add(common_subdomains[i] + '.' + domain)
        
        return list(subdomains)
    
    async def check_subdomain_exists(self, subdomain):
        """Check if a subdomain exists by DNS resolution."""
        try:
            answers = dns.resolver.resolve(subdomain, 'A')
            return True if answers else False
        except:
            try:
                answers = dns.resolver.resolve(subdomain, 'CNAME')
                return True if answers else False
            except:
                return False
    
    async def get_web_info(self, domain):
        """Get information from the website itself."""
        web_info = {}
        
        try:
            url = f"https://{domain}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract basic info
                    web_info['title'] = soup.title.string.strip() if soup.title else 'No title'
                    web_info['status_code'] = response.status
                    
                    # Extract meta tags
                    meta_tags = {}
                    for meta in soup.find_all('meta'):
                        name = meta.get('name') or meta.get('property')
                        content = meta.get('content')
                        if name and content:
                            meta_tags[name] = content
                    
                    web_info['meta_tags'] = meta_tags
                    
                    # Look for security headers
                    security_headers = {}
                    security_header_names = [
                        'X-Frame-Options', 'X-XSS-Protection', 'X-Content-Type-Options',
                        'Strict-Transport-Security', 'Content-Security-Policy',
                        'X-Content-Security-Policy', 'Referrer-Policy'
                    ]
                    
                    for header in security_header_names:
                        if header in response.headers:
                            security_headers[header] = response.headers[header]
                    
                    web_info['security_headers'] = security_headers
                    web_info['server'] = response.headers.get('Server', 'Unknown')
                    
                else:
                    web_info['status_code'] = response.status
                    
        except Exception as e:
            web_info['error'] = str(e)
        
        # Try HTTP if HTTPS fails
        if 'error' in web_info:
            try:
                url = f"http://{domain}"
                async with self.session.get(url) as response:
                    web_info['http_status'] = response.status
            except:
                pass
        
        return web_info
    
    async def investigate_domain(self, domain):
        """Perform comprehensive domain investigation."""
        clean_domain = self.clean_domain(domain)
        if not clean_domain:
            return {'error': 'Invalid domain format'}
        
        print(f"Investigating domain: {clean_domain}")
        
        # Run all investigations concurrently
        tasks = [
            self.get_whois_info(clean_domain),
            self.get_dns_records(clean_domain),
            self.get_subdomains(clean_domain),
            self.get_web_info(clean_domain)
        ]
        
        whois_info, dns_records, subdomains, web_info = await asyncio.gather(*tasks)
        
        results = {
            'domain': clean_domain,
            'investigation_date': datetime.now().isoformat(),
            'whois': whois_info,
            'dns_records': dns_records,
            'subdomains': subdomains,
            'web_info': web_info
        }
        
        return results
    
    def format_results(self, results):
        """Format investigation results for display."""
        if 'error' in results:
            return f"Error: {results['error']}"
        
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"DOMAIN INVESTIGATION RESULTS")
        output.append(f"{'='*60}")
        output.append(f"Domain: {results['domain']}")
        output.append(f"Investigation Date: {results['investigation_date']}")
        
        # WHOIS Information
        output.append(f"\n{'─'*40}")
        output.append("WHOIS INFORMATION")
        output.append(f"{'─'*40}")
        
        whois = results['whois']
        if 'error' in whois:
            output.append(f"WHOIS Error: {whois['error']}")
        else:
            output.append(f"Registrar: {whois.get('registrar', 'Unknown')}")
            output.append(f"Created: {whois.get('creation_date', 'Unknown')}")
            output.append(f"Expires: {whois.get('expiration_date', 'Unknown')}")
            output.append(f"Updated: {whois.get('updated_date', 'Unknown')}")
            output.append(f"Registrant: {whois.get('registrant_name', 'Unknown')}")
            output.append(f"Organization: {whois.get('registrant_org', 'Unknown')}")
            output.append(f"Country: {whois.get('registrant_country', 'Unknown')}")
            
            name_servers = whois.get('name_servers', [])
            if name_servers:
                output.append(f"Name Servers: {', '.join(str(ns) for ns in name_servers[:3])}")
                if len(name_servers) > 3:
                    output.append(f"  ... and {len(name_servers) - 3} more")
        
        # DNS Records
        output.append(f"\n{'─'*40}")
        output.append("DNS RECORDS")
        output.append(f"{'─'*40}")
        
        dns = results['dns_records']
        for record_type, records in dns.items():
            if records:
                output.append(f"\n{record_type} Records:")
                for record in records[:5]:  # Limit to first 5 records
                    if not record.startswith('Error:'):
                        output.append(f"  • {record}")
                    else:
                        output.append(f"  • {record}")
                if len(records) > 5:
                    output.append(f"  ... and {len(records) - 5} more")
        
        # Subdomains
        output.append(f"\n{'─'*40}")
        output.append("DISCOVERED SUBDOMAINS")
        output.append(f"{'─'*40}")
        
        subdomains = results['subdomains']
        if subdomains:
            for subdomain in subdomains[:10]:  # Limit to first 10
                output.append(f"  • {subdomain}")
            if len(subdomains) > 10:
                output.append(f"  ... and {len(subdomains) - 10} more")
        else:
            output.append("  No subdomains found")
        
        # Web Information
        output.append(f"\n{'─'*40}")
        output.append("WEBSITE INFORMATION")
        output.append(f"{'─'*40}")
        
        web = results['web_info']
        if 'error' in web:
            output.append(f"Web Info Error: {web['error']}")
        else:
            output.append(f"Title: {web.get('title', 'Unknown')}")
            output.append(f"Status Code: {web.get('status_code', 'Unknown')}")
            output.append(f"Server: {web.get('server', 'Unknown')}")
            
            if web.get('security_headers'):
                output.append("\nSecurity Headers:")
                for header, value in web.get('security_headers', {}).items():
                    output.append(f"  • {header}: {value}")
        
        return '\n'.join(output)
