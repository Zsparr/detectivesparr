import json
import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from typing import Dict, List, Any
import logging

class ExportManager:
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        self.ensure_output_dir()
        self.logger = logging.getLogger(__name__)
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_filename(self, prefix: str, extension: str) -> str:
        """Generate unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
    
    def export_json(self, data: Dict[str, Any], filename: str = None) -> str:
        """Export data to JSON file."""
        if filename is None:
            filename = self.generate_filename("report", "json")
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return filepath
        except Exception as e:
            self.logger.error(f"JSON export failed: {str(e)}")
            raise
    
    def export_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to CSV file."""
        if filename is None:
            filename = self.generate_filename("report", "csv")
        
        filepath = os.path.join(self.output_dir, filename)
        
        if not data:
            raise ValueError("No data to export")
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if isinstance(data[0], dict):
                    # Get all possible keys from all dictionaries
                    fieldnames = set()
                    for item in data:
                        fieldnames.update(item.keys())
                    fieldnames = sorted(list(fieldnames))
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for item in data:
                        # Convert nested dicts to strings for CSV
                        row = {}
                        for key, value in item.items():
                            if isinstance(value, (dict, list)):
                                row[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                row[key] = str(value) if value is not None else ""
                        writer.writerow(row)
                else:
                    writer = csv.writer(f)
                    for item in data:
                        writer.writerow([str(item)])
            
            return filepath
        except Exception as e:
            self.logger.error(f"CSV export failed: {str(e)}")
            raise
    
    def export_pdf(self, data: Dict[str, Any], filename: str = None, report_type: str = "General") -> str:
        """Export data to PDF report."""
        if filename is None:
            filename = self.generate_filename("report", "pdf")
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            # Title
            story.append(Paragraph(f"DETECTIVE OSINT REPORT", title_style))
            story.append(Paragraph(f"{report_type} Investigation", styles['Heading2']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Report content based on data type
            if 'username_results' in data:
                story.extend(self._format_username_results(data['username_results'], styles))
            
            if 'breach_results' in data:
                story.extend(self._format_breach_results(data['breach_results'], styles))
            
            if 'domain_results' in data:
                story.extend(self._format_domain_results(data['domain_results'], styles))
            
            if 'ip_results' in data:
                story.extend(self._format_ip_results(data['ip_results'], styles))
            
            if 'email_results' in data:
                story.extend(self._format_email_results(data['email_results'], styles))
            
            # Add metadata
            if 'metadata' in data:
                story.append(PageBreak())
                story.append(Paragraph("REPORT METADATA", heading_style))
                metadata_table = self._create_metadata_table(data['metadata'])
                story.append(metadata_table)
            
            doc.build(story)
            return filepath
            
        except Exception as e:
            self.logger.error(f"PDF export failed: {str(e)}")
            raise
    
    def _format_username_results(self, results: List[Dict], styles) -> List:
        """Format username search results for PDF."""
        story = []
        story.append(Paragraph("USERNAME SEARCH RESULTS", styles['Heading2']))
        
        found_profiles = [r for r in results if r.get('found')]
        error_profiles = [r for r in results if r.get('error')]
        
        if found_profiles:
            story.append(Paragraph(f"Found {len(found_profiles)} profiles:", styles['Heading3']))
            
            table_data = [['Platform', 'URL', 'Metadata']]
            for result in found_profiles:
                url = result.get('url', 'N/A')
                metadata = result.get('metadata', {})
                
                # Extract key metadata
                meta_text = ""
                if metadata.get('followers'):
                    meta_text += f"Followers: {metadata['followers']}"
                if metadata.get('bio'):
                    meta_text = meta_text + f"<br/>Bio: {metadata['bio'][:50]}..." if len(metadata['bio']) > 50 else meta_text + f"<br/>Bio: {metadata['bio']}"
                
                table_data.append([result.get('name', 'Unknown'), url[:50] + '...' if len(url) > 50 else url, meta_text])
            
            table = Table(table_data, colWidths=[2*inch, 3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        if error_profiles:
            story.append(Paragraph(f"Errors encountered on {len(error_profiles)} platforms:", styles['Heading3']))
            for result in error_profiles:
                story.append(Paragraph(f"• {result.get('name', 'Unknown')}: {result.get('error', 'Unknown error')}", styles['Normal']))
        
        return story
    
    def _format_breach_results(self, results: Dict, styles) -> List:
        """Format breach check results for PDF."""
        story = []
        story.append(Paragraph("DATA BREACH CHECK RESULTS", styles['Heading2']))
        
        if results.get('breaches'):
            story.append(Paragraph(f"Found {len(results['breaches'])} breaches:", styles['Heading3']))
            
            table_data = [['Breach Name', 'Date', 'Data Types']]
            for breach in results['breaches']:
                name = breach.get('name', 'Unknown')
                date = breach.get('breach_date', 'Unknown')
                data_types = ', '.join(breach.get('data_types', []))
                table_data.append([name, date, data_types])
            
            table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No breaches found.", styles['Normal']))
        
        return story
    
    def _format_domain_results(self, results: Dict, styles) -> List:
        """Format domain investigation results for PDF."""
        story = []
        story.append(Paragraph("DOMAIN INVESTIGATION RESULTS", styles['Heading2']))
        
        # WHOIS Information
        if 'whois' in results:
            story.append(Paragraph("WHOIS Information", styles['Heading3']))
            whois = results['whois']
            whois_data = [['Field', 'Value']]
            
            key_fields = ['registrar', 'creation_date', 'expiration_date', 'registrant_name', 'registrant_country']
            for field in key_fields:
                value = whois.get(field, 'Unknown')
                whois_data.append([field.replace('_', ' ').title(), str(value)])
            
            table = Table(whois_data, colWidths=[2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        # DNS Records
        if 'dns_records' in results:
            story.append(Paragraph("DNS Records", styles['Heading3']))
            dns = results['dns_records']
            
            for record_type, records in dns.items():
                if records:
                    story.append(Paragraph(f"{record_type} Records:", styles['Normal']))
                    for record in records[:3]:  # Limit to first 3
                        story.append(Paragraph(f"  • {record}", styles['Normal']))
                    if len(records) > 3:
                        story.append(Paragraph(f"  ... and {len(records) - 3} more", styles['Normal']))
        
        return story
    
    def _format_ip_results(self, results: Dict, styles) -> List:
        """Format IP analysis results for PDF."""
        story = []
        story.append(Paragraph("IP ADDRESS ANALYSIS RESULTS", styles['Heading2']))
        
        # IPInfo Details
        if 'ipinfo' in results:
            story.append(Paragraph("Location & ISP Information", styles['Heading3']))
            ipinfo = results['ipinfo']
            
            ipinfo_data = [['Field', 'Value']]
            key_fields = ['ip', 'city', 'region', 'country', 'org', 'hostname']
            for field in key_fields:
                value = ipinfo.get(field, 'Unknown')
                ipinfo_data.append([field.replace('_', ' ').title(), str(value)])
            
            table = Table(ipinfo_data, colWidths=[2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        # Open Ports
        if 'open_ports' in results:
            story.append(Paragraph("Open Ports", styles['Heading3']))
            ports = results['open_ports']
            if ports:
                port_services = {
                    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
                    80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
                    993: 'IMAPS', 995: 'POP3S', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt'
                }
                
                ports_data = [['Port', 'Service']]
                for port in sorted(ports):
                    service = port_services.get(port, 'Unknown')
                    ports_data.append([str(port), service])
                
                table = Table(ports_data, colWidths=[1.5*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
            else:
                story.append(Paragraph("No common open ports detected.", styles['Normal']))
        
        return story
    
    def _format_email_results(self, results: Dict, styles) -> List:
        """Format email analysis results for PDF."""
        story = []
        story.append(Paragraph("EMAIL HEADER ANALYSIS RESULTS", styles['Heading2']))
        
        # Basic Information
        if 'basic_info' in results:
            story.append(Paragraph("Basic Information", styles['Heading3']))
            basic = results['basic_info']
            
            basic_data = [['Field', 'Value']]
            for key, value in basic.items():
                basic_data.append([key.title(), str(value)])
            
            table = Table(basic_data, colWidths=[2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 12))
        
        # Authentication Results
        if 'authentication' in results:
            story.append(Paragraph("Authentication Results", styles['Heading3']))
            auth = results['authentication']
            
            for auth_type, result in auth.items():
                status = "✓ PASS" if result.lower() in ['pass', 'ok'] else "✗ FAIL"
                story.append(Paragraph(f"{auth_type.upper()}: {status}", styles['Normal']))
        
        # Spoofing Indicators
        if 'spoofing_indicators' in results:
            story.append(Paragraph("Spoofing Indicators", styles['Heading3']))
            indicators = results['spoofing_indicators']
            
            if indicators:
                for indicator in indicators:
                    story.append(Paragraph(f"⚠ {indicator['description']}", styles['Normal']))
            else:
                story.append(Paragraph("✓ No obvious spoofing indicators detected", styles['Normal']))
        
        return story
    
    def _create_metadata_table(self, metadata: Dict) -> Table:
        """Create metadata table for PDF."""
        data = [['Metadata Field', 'Value']]
        
        for key, value in metadata.items():
            data.append([key.replace('_', ' ').title(), str(value)])
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def export_username_report(self, results: List[Dict], username: str) -> Dict[str, str]:
        """Export comprehensive username search report."""
        # Prepare data for different formats
        export_data = {
            'username': username,
            'search_date': datetime.now().isoformat(),
            'username_results': results,
            'summary': {
                'total_sites_checked': len(results),
                'profiles_found': len([r for r in results if r.get('found')]),
                'errors': len([r for r in results if r.get('error')]),
                'sites_with_metadata': len([r for r in results if r.get('metadata') and r['metadata']])
            }
        }
        
        # Export in all formats
        exported_files = {}
        
        try:
            exported_files['json'] = self.export_json(export_data, f"username_search_{username}.json")
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
        
        try:
            # CSV format - flatten results
            csv_data = []
            for result in results:
                csv_data.append(result)
            exported_files['csv'] = self.export_csv(csv_data, f"username_search_{username}.csv")
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
        
        try:
            exported_files['pdf'] = self.export_pdf(export_data, f"username_search_{username}.pdf", "Username Search")
        except Exception as e:
            self.logger.error(f"PDF export failed: {e}")
        
        return exported_files
    
    def export_breach_report(self, results: Dict, query: str) -> Dict[str, str]:
        """Export breach check report."""
        export_data = {
            'query': query,
            'check_date': datetime.now().isoformat(),
            'breach_results': results,
            'summary': {
                'breaches_found': len(results.get('breaches', [])),
                'total_exposed_data_types': len(set().union(*[b.get('data_types', []) for b in results.get('breaches', [])]))
            }
        }
        
        exported_files = {}
        
        try:
            exported_files['json'] = self.export_json(export_data, f"breach_check_{query}.json")
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
        
        try:
            exported_files['pdf'] = self.export_pdf(export_data, f"breach_check_{query}.pdf", "Data Breach Check")
        except Exception as e:
            self.logger.error(f"PDF export failed: {e}")
        
        return exported_files
