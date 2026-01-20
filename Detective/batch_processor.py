import asyncio
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor
import time

from searcher import SiteChecker
from breach_checker import BreachChecker
from domain_investigator import DomainInvestigator
from ip_analyzer import IPAnalyzer
from email_analyzer import EmailAnalyzer
from export_manager import ExportManager
from config_manager import ConfigManager

class BatchProcessor:
    def __init__(self, config_manager: ConfigManager = None):
        self.config = config_manager or ConfigManager()
        self.export_manager = ExportManager()
        self.results = []
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        self.progress_callback = callback
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    async def batch_username_search(self, usernames: List[str], extract_metadata: bool = None) -> Dict[str, Any]:
        """Process multiple usernames in batch."""
        if extract_metadata is None:
            extract_metadata = self.config.get_preference('enable_metadata_extraction', True)
        
        max_concurrent = self.config.get_preference('max_concurrent_requests', 50)
        
        print(f"Starting batch username search for {len(usernames)} usernames...")
        
        all_results = {}
        checker = SiteChecker()
        
        for i, username in enumerate(usernames):
            self.update_progress(i, len(usernames), f"Processing {username}")
            
            try:
                # Check if we should generate variations
                generate_variations = self.config.get_preference('generate_username_variations', False)
                usernames_to_check = [username]
                
                if generate_variations:
                    variations = checker.generate_username_variations(username)
                    # Limit variations to avoid too many requests
                    max_variations = self.config.get_investigation_setting('username_variations_count', 10)
                    usernames_to_check = variations[:max_variations]
                
                # Search all variations
                username_results = {}
                for var_username in usernames_to_check:
                    results = await checker.search_all(var_username, extract_metadata)
                    username_results[var_username] = results
                
                # Find best results (most profiles found)
                best_username = max(username_results.keys(), 
                                  key=lambda x: len([r for r in username_results[x] if r.get('found')]))
                
                all_results[username] = {
                    'searched_variations': usernames_to_check,
                    'best_variation': best_username,
                    'results': username_results[best_username],
                    'all_variations_results': username_results,
                    'summary': {
                        'total_profiles_found': len([r for r in username_results[best_username] if r.get('found')]),
                        'total_sites_checked': len(username_results[best_username]),
                        'errors': len([r for r in username_results[best_username] if r.get('error')])
                    }
                }
                
                # Rate limiting
                if i < len(usernames) - 1:  # Don't sleep after last one
                    pause_time = self.config.get('ui_settings.pause_between_checks', 0.0)
                    if pause_time > 0:
                        await asyncio.sleep(pause_time)
                
            except Exception as e:
                all_results[username] = {
                    'error': str(e),
                    'summary': {'total_profiles_found': 0, 'total_sites_checked': 0, 'errors': 1}
                }
        
        self.update_progress(len(usernames), len(usernames), "Batch username search completed")
        
        return {
            'batch_type': 'username_search',
            'total_queries': len(usernames),
            'completion_time': datetime.now().isoformat(),
            'results': all_results,
            'summary': self._summarize_batch_results(all_results)
        }
    
    async def batch_breach_check(self, queries: List[str]) -> Dict[str, Any]:
        """Process multiple email/phone breach checks in batch."""
        print(f"Starting batch breach check for {len(queries)} queries...")
        
        all_results = {}
        checker = BreachChecker()
        
        for i, query in enumerate(queries):
            self.update_progress(i, len(queries), f"Checking {query}")
            
            try:
                # Determine if query is email or phone
                if '@' in query:
                    result = await checker.check_email_breach(query)
                    query_type = 'email'
                else:
                    result = await checker.check_phone_breach(query)
                    query_type = 'phone'
                
                all_results[query] = {
                    'type': query_type,
                    'result': result,
                    'summary': {
                        'breaches_found': len(result.get('breaches', [])),
                        'total_exposed_data_types': len(set().union(*[b.get('data_types', []) for b in result.get('breaches', [])]))
                    }
                }
                
                # Rate limiting
                if i < len(queries) - 1:
                    pause_time = self.config.get('ui_settings.pause_between_checks', 0.0)
                    if pause_time > 0:
                        await asyncio.sleep(pause_time)
                
            except Exception as e:
                all_results[query] = {
                    'error': str(e),
                    'type': 'unknown',
                    'summary': {'breaches_found': 0, 'total_exposed_data_types': 0}
                }
        
        self.update_progress(len(queries), len(queries), "Batch breach check completed")
        
        return {
            'batch_type': 'breach_check',
            'total_queries': len(queries),
            'completion_time': datetime.now().isoformat(),
            'results': all_results,
            'summary': self._summarize_batch_results(all_results)
        }
    
    async def batch_domain_investigation(self, domains: List[str]) -> Dict[str, Any]:
        """Process multiple domain investigations in batch."""
        print(f"Starting batch domain investigation for {len(domains)} domains...")
        
        all_results = {}
        
        async with DomainInvestigator() as investigator:
            for i, domain in enumerate(domains):
                self.update_progress(i, len(domains), f"Investigating {domain}")
                
                try:
                    result = await investigator.investigate_domain(domain)
                    all_results[domain] = {
                        'result': result,
                        'summary': {
                            'subdomains_found': len(result.get('subdomains', [])),
                            'dns_records_found': sum(1 for records in result.get('dns_records', {}).values() if records),
                            'has_whois': 'error' not in result.get('whois', {}),
                            'has_web_info': 'error' not in result.get('web_info', {})
                        }
                    }
                    
                    # Rate limiting
                    if i < len(domains) - 1:
                        pause_time = self.config.get('ui_settings.pause_between_checks', 0.0)
                        if pause_time > 0:
                            await asyncio.sleep(pause_time)
                
                except Exception as e:
                    all_results[domain] = {
                        'error': str(e),
                        'summary': {'subdomains_found': 0, 'dns_records_found': 0, 'has_whois': False, 'has_web_info': False}
                    }
        
        self.update_progress(len(domains), len(domains), "Batch domain investigation completed")
        
        return {
            'batch_type': 'domain_investigation',
            'total_queries': len(domains),
            'completion_time': datetime.now().isoformat(),
            'results': all_results,
            'summary': self._summarize_batch_results(all_results)
        }
    
    async def batch_ip_analysis(self, ips: List[str]) -> Dict[str, Any]:
        """Process multiple IP analyses in batch."""
        print(f"Starting batch IP analysis for {len(ips)} IP addresses...")
        
        all_results = {}
        vt_api_key = self.config.get_api_key('virustotal')
        shodan_api_key = self.config.get_api_key('shodan')
        check_ports = self.config.get_preference('check_open_ports', False)
        
        async with IPAnalyzer(self.config.get_api_key('ipinfo')) as analyzer:
            for i, ip in enumerate(ips):
                self.update_progress(i, len(ips), f"Analyzing {ip}")
                
                try:
                    result = await analyzer.analyze_ip(ip, vt_api_key, shodan_api_key, check_ports)
                    all_results[ip] = {
                        'result': result,
                        'summary': {
                            'has_location_info': 'error' not in result.get('ipinfo', {}),
                            'open_ports_count': len(result.get('open_ports', [])),
                            'has_virustotal': 'virustotal' in result,
                            'has_shodan': 'shodan' in result
                        }
                    }
                    
                    # Rate limiting
                    if i < len(ips) - 1:
                        pause_time = self.config.get('ui_settings.pause_between_checks', 0.0)
                        if pause_time > 0:
                            await asyncio.sleep(pause_time)
                
                except Exception as e:
                    all_results[ip] = {
                        'error': str(e),
                        'summary': {'has_location_info': False, 'open_ports_count': 0, 'has_virustotal': False, 'has_shodan': False}
                    }
        
        self.update_progress(len(ips), len(ips), "Batch IP analysis completed")
        
        return {
            'batch_type': 'ip_analysis',
            'total_queries': len(ips),
            'completion_time': datetime.now().isoformat(),
            'results': all_results,
            'summary': self._summarize_batch_results(all_results)
        }
    
    def load_batch_file(self, filepath: str) -> List[str]:
        """Load batch items from file (CSV, TXT, or JSON)."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        file_ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if file_ext == '.csv':
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    # Assume first column contains the data
                    return [row[0] for row in reader if row and row[0].strip()]
            
            elif file_ext == '.txt':
                with open(filepath, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            
            elif file_ext == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, list):
                        return [str(item) for item in data]
                    elif isinstance(data, dict):
                        # Look for common keys
                        for key in ['items', 'data', 'queries', 'targets']:
                            if key in data and isinstance(data[key], list):
                                return [str(item) for item in data[key]]
                        # If no list found, use dict keys
                        return list(data.keys())
                    else:
                        return [str(data)]
            
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    def _summarize_batch_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for batch results."""
        total_items = len(results)
        successful_items = len([r for r in results.values() if 'error' not in r])
        failed_items = total_items - successful_items
        
        # Calculate totals based on batch type
        summary = {
            'total_items': total_items,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'success_rate': (successful_items / total_items * 100) if total_items > 0 else 0
        }
        
        # Add specific metrics based on result summaries
        if results:
            first_result = next(iter(results.values()))
            if 'summary' in first_result:
                # Aggregate summary statistics
                for key, value in first_result['summary'].items():
                    if isinstance(value, (int, float)):
                        total = sum(r.get('summary', {}).get(key, 0) for r in results.values())
                        summary[f'total_{key}'] = total
                        if key == 'total_profiles_found':
                            summary['average_profiles_per_item'] = total / successful_items if successful_items > 0 else 0
        
        return summary
    
    async def export_batch_results(self, batch_results: Dict[str, Any], batch_type: str) -> Dict[str, str]:
        """Export batch results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"batch_{batch_type}_{timestamp}"
        
        exported_files = {}
        
        try:
            # JSON export
            json_file = self.export_manager.export_json(batch_results, f"{base_filename}.json")
            exported_files['json'] = json_file
        except Exception as e:
            print(f"JSON export failed: {e}")
        
        try:
            # CSV export - flatten results for CSV
            csv_data = self._flatten_batch_results_for_csv(batch_results)
            csv_file = self.export_manager.export_csv(csv_data, f"{base_filename}.csv")
            exported_files['csv'] = csv_file
        except Exception as e:
            print(f"CSV export failed: {e}")
        
        try:
            # PDF export
            pdf_file = self.export_manager.export_pdf(batch_results, f"{base_filename}.pdf", f"Batch {batch_type.replace('_', ' ').title()}")
            exported_files['pdf'] = pdf_file
        except Exception as e:
            print(f"PDF export failed: {e}")
        
        return exported_files
    
    def _flatten_batch_results_for_csv(self, batch_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten batch results for CSV export."""
        csv_data = []
        
        for query, result_data in batch_results.get('results', {}).items():
            row = {
                'query': query,
                'status': 'Success' if 'error' not in result_data else 'Error',
                'batch_type': batch_results.get('batch_type', 'unknown'),
                'completion_time': batch_results.get('completion_time', 'unknown')
            }
            
            # Add summary data
            for key, value in result_data.get('summary', {}).items():
                row[f'summary_{key}'] = value
            
            # Add error if present
            if 'error' in result_data:
                row['error'] = result_data['error']
            
            csv_data.append(row)
        
        return csv_data
    
    def print_batch_summary(self, batch_results: Dict[str, Any]):
        """Print a summary of batch results."""
        summary = batch_results.get('summary', {})
        batch_type = batch_results.get('batch_type', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"BATCH {batch_type.replace('_', ' ').upper()} SUMMARY")
        print(f"{'='*60}")
        print(f"Total items processed: {summary.get('total_items', 0)}")
        print(f"Successful: {summary.get('successful_items', 0)}")
        print(f"Failed: {summary.get('failed_items', 0)}")
        print(f"Success rate: {summary.get('success_rate', 0):.1f}%")
        
        # Show specific metrics based on batch type
        if batch_type == 'username_search':
            print(f"Total profiles found: {summary.get('total_total_profiles_found', 0)}")
            print(f"Average profiles per username: {summary.get('average_profiles_per_item', 0):.1f}")
        
        elif batch_type == 'breach_check':
            print(f"Total breaches found: {summary.get('total_breaches_found', 0)}")
        
        elif batch_type == 'domain_investigation':
            print(f"Total subdomains found: {summary.get('total_subdomains_found', 0)}")
            print(f"Total DNS records found: {summary.get('total_dns_records_found', 0)}")
        
        elif batch_type == 'ip_analysis':
            print(f"Total open ports found: {summary.get('total_open_ports_count', 0)}")
        
        print(f"{'='*60}")
    
    async def run_batch_from_file(self, filepath: str, batch_type: str) -> Dict[str, Any]:
        """Run batch processing from file."""
        try:
            items = self.load_batch_file(filepath)
            print(f"Loaded {len(items)} items from {os.path.basename(filepath)}")
            
            if batch_type == 'username':
                return await self.batch_username_search(items)
            elif batch_type == 'breach':
                return await self.batch_breach_check(items)
            elif batch_type == 'domain':
                return await self.batch_domain_investigation(items)
            elif batch_type == 'ip':
                return await self.batch_ip_analysis(items)
            else:
                raise ValueError(f"Unknown batch type: {batch_type}")
        
        except Exception as e:
            return {
                'batch_type': batch_type,
                'error': str(e),
                'total_queries': 0,
                'completion_time': datetime.now().isoformat(),
                'results': {},
                'summary': {'total_items': 0, 'successful_items': 0, 'failed_items': 0, 'success_rate': 0}
            }
