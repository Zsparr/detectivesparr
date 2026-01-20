import re
import json
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.header import decode_header
import ipaddress
from urllib.parse import unquote

class EmailAnalyzer:
    def __init__(self):
        self.suspicious_patterns = {
            'spoofed_domains': [],
            'suspicious_headers': [],
            'mismatched_servers': []
        }
    
    def parse_email_headers(self, raw_headers):
        """Parse raw email headers into structured format."""
        try:
            # Handle both string and bytes input
            if isinstance(raw_headers, str):
                raw_headers = raw_headers.encode('utf-8')
            
            # Parse the email headers
            msg = BytesParser(policy=policy.default).parsebytes(raw_headers)
            
            headers = {}
            for key, value in msg.items():
                headers[key.lower()] = self.decode_header_value(value)
            
            return headers
        except Exception as e:
            return {'error': f'Failed to parse headers: {str(e)}'}
    
    def decode_header_value(self, header_value):
        """Decode email header values (handle encoded words)."""
        try:
            decoded_parts = decode_header(str(header_value))
            decoded_value = []
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_value.append(part.decode(encoding))
                    else:
                        decoded_value.append(part.decode('utf-8', errors='ignore'))
                else:
                    decoded_value.append(str(part))
            
            return ''.join(decoded_value)
        except:
            return str(header_value)
    
    def extract_ip_addresses(self, headers):
        """Extract IP addresses from headers."""
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = []
        
        # Search in common headers that might contain IPs
        ip_headers = ['received', 'x-originating-ip', 'x-sender-ip', 'x-real-ip']
        
        for header_name in ip_headers:
            if header_name in headers:
                header_value = headers[header_name]
                found_ips = re.findall(ip_pattern, header_value)
                for ip in found_ips:
                    if self.is_valid_ip(ip):
                        ips.append({
                            'ip': ip,
                            'source_header': header_name,
                            'full_header': header_value
                        })
        
        return ips
    
    def is_valid_ip(self, ip):
        """Validate IP address."""
        try:
            ipaddress.ip_address(ip)
            # Exclude private IPs that are commonly internal
            private_ranges = [
                '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
                '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                '172.30.', '172.31.', '192.168.', '127.'
            ]
            
            for private_range in private_ranges:
                if ip.startswith(private_range):
                    return False
            
            return True
        except:
            return False
    
    def analyze_received_headers(self, headers):
        """Analyze Received headers for email path."""
        received_headers = []
        
        if 'received' in headers:
            received_list = headers['received']
            if isinstance(received_list, str):
                received_list = [received_list]
            
            for i, received in enumerate(received_list):
                # Extract server info and timestamps
                server_info = self.extract_server_info(received)
                timestamp = self.extract_timestamp(received)
                
                received_headers.append({
                    'hop': i + 1,
                    'raw_header': received,
                    'server_info': server_info,
                    'timestamp': timestamp
                })
        
        return received_headers
    
    def extract_server_info(self, received_header):
        """Extract server information from Received header."""
        server_info = {
            'from': None,
            'by': None,
            'with': None,
            'id': None,
            'for': None
        }
        
        # Extract server names and IPs
        patterns = {
            'from': r'from\s+([^\s]+)',
            'by': r'by\s+([^\s]+)',
            'with': r'with\s+([^\s]+)',
            'id': r'id\s+([^\s;]+)',
            'for': r'for\s+([^;\s]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, received_header, re.IGNORECASE)
            if match:
                server_info[key] = match.group(1)
        
        return server_info
    
    def extract_timestamp(self, received_header):
        """Extract timestamp from Received header."""
        # Common timestamp patterns
        patterns = [
            r';\s*([A-Za-z]{3},?\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+[+-]\d{4})',
            r';\s*([A-Za-z]{3},?\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+\w+)',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, received_header)
            if match:
                return match.group(1)
        
        return None
    
    def check_authentication_results(self, headers):
        """Check SPF, DKIM, and DMARC results."""
        auth_results = {}
        
        # Check Authentication-Results header
        if 'authentication-results' in headers:
            auth_header = headers['authentication-results'].lower()
            
            # SPF
            spf_match = re.search(r'spf=(\w+)', auth_header)
            if spf_match:
                auth_results['spf'] = spf_match.group(1)
            
            # DKIM
            dkim_match = re.search(r'dkim=(\w+)', auth_header)
            if dkim_match:
                auth_results['dkim'] = dkim_match.group(1)
            
            # DMARC
            dmarc_match = re.search(r'dmarc=(\w+)', auth_header)
            if dmarc_match:
                auth_results['dmarc'] = dmarc_match.group(1)
        
        # Check individual headers
        if 'received-spf' in headers:
            spf_match = re.search(r'(\w+)', headers['received-spf'])
            if spf_match:
                auth_results['received_spf'] = spf_match.group(1)
        
        return auth_results
    
    def analyze_message_id(self, headers):
        """Analyze Message-ID for anomalies."""
        if 'message-id' not in headers:
            return {'error': 'No Message-ID found'}
        
        message_id = headers['message-id']
        analysis = {
            'message_id': message_id,
            'format_valid': False,
            'domain': None,
            'suspicious': False
        }
        
        # Check Message-ID format
        id_pattern = r'<[^@]+@[^>]+>'
        if re.match(id_pattern, message_id):
            analysis['format_valid'] = True
            
            # Extract domain
            domain_match = re.search(r'@([^>]+)', message_id)
            if domain_match:
                analysis['domain'] = domain_match.group(1)
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'random',
            r'test'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, message_id, re.IGNORECASE):
                analysis['suspicious'] = True
                break
        
        return analysis
    
    def detect_spoofing_attempts(self, headers):
        """Detect potential email spoofing attempts."""
        spoofing_indicators = []
        
        # Check Return-Path vs From header
        if 'return-path' in headers and 'from' in headers:
            return_path_domain = self.extract_domain_from_email(headers['return-path'])
            from_domain = self.extract_domain_from_email(headers['from'])
            
            if return_path_domain and from_domain and return_path_domain != from_domain:
                spoofing_indicators.append({
                    'type': 'domain_mismatch',
                    'description': 'Return-Path domain differs from From domain',
                    'return_path': return_path_domain,
                    'from': from_domain
                })
        
        # Check for missing authentication headers
        required_headers = ['authentication-results', 'received-spf']
        missing_auth = [h for h in required_headers if h not in headers]
        
        if missing_auth:
            spoofing_indicators.append({
                'type': 'missing_authentication',
                'description': f'Missing authentication headers: {", ".join(missing_auth)}',
                'missing_headers': missing_auth
            })
        
        # Check Reply-To vs From
        if 'reply-to' in headers and 'from' in headers:
            reply_to_domain = self.extract_domain_from_email(headers['reply-to'])
            from_domain = self.extract_domain_from_email(headers['from'])
            
            if reply_to_domain and from_domain and reply_to_domain != from_domain:
                spoofing_indicators.append({
                    'type': 'reply_to_mismatch',
                    'description': 'Reply-To domain differs from From domain',
                    'reply_to': reply_to_domain,
                    'from': from_domain
                })
        
        return spoofing_indicators
    
    def extract_domain_from_email(self, email_string):
        """Extract domain from email address."""
        email_pattern = r'<([^>]+)>|([^@\s]+@[^@\s]+)'
        matches = re.findall(email_pattern, email_string)
        
        for match in matches:
            email = match[0] if match[0] else match[1]
            if '@' in email:
                return email.split('@')[1].lower()
        
        return None
    
    def analyze_email_headers(self, raw_headers):
        """Perform comprehensive email header analysis."""
        print("Analyzing email headers...")
        
        # Parse headers
        headers = self.parse_email_headers(raw_headers)
        if 'error' in headers:
            return headers
        
        # Perform all analyses
        analysis = {
            'analysis_date': datetime.now().isoformat(),
            'headers': headers,
            'extracted_ips': self.extract_ip_addresses(headers),
            'received_headers': self.analyze_received_headers(headers),
            'authentication': self.check_authentication_results(headers),
            'message_id_analysis': self.analyze_message_id(headers),
            'spoofing_indicators': self.detect_spoofing_attempts(headers)
        }
        
        # Add basic email info
        analysis['basic_info'] = {
            'from': headers.get('from', 'Unknown'),
            'to': headers.get('to', 'Unknown'),
            'subject': headers.get('subject', 'Unknown'),
            'date': headers.get('date', 'Unknown')
        }
        
        return analysis
    
    def format_results(self, analysis):
        """Format email analysis results for display."""
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        output = []
        output.append(f"\n{'='*60}")
        output.append(f"EMAIL HEADER ANALYSIS RESULTS")
        output.append(f"{'='*60}")
        output.append(f"Analysis Date: {analysis['analysis_date']}")
        
        # Basic Information
        output.append(f"\n{'─'*40}")
        output.append("BASIC EMAIL INFORMATION")
        output.append(f"{'─'*40}")
        
        basic = analysis.get('basic_info', {})
        output.append(f"From: {basic.get('from', 'Unknown')}")
        output.append(f"To: {basic.get('to', 'Unknown')}")
        output.append(f"Subject: {basic.get('subject', 'Unknown')}")
        output.append(f"Date: {basic.get('date', 'Unknown')}")
        
        # Authentication Results
        output.append(f"\n{'─'*40}")
        output.append("AUTHENTICATION RESULTS")
        output.append(f"{'─'*40}")
        
        auth = analysis.get('authentication', {})
        if auth:
            for auth_type, result in auth.items():
                status_color = "✓" if result.lower() in ['pass', 'ok'] else "✗"
                output.append(f"{status_color} {auth_type.upper()}: {result}")
        else:
            output.append("No authentication results found")
        
        # Message ID Analysis
        output.append(f"\n{'─'*40}")
        output.append("MESSAGE ID ANALYSIS")
        output.append(f"{'─'*40}")
        
        msg_id = analysis.get('message_id_analysis', {})
        if 'error' not in msg_id:
            output.append(f"Message-ID: {msg_id.get('message_id', 'Unknown')}")
            output.append(f"Format Valid: {'✓' if msg_id.get('format_valid') else '✗'}")
            output.append(f"Domain: {msg_id.get('domain', 'Unknown')}")
            output.append(f"Suspicious: {'⚠' if msg_id.get('suspicious') else '✓'}")
        
        # Extracted IP Addresses
        output.append(f"\n{'─'*40}")
        output.append("EXTRACTED IP ADDRESSES")
        output.append(f"{'─'*40}")
        
        ips = analysis.get('extracted_ips', [])
        if ips:
            for ip_info in ips:
                output.append(f"  • {ip_info['ip']} (from {ip_info['source_header']})")
        else:
            output.append("  No external IP addresses found")
        
        # Received Headers (Email Path)
        output.append(f"\n{'─'*40}")
        output.append("EMAIL PATH (RECEIVED HEADERS)")
        output.append(f"{'─'*40}")
        
        received = analysis.get('received_headers', [])
        if received:
            for hop in received:
                output.append(f"\nHop {hop['hop']}:")
                server = hop.get('server_info', {})
                if server.get('from'):
                    output.append(f"  From: {server['from']}")
                if server.get('by'):
                    output.append(f"  By: {server['by']}")
                if server.get('with'):
                    output.append(f"  With: {server['with']}")
                if hop.get('timestamp'):
                    output.append(f"  Time: {hop['timestamp']}")
        else:
            output.append("  No Received headers found")
        
        # Spoofing Indicators
        output.append(f"\n{'─'*40}")
        output.append("SPOOFING INDICATORS")
        output.append(f"{'─'*40}")
        
        spoofing = analysis.get('spoofing_indicators', [])
        if spoofing:
            for indicator in spoofing:
                output.append(f"⚠ {indicator['description']}")
                if indicator.get('return_path') and indicator.get('from'):
                    output.append(f"   Return-Path: {indicator['return_path']}")
                    output.append(f"   From: {indicator['from']}")
        else:
            output.append("✓ No obvious spoofing indicators detected")
        
        return '\n'.join(output)
