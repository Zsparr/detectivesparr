import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        default_config = {
            "api_keys": {
                "ipinfo": "",
                "virustotal": "",
                "shodan": "",
                "hunter": ""
            },
            "preferences": {
                "default_export_format": "json",
                "auto_export": False,
                "export_directory": "exports",
                "max_concurrent_requests": 50,
                "request_timeout": 10,
                "enable_metadata_extraction": True,
                "show_not_found_sites": False,
                "show_error_sites": False,
                "check_open_ports": False,
                "generate_username_variations": False,
                "randomize_site_order": False,
                "max_sites_to_check": 0,
                "retry_attempts": 2,
                "concurrency_limit": 50,
                "use_extended_sites": True
            },
            "site_sources": ["sites.json", "sites_extra.json", "sites_extended.json"],
            "investigation_settings": {
                "username_variations_count": 10,
                "subdomain_scan_depth": "basic",  # basic, comprehensive
                "port_scan_common_only": True,
                "dns_record_types": ["A", "AAAA", "MX", "NS", "TXT", "CNAME"],
                "email_header_analysis_depth": "standard"  # basic, standard, detailed
            },
            "ui_settings": {
                "color_scheme": "default",  # default, dark, light
                "show_progress_bars": True,
                "verbose_output": False,
                "pause_between_checks": 0.0
            },
            "security": {
                "enable_tor_support": False,
                "tor_port": 9050,
                "user_agent_rotation": False,
                "rate_limiting": True,
                "max_requests_per_minute": 60
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                config = self._merge_configs(default_config, loaded_config)
                return config
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration.")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with defaults."""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'api_keys.ipinfo')."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self.config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the final value
            config[keys[-1]] = value
            return True
        except (KeyError, TypeError):
            return False
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        api_key = self.get(f"api_keys.{service}")
        return api_key if api_key else None
    
    def set_api_key(self, service: str, api_key: str) -> bool:
        """Set API key for a specific service."""
        return self.set(f"api_keys.{service}", api_key)
    
    def get_preference(self, preference: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.get(f"preferences.{preference}", default)
    
    def set_preference(self, preference: str, value: Any) -> bool:
        """Set user preference."""
        return self.set(f"preferences.{preference}", value)
    
    def get_investigation_setting(self, setting: str, default: Any = None) -> Any:
        """Get investigation setting."""
        return self.get(f"investigation_settings.{setting}", default)
    
    def set_investigation_setting(self, setting: str, value: Any) -> bool:
        """Set investigation setting."""
        return self.set(f"investigation_settings.{setting}", value)
    
    def list_api_keys(self) -> Dict[str, str]:
        """List all configured API keys (masked for security)."""
        api_keys = self.config.get('api_keys', {})
        masked_keys = {}
        
        for service, key in api_keys.items():
            if key and len(key) > 4:
                masked_keys[service] = key[:4] + '*' * (len(key) - 4)
            else:
                masked_keys[service] = key if key else "Not set"
        
        return masked_keys
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys format (basic validation)."""
        api_keys = self.config.get('api_keys', {})
        validation_results = {}
        
        # Basic format validation for different services
        patterns = {
            'virustotal': r'^[a-f0-9]{64}$',  # 64-character hex
            'shodan': r'^[A-Za-z0-9]{32}$',   # 32-character alphanumeric
            'ipinfo': r'^[a-f0-9]{32}$',      # 32-character hex
            'hunter': r'^[a-f0-9]{36}$'       # 36-character hex (UUID-like)
        }
        
        for service, key in api_keys.items():
            if not key:
                validation_results[service] = False
                continue
            
            pattern = patterns.get(service, r'^.+$')  # Default to any non-empty string
            validation_results[service] = bool(key and len(key) > 0)
        
        return validation_results
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self.config = self.load_config()
            return True
        except OSError:
            return False
    
    def export_config(self, filename: str) -> bool:
        """Export current configuration to a file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def import_config(self, filename: str) -> bool:
        """Import configuration from a file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate imported config structure
            if self._validate_config_structure(imported_config):
                self.config = self._merge_configs(self.config, imported_config)
                return self.save_config()
            else:
                print("Invalid configuration file structure.")
                return False
        except (IOError, json.JSONDecodeError):
            return False
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> bool:
        """Basic validation of configuration structure."""
        required_sections = ['api_keys', 'preferences', 'investigation_settings', 'ui_settings', 'security']
        
        for section in required_sections:
            if section not in config or not isinstance(config[section], dict):
                return False
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for display."""
        return {
            'config_file': self.config_file,
            'api_keys_configured': len([k for k, v in self.config.get('api_keys', {}).items() if v]),
            'total_api_keys': len(self.config.get('api_keys', {})),
            'auto_export_enabled': self.get_preference('auto_export', False),
            'metadata_extraction': self.get_preference('enable_metadata_extraction', True),
            'tor_enabled': self.get('security.enable_tor_support', False),
            'rate_limiting': self.get('security.rate_limiting', True),
            'max_concurrent_requests': self.get_preference('max_concurrent_requests', 50)
        }
    
    def interactive_setup(self):
        """Interactive configuration setup."""
        print("\n" + "="*50)
        print("DETECTIVE - Configuration Setup")
        print("="*50)
        
        print("\nOptional: Configure API keys for enhanced features")
        print("You can skip any of these by pressing Enter")
        
        services = {
            'ipinfo': 'IP geolocation and ISP information',
            'virustotal': 'IP/Domain maliciousness detection',
            'shodan': 'Device and service enumeration',
            'hunter': 'Email domain verification'
        }
        
        for service, description in services.items():
            current_key = self.get_api_key(service)
            current_display = "Set" if current_key else "Not set"
            
            print(f"\n{service.upper()} - {description}")
            print(f"Current status: {current_display}")
            
            if current_key:
                change = input("Change this key? (y/n): ").strip().lower()
                if change not in ['y', 'yes']:
                    continue
            
            new_key = input(f"Enter {service} API key (or press Enter to skip): ").strip()
            if new_key:
                self.set_api_key(service, new_key)
                print(f"✓ {service} API key configured")
            else:
                print(f"- Skipped {service} API key")
        
        print("\nConfigure preferences:")
        
        # Export format
        current_format = self.get_preference('default_export_format', 'json')
        print(f"Default export format (current: {current_format}) [json/csv/pdf]:")
        export_format = input().strip().lower()
        if export_format in ['json', 'csv', 'pdf']:
            self.set_preference('default_export_format', export_format)
        
        # Auto export
        auto_export = self.get_preference('auto_export', False)
        print(f"Auto-export results? (current: {'yes' if auto_export else 'no'}) [y/n]:")
        auto = input().strip().lower()
        self.set_preference('auto_export', auto in ['y', 'yes'])
        
        # Metadata extraction
        metadata = self.get_preference('enable_metadata_extraction', True)
        print(f"Enable metadata extraction? (current: {'yes' if metadata else 'no'}) [y/n]:")
        meta = input().strip().lower()
        self.set_preference('enable_metadata_extraction', meta in ['y', 'yes'])
        
        # Username variations
        variations = self.get_preference('generate_username_variations', False)
        print(f"Generate username variations? (current: {'yes' if variations else 'no'}) [y/n]:")
        vars_choice = input().strip().lower()
        self.set_preference('generate_username_variations', vars_choice in ['y', 'yes'])
        
        # Save configuration
        if self.save_config():
            print("\n✓ Configuration saved successfully!")
            print(f"Config file: {os.path.abspath(self.config_file)}")
        else:
            print("\n✗ Error saving configuration")
        
        # Show summary
        summary = self.get_summary()
        print(f"\nConfiguration Summary:")
        print(f"- API keys configured: {summary['api_keys_configured']}/{summary['total_api_keys']}")
        print(f"- Auto-export: {'Enabled' if summary['auto_export_enabled'] else 'Disabled'}")
        print(f"- Metadata extraction: {'Enabled' if summary['metadata_extraction'] else 'Disabled'}")
        print(f"- Max concurrent requests: {summary['max_concurrent_requests']}")
