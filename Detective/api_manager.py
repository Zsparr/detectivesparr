import json
import os
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime

class APIManager:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.api_endpoints = {
            'virustotal': {
                'test_url': 'https://www.virustotal.com/vtapi/v2/ip-address/report',
                'test_params': {'apikey': '{key}', 'ip': '8.8.8.8'},
                'validation_pattern': r'^[a-f0-9]{64}$',
                'description': 'VirusTotal - IP/Domain maliciousness detection',
                'free_tier_limit': '500 requests/day',
                'website': 'https://www.virustotal.com/'
            },
            'shodan': {
                'test_url': 'https://api.shodan.io/shodan/host/8.8.8.8',
                'test_params': {'key': '{key}'},
                'validation_pattern': r'^[A-Za-z0-9]{32}$',
                'description': 'Shodan - Device and service enumeration',
                'free_tier_limit': '1,000 requests/month',
                'website': 'https://www.shodan.io/'
            },
            'ipinfo': {
                'test_url': 'https://ipinfo.io/8.8.8.8/json',
                'test_params': {'token': '{key}'},
                'validation_pattern': r'^[a-f0-9]{32}$',
                'description': 'IPInfo - IP geolocation and ISP information',
                'free_tier_limit': '50,000 requests/month',
                'website': 'https://ipinfo.io/'
            },
            'hunter': {
                'test_url': 'https://api.hunter.io/v2/domain-verifier',
                'test_params': {'api_key': '{key}', 'domain': 'google.com'},
                'validation_pattern': r'^[a-f0-9]{36}$',
                'description': 'Hunter - Email domain verification',
                'free_tier_limit': '100 requests/month',
                'website': 'https://hunter.io/'
            }
        }
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
        if self.config:
            return self.config.get_api_key(service)
        return None
    
    def set_api_key(self, service: str, api_key: str) -> bool:
        """Set API key for a service."""
        if self.config:
            return self.config.set_api_key(service, api_key)
        return False
    
    def validate_api_key_format(self, service: str, api_key: str) -> bool:
        """Validate API key format."""
        if service not in self.api_endpoints:
            return False
        
        pattern = self.api_endpoints[service]['validation_pattern']
        import re
        return bool(re.match(pattern, api_key))
    
    async def test_api_key(self, service: str, api_key: str) -> Dict[str, Any]:
        """Test API key validity."""
        if service not in self.api_endpoints:
            return {'valid': False, 'error': 'Unknown service'}
        
        endpoint = self.api_endpoints[service]
        
        try:
            # Prepare test request
            url = endpoint['test_url']
            params = {}
            for key, value in endpoint['test_params'].items():
                if '{key}' in str(value):
                    params[key] = api_key
                else:
                    params[key] = value
            
            # Make test request
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    'valid': True,
                    'service': service,
                    'status_code': response.status_code,
                    'response_size': len(response.content),
                    'test_time': datetime.now().isoformat()
                }
            elif response.status_code == 401 or response.status_code == 403:
                return {
                    'valid': False,
                    'service': service,
                    'error': 'Invalid API key',
                    'status_code': response.status_code
                }
            elif response.status_code == 429:
                return {
                    'valid': False,
                    'service': service,
                    'error': 'Rate limit exceeded',
                    'status_code': response.status_code
                }
            else:
                return {
                    'valid': False,
                    'service': service,
                    'error': f'HTTP {response.status_code}: {response.text[:100]}',
                    'status_code': response.status_code
                }
        
        except requests.exceptions.Timeout:
            return {
                'valid': False,
                'service': service,
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'valid': False,
                'service': service,
                'error': 'Connection error'
            }
        except Exception as e:
            return {
                'valid': False,
                'service': service,
                'error': f'Test failed: {str(e)}'
            }
    
    async def test_all_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Test all configured API keys."""
        results = {}
        
        for service in self.api_endpoints.keys():
            api_key = self.get_api_key(service)
            if api_key:
                print(f"Testing {service} API key...")
                result = await self.test_api_key(service, api_key)
                results[service] = result
            else:
                results[service] = {
                    'valid': False,
                    'service': service,
                    'error': 'No API key configured'
                }
        
        return results
    
    def get_service_info(self, service: str) -> Optional[Dict[str, Any]]:
        """Get information about a service."""
        return self.api_endpoints.get(service)
    
    def list_all_services(self) -> Dict[str, Dict[str, Any]]:
        """List all available services."""
        return self.api_endpoints.copy()
    
    def get_configured_services(self) -> Dict[str, str]:
        """Get list of configured services with masked keys."""
        configured = {}
        
        for service in self.api_endpoints.keys():
            api_key = self.get_api_key(service)
            if api_key:
                # Mask the key for display
                if len(api_key) > 8:
                    masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
                else:
                    masked = '*' * len(api_key)
                configured[service] = masked
            else:
                configured[service] = 'Not configured'
        
        return configured
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics (placeholder for future implementation)."""
        stats = {
            'total_configured': 0,
            'working_keys': 0,
            'services': {}
        }
        
        for service in self.api_endpoints.keys():
            api_key = self.get_api_key(service)
            if api_key:
                stats['total_configured'] += 1
                stats['services'][service] = {
                    'configured': True,
                    'key_length': len(api_key),
                    'last_test': None,
                    'status': 'Unknown'
                }
            else:
                stats['services'][service] = {
                    'configured': False,
                    'key_length': 0,
                    'last_test': None,
                    'status': 'Not configured'
                }
        
        return stats
    
    def interactive_api_setup(self):
        """Interactive API key setup."""
        print("\n" + "="*60)
        print("DETECTIVE - API Key Management")
        print("="*60)
        
        print("\nConfigure API keys for enhanced features")
        print("All API keys are optional - the tool works without them")
        print("but provides more information with API integrations.\n")
        
        for service, info in self.api_endpoints.items():
            print(f"\n{'─'*40}")
            print(f"{service.upper()}")
            print(f"{'─'*40}")
            print(f"Description: {info['description']}")
            print(f"Free tier: {info['free_tier_limit']}")
            print(f"Website: {info['website']}")
            
            current_key = self.get_api_key(service)
            if current_key:
                print(f"Current status: Configured ({current_key[:4]}{'*' * (len(current_key) - 4)})")
                change = input("Change this key? (y/n): ").strip().lower()
                if change not in ['y', 'yes']:
                    continue
            else:
                print("Current status: Not configured")
            
            # Get new key
            new_key = input(f"Enter {service} API key (or press Enter to skip): ").strip()
            
            if new_key:
                # Validate format
                if self.validate_api_key_format(service, new_key):
                    self.set_api_key(service, new_key)
                    print(f"✓ {service} API key configured")
                else:
                    print(f"⚠ Warning: {service} API key format may be incorrect")
                    confirm = input("Save anyway? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        self.set_api_key(service, new_key)
                        print(f"✓ {service} API key configured (with warning)")
            else:
                print(f"- Skipped {service} API key")
        
        # Test configured keys
        print(f"\n{'─'*40}")
        print("Testing configured API keys...")
        print(f"{'─'*40}")
        
        import asyncio
        
        async def test_keys():
            results = await self.test_all_api_keys()
            for service, result in results.items():
                if result['valid']:
                    print(f"✓ {service}: Working")
                else:
                    print(f"✗ {service}: {result.get('error', 'Unknown error')}")
        
        asyncio.run(test_keys())
        
        print(f"\n✓ API key setup completed!")
        print("You can always update API keys later through the configuration menu.")
    
    def export_api_keys(self, filepath: str, mask_keys: bool = True) -> bool:
        """Export API keys to file."""
        try:
            export_data = {}
            
            for service in self.api_endpoints.keys():
                api_key = self.get_api_key(service)
                if api_key:
                    if mask_keys:
                        # Mask the key for security
                        if len(api_key) > 8:
                            export_data[service] = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
                        else:
                            export_data[service] = '*' * len(api_key)
                    else:
                        export_data[service] = api_key
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def import_api_keys(self, filepath: str, clear_existing: bool = False) -> bool:
        """Import API keys from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if clear_existing:
                # Clear all existing keys first
                for service in self.api_endpoints.keys():
                    self.set_api_key(service, '')
            
            imported_count = 0
            for service, api_key in import_data.items():
                if service in self.api_endpoints:
                    # Skip masked keys
                    if not api_key.count('*') > len(api_key) / 2:
                        self.set_api_key(service, api_key)
                        imported_count += 1
            
            print(f"Imported {imported_count} API keys")
            return True
        except Exception:
            return False
    
    def generate_api_report(self) -> Dict[str, Any]:
        """Generate comprehensive API status report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_services': len(self.api_endpoints),
                'configured_services': 0,
                'working_services': 0
            }
        }
        
        import asyncio
        
        async def generate_report_async():
            results = await self.test_all_api_keys()
            
            for service, result in results.items():
                api_key = self.get_api_key(service)
                service_info = self.api_endpoints[service]
                
                service_data = {
                    'name': service.upper(),
                    'description': service_info['description'],
                    'website': service_info['website'],
                    'free_tier_limit': service_info['free_tier_limit'],
                    'configured': bool(api_key),
                    'key_length': len(api_key) if api_key else 0,
                    'test_result': result,
                    'last_test': result.get('test_time')
                }
                
                if api_key:
                    report['summary']['configured_services'] += 1
                
                if result.get('valid'):
                    report['summary']['working_services'] += 1
                
                report['services'][service] = service_data
            
            return report
        
        return asyncio.run(generate_report_async())
    
    def print_api_status(self):
        """Print current API status."""
        configured = self.get_configured_services()
        
        print(f"\n{'='*50}")
        print("API STATUS")
        print(f"{'='*50}")
        
        for service, status in configured.items():
            info = self.api_endpoints[service]
            print(f"\n{service.upper()}:")
            print(f"  Status: {status}")
            print(f"  Description: {info['description']}")
            print(f"  Free tier: {info['free_tier_limit']}")
        
        print(f"\n{'='*50}")
        print(f"Configured services: {len([s for s in configured.values() if s != 'Not configured'])}/{len(configured)}")
        print(f"{'='*50}")
