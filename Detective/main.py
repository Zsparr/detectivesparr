import asyncio
import sys
import os
from typing import Dict, Any
from colorama import init, Fore, Style
from searcher import SiteChecker
from breach_checker import BreachChecker
from domain_investigator import DomainInvestigator
from ip_analyzer import IPAnalyzer
from email_analyzer import EmailAnalyzer
from export_manager import ExportManager
from config_manager import ConfigManager
from api_manager import APIManager
from batch_processor import BatchProcessor
from advanced_checker import AdvancedChecker
from name_searcher import NameSearcher
from advanced_reporter import AdvancedReporter

# Initialize colorama
init()

def display_menu():
    """Display the main menu and get user choice."""
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}           DETECTIVE - OSINT Toolkit{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}[1]{Style.RESET_ALL} Username Check - Search across social media platforms")
    print(f"{Fore.GREEN}[2]{Style.RESET_ALL} Email & Phone Data Breach Check")
    print(f"{Fore.GREEN}[3]{Style.RESET_ALL} Domain/URL Investigation")
    print(f"{Fore.GREEN}[4]{Style.RESET_ALL} IP Address Analysis")
    print(f"{Fore.GREEN}[5]{Style.RESET_ALL} Email Header Analysis")
    print(f"{Fore.GREEN}[6]{Style.RESET_ALL} Batch Processing")
    print(f"{Fore.GREEN}[7]{Style.RESET_ALL} Configuration & API Management")
    print(f"{Fore.GREEN}[8]{Style.RESET_ALL} Advanced Username Search")
    print(f"{Fore.GREEN}[9]{Style.RESET_ALL} Search by Real Name")
    print(f"{Fore.RED}[0]{Style.RESET_ALL} Exit\n")
    
    while True:
        try:
            choice = input(f"{Fore.YELLOW}Select an option (0-9): {Style.RESET_ALL}").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                return choice
            else:
                print(f"{Fore.RED}Invalid choice. Please enter 0-9.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Exiting...{Style.RESET_ALL}")
            sys.exit(0)

async def username_check():
    """Tool 1: Check username across social media sites."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}           USERNAME CHECK{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    checker = SiteChecker()
    
    username = input(f"{Fore.YELLOW}Enter username to search: {Style.RESET_ALL}").strip()
    
    if not username:
        print(f"{Fore.RED}Username cannot be empty.{Style.RESET_ALL}")
        return
    
    # Ask for variations
    generate_variations = config.get_preference('generate_username_variations', False)
    if not generate_variations:
        variations_choice = input(f"{Fore.YELLOW}Generate username variations? (y/n): {Style.RESET_ALL}").strip().lower()
        generate_variations = variations_choice in ['y', 'yes']
    
    # Ask for metadata extraction
    extract_metadata = config.get_preference('enable_metadata_extraction', True)
    if extract_metadata:
        metadata_choice = input(f"{Fore.YELLOW}Extract profile metadata? (y/n): {Style.RESET_ALL}").strip().lower()
        extract_metadata = metadata_choice in ['y', 'yes']
    
    usernames_to_check = [username]
    if generate_variations:
        variations = checker.generate_username_variations(username)
        max_variations = config.get_investigation_setting('username_variations_count', 10)
        usernames_to_check = variations[:max_variations]
        print(f"{Fore.CYAN}Checking {len(usernames_to_check)} variations...{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}Searching for username: {Style.BRIGHT}{username}{Style.RESET_ALL}\n")

    if not checker.sites:
        print(f"{Fore.RED}No sites loaded. Check sites.json.{Style.RESET_ALL}")
        return

    # Search all variations
    all_results = {}
    for var_username in usernames_to_check:
        print(f"{Fore.CYAN}Checking: {var_username}{Style.RESET_ALL}")
        results = await checker.search_all(var_username, extract_metadata)
        all_results[var_username] = results
    
    # Find best result (most profiles found)
    best_username = max(all_results.keys(), 
                        key=lambda x: len([r for r in all_results[x] if r.get('found')]))
    
    print(f"\n{Fore.CYAN}Best results for: {Style.BRIGHT}{best_username}{Style.RESET_ALL}\n")

    found_count = 0
    show_errors = config.get_preference('show_error_sites', False)
    for res in all_results[best_username]:
        if res["found"]:
            print(f"{Fore.GREEN}[+] Found {res['name']}: {res['url']}{Style.RESET_ALL}")
            if extract_metadata and res.get('metadata'):
                metadata = res['metadata']
                if metadata.get('followers'):
                    print(f"{Fore.CYAN}    Followers: {metadata['followers']}{Style.RESET_ALL}")
                if metadata.get('bio'):
                    bio = metadata['bio'][:100] + '...' if len(metadata['bio']) > 100 else metadata['bio']
                    print(f"{Fore.CYAN}    Bio: {bio}{Style.RESET_ALL}")
            found_count += 1
        elif res["error"] and show_errors:
            print(f"{Fore.YELLOW}[!] Error accessing {res['name']}: {res['error']}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Search complete. Found {found_count} profiles.{Style.RESET_ALL}")
    
    # Export if configured
    if config.get_preference('auto_export', False):
        export_manager = ExportManager()
        try:
            exported_files = export_manager.export_username_report(all_results[best_username], username)
            print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.YELLOW}Export failed: {e}{Style.RESET_ALL}")

async def breach_check():
    """Tool 2: Check email and phone number for data breaches."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}     EMAIL & PHONE DATA BREACH CHECK{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    from breach_checker import BreachChecker
    
    checker = BreachChecker()
    
    print(f"{Fore.CYAN}Enter an email address or phone number to check for data breaches.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Phone format: +1234567890 or (123) 456-7890{Style.RESET_ALL}\n")
    
    user_input = input(f"{Fore.YELLOW}Enter email or phone number: {Style.RESET_ALL}").strip()
    
    if not user_input:
        print(f"{Fore.RED}Input cannot be empty.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Checking for breaches...{Style.RESET_ALL}\n")
    
    # Determine if input is email or phone
    if '@' in user_input:
        # Likely an email
        result = await checker.check_email_breach(user_input)
        checker.format_breach_output(result, "email")
    else:
        # Likely a phone number
        result = await checker.check_phone_breach(user_input)
        checker.format_breach_output(result, "phone")
    
    # Export if configured
    if config.get_preference('auto_export', False):
        export_manager = ExportManager()
        try:
            exported_files = export_manager.export_breach_report(result, user_input)
            print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.YELLOW}Export failed: {e}{Style.RESET_ALL}")

async def domain_investigation():
    """Tool 3: Domain/URL investigation."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        DOMAIN/URL INVESTIGATION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    
    domain = input(f"{Fore.YELLOW}Enter domain or URL to investigate: {Style.RESET_ALL}").strip()
    
    if not domain:
        print(f"{Fore.RED}Domain cannot be empty.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Investigating domain: {Style.BRIGHT}{domain}{Style.RESET_ALL}\n")
    
    try:
        async with DomainInvestigator() as investigator:
            results = await investigator.investigate_domain(domain)
            
            if 'error' in results:
                print(f"{Fore.RED}Error: {results['error']}{Style.RESET_ALL}")
                return
            
            # Display results
            formatted_output = investigator.format_results(results)
            print(formatted_output)
            
            # Export if configured
            if config.get_preference('auto_export', False):
                export_manager = ExportManager()
                try:
                    exported_files = export_manager.export_pdf(results, f"domain_investigation_{domain}.pdf", "Domain Investigation")
                    print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.YELLOW}Export failed: {e}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Investigation failed: {e}{Style.RESET_ALL}")

async def ip_analysis():
    """Tool 4: IP address analysis."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        IP ADDRESS ANALYSIS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    
    ip = input(f"{Fore.YELLOW}Enter IP address to analyze: {Style.RESET_ALL}").strip()
    
    if not ip:
        print(f"{Fore.RED}IP address cannot be empty.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Analyzing IP: {Style.BRIGHT}{ip}{Style.RESET_ALL}\n")
    
    # Get API keys
    vt_api_key = config.get_api_key('virustotal')
    shodan_api_key = config.get_api_key('shodan')
    check_ports = config.get_preference('check_open_ports', False)
    
    if not check_ports:
        ports_choice = input(f"{Fore.YELLOW}Check for open ports? (y/n): {Style.RESET_ALL}").strip().lower()
        check_ports = ports_choice in ['y', 'yes']
    
    try:
        async with IPAnalyzer(config.get_api_key('ipinfo')) as analyzer:
            results = await analyzer.analyze_ip(ip, vt_api_key, shodan_api_key, check_ports)
            
            if 'error' in results:
                print(f"{Fore.RED}Error: {results['error']}{Style.RESET_ALL}")
                return
            
            # Display results
            formatted_output = analyzer.format_results(results)
            print(formatted_output)
            
            # Export if configured
            if config.get_preference('auto_export', False):
                export_manager = ExportManager()
                try:
                    exported_files = export_manager.export_pdf(results, f"ip_analysis_{ip}.pdf", "IP Analysis")
                    print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"\n{Fore.YELLOW}Export failed: {e}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Analysis failed: {e}{Style.RESET_ALL}")

async def email_header_analysis():
    """Tool 5: Email header analysis."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        EMAIL HEADER ANALYSIS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    
    print(f"{Fore.CYAN}Paste email headers below.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Press Enter on an empty line when finished.{Style.RESET_ALL}\n")
    
    headers_lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        headers_lines.append(line)
    
    if not headers_lines:
        print(f"{Fore.RED}No headers provided.{Style.RESET_ALL}")
        return
    
    raw_headers = "\n".join(headers_lines)
    
    print(f"\n{Fore.CYAN}Analyzing email headers...{Style.RESET_ALL}\n")
    
    try:
        analyzer = EmailAnalyzer()
        results = analyzer.analyze_email_headers(raw_headers)
        
        if 'error' in results:
            print(f"{Fore.RED}Error: {results['error']}{Style.RESET_ALL}")
            return
        
        # Display results
        formatted_output = analyzer.format_results(results)
        print(formatted_output)
        
        # Export if configured
        if config.get_preference('auto_export', False):
            export_manager = ExportManager()
            try:
                exported_files = export_manager.export_pdf(results, "email_header_analysis.pdf", "Email Header Analysis")
                print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
            except Exception as e:
                print(f"\n{Fore.YELLOW}Export failed: {e}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Analysis failed: {e}{Style.RESET_ALL}")

async def batch_processing_menu():
    """Tool 6: Batch processing menu."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        BATCH PROCESSING{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}[1]{Style.RESET_ALL} Batch Username Search")
    print(f"{Fore.GREEN}[2]{Style.RESET_ALL} Batch Breach Check")
    print(f"{Fore.GREEN}[3]{Style.RESET_ALL} Batch Domain Investigation")
    print(f"{Fore.GREEN}[4]{Style.RESET_ALL} Batch IP Analysis")
    print(f"{Fore.RED}[0]{Style.RESET_ALL} Return to main menu\n")
    
    choice = input(f"{Fore.YELLOW}Select batch operation (0-4): {Style.RESET_ALL}").strip()
    
    if choice == '0':
        return
    elif choice == '1':
        await batch_username_search()
    elif choice == '2':
        await batch_breach_check()
    elif choice == '3':
        await batch_domain_investigation()
    elif choice == '4':
        await batch_ip_analysis()
    else:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")

async def batch_username_search():
    """Batch username search."""
    print(f"\n{Fore.CYAN}BATCH USERNAME SEARCH{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    processor = BatchProcessor(config)
    
    print(f"{Fore.YELLOW}Enter usernames (one per line), or press Enter to load from file:{Style.RESET_ALL}")
    
    usernames = []
    while True:
        username = input()
        if username.strip() == "":
            break
        usernames.append(username.strip())
    
    if not usernames:
        # Load from file
        filepath = input(f"{Fore.YELLOW}Enter path to file with usernames: {Style.RESET_ALL}").strip()
        try:
            usernames = processor.load_batch_file(filepath)
            print(f"{Fore.GREEN}Loaded {len(usernames)} usernames from file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to load file: {e}{Style.RESET_ALL}")
            return
    
    if not usernames:
        print(f"{Fore.RED}No usernames to process.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Processing {len(usernames)} usernames...{Style.RESET_ALL}")
    
    try:
        results = await processor.batch_username_search(usernames)
        processor.print_batch_summary(results)
        
        # Export results
        exported_files = await processor.export_batch_results(results, 'username_search')
        print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}")

async def batch_breach_check():
    """Batch breach check."""
    print(f"\n{Fore.CYAN}BATCH BREACH CHECK{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    processor = BatchProcessor(config)
    
    print(f"{Fore.YELLOW}Enter emails/phones (one per line), or press Enter to load from file:{Style.RESET_ALL}")
    
    queries = []
    while True:
        query = input()
        if query.strip() == "":
            break
        queries.append(query.strip())
    
    if not queries:
        # Load from file
        filepath = input(f"{Fore.YELLOW}Enter path to file with queries: {Style.RESET_ALL}").strip()
        try:
            queries = processor.load_batch_file(filepath)
            print(f"{Fore.GREEN}Loaded {len(queries)} queries from file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to load file: {e}{Style.RESET_ALL}")
            return
    
    if not queries:
        print(f"{Fore.RED}No queries to process.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Processing {len(queries)} queries...{Style.RESET_ALL}")
    
    try:
        results = await processor.batch_breach_check(queries)
        processor.print_batch_summary(results)
        
        # Export results
        exported_files = await processor.export_batch_results(results, 'breach_check')
        print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}")

async def batch_domain_investigation():
    """Batch domain investigation."""
    print(f"\n{Fore.CYAN}BATCH DOMAIN INVESTIGATION{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    processor = BatchProcessor(config)
    
    print(f"{Fore.YELLOW}Enter domains (one per line), or press Enter to load from file:{Style.RESET_ALL}")
    
    domains = []
    while True:
        domain = input()
        if domain.strip() == "":
            break
        domains.append(domain.strip())
    
    if not domains:
        # Load from file
        filepath = input(f"{Fore.YELLOW}Enter path to file with domains: {Style.RESET_ALL}").strip()
        try:
            domains = processor.load_batch_file(filepath)
            print(f"{Fore.GREEN}Loaded {len(domains)} domains from file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to load file: {e}{Style.RESET_ALL}")
            return
    
    if not domains:
        print(f"{Fore.RED}No domains to process.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Processing {len(domains)} domains...{Style.RESET_ALL}")
    
    try:
        results = await processor.batch_domain_investigation(domains)
        processor.print_batch_summary(results)
        
        # Export results
        exported_files = await processor.export_batch_results(results, 'domain_investigation')
        print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}")

async def batch_ip_analysis():
    """Batch IP analysis."""
    print(f"\n{Fore.CYAN}BATCH IP ANALYSIS{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    processor = BatchProcessor(config)
    
    print(f"{Fore.YELLOW}Enter IP addresses (one per line), or press Enter to load from file:{Style.RESET_ALL}")
    
    ips = []
    while True:
        ip = input()
        if ip.strip() == "":
            break
        ips.append(ip.strip())
    
    if not ips:
        # Load from file
        filepath = input(f"{Fore.YELLOW}Enter path to file with IPs: {Style.RESET_ALL}").strip()
        try:
            ips = processor.load_batch_file(filepath)
            print(f"{Fore.GREEN}Loaded {len(ips)} IPs from file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to load file: {e}{Style.RESET_ALL}")
            return
    
    if not ips:
        print(f"{Fore.RED}No IPs to process.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}Processing {len(ips)} IP addresses...{Style.RESET_ALL}")
    
    try:
        results = await processor.batch_ip_analysis(ips)
        processor.print_batch_summary(results)
        
        # Export results
        exported_files = await processor.export_batch_results(results, 'ip_analysis')
        print(f"\n{Fore.GREEN}Results exported: {', '.join(exported_files.values())}{Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{Fore.RED}Batch processing failed: {e}{Style.RESET_ALL}")

async def configuration_menu():
    """Tool 7: Configuration and API management."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}   CONFIGURATION & API MANAGEMENT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}[1]{Style.RESET_ALL} View Configuration")
    print(f"{Fore.GREEN}[2]{Style.RESET_ALL} API Key Management")
    print(f"{Fore.GREEN}[3]{Style.RESET_ALL} Test API Keys")
    print(f"{Fore.GREEN}[4]{Style.RESET_ALL} Reset Configuration")
    print(f"{Fore.RED}[0]{Style.RESET_ALL} Return to main menu\n")
    
    choice = input(f"{Fore.YELLOW}Select option (0-4): {Style.RESET_ALL}").strip()
    
    if choice == '0':
        return
    elif choice == '1':
        await view_configuration()
    elif choice == '2':
        await api_key_management()
    elif choice == '3':
        await test_api_keys()
    elif choice == '4':
        await reset_configuration()
    else:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")

async def view_configuration():
    """View current configuration."""
    config = ConfigManager()
    summary = config.get_summary()
    
    print(f"\n{Fore.CYAN}CURRENT CONFIGURATION{Style.RESET_ALL}")
    print(f"{'='*40}")
    print(f"Config file: {summary['config_file']}")
    print(f"API keys configured: {summary['api_keys_configured']}/{summary['total_api_keys']}")
    print(f"Auto-export: {'Enabled' if summary['auto_export_enabled'] else 'Disabled'}")
    print(f"Metadata extraction: {'Enabled' if summary['metadata_extraction'] else 'Disabled'}")
    print(f"Tor support: {'Enabled' if summary['tor_enabled'] else 'Disabled'}")
    print(f"Rate limiting: {'Enabled' if summary['rate_limiting'] else 'Disabled'}")
    print(f"Max concurrent requests: {summary['max_concurrent_requests']}")

async def api_key_management():
    """API key management."""
    config = ConfigManager()
    api_manager = APIManager(config)
    
    print(f"\n{Fore.CYAN}API KEY MANAGEMENT{Style.RESET_ALL}")
    api_manager.interactive_api_setup()

async def test_api_keys():
    """Test all API keys."""
    config = ConfigManager()
    api_manager = APIManager(config)
    
    print(f"\n{Fore.CYAN}TESTING API KEYS{Style.RESET_ALL}")
    print(f"{'='*40}")
    
    results = await api_manager.test_all_api_keys()
    
    for service, result in results.items():
        if result['valid']:
            print(f"{Fore.GREEN}✓ {service}: Working{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ {service}: {result.get('error', 'Unknown error')}{Style.RESET_ALL}")

async def reset_configuration():
    """Reset configuration to defaults."""
    print(f"\n{Fore.YELLOW}This will reset all configuration to defaults.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}All API keys and preferences will be lost.{Style.RESET_ALL}")
    
    confirm = input(f"{Fore.YELLOW}Are you sure? (type 'reset' to confirm): {Style.RESET_ALL}").strip().lower()
    
    if confirm == 'reset':
        config = ConfigManager()
        if config.reset_to_defaults():
            print(f"{Fore.GREEN}Configuration reset successfully.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Please restart Detective for initial setup.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Failed to reset configuration.{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}Configuration reset cancelled.{Style.RESET_ALL}")

async def advanced_username_search():
    """Tool 8: Advanced username search with enhanced features."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}        ADVANCED USERNAME SEARCH{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    checker = AdvancedChecker(config)
    reporter = AdvancedReporter()
    
    print(f"{Fore.GREEN}[1]{Style.RESET_ALL} Tag-based Search")
    print(f"{Fore.GREEN}[2]{Style.RESET_ALL} Recursive Username Search")
    print(f"{Fore.GREEN}[3]{Style.RESET_ALL} Batch Tagged Search")
    print(f"{Fore.GREEN}[4]{Style.RESET_ALL} Alt Username Discovery")
    print(f"{Fore.GREEN}[5]{Style.RESET_ALL} Deep Profile Chain")
    print(f"{Fore.GREEN}[6]{Style.RESET_ALL} View Available Tags")
    print(f"{Fore.RED}[0]{Style.RESET_ALL} Return to main menu\n")
    
    choice = input(f"{Fore.YELLOW}Select option (0-6): {Style.RESET_ALL}").strip()
    
    if choice == '0':
        return
    elif choice == '1':
        await tagged_search(checker, reporter)
    elif choice == '2':
        await recursive_search(checker, reporter)
    elif choice == '3':
        await batch_tagged_search(checker, reporter)
    elif choice == '4':
        await alt_discovery(checker, reporter)
    elif choice == '5':
        await deep_profile_chain(checker, reporter)
    elif choice == '6':
        await view_available_tags(checker)
    else:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")

async def tagged_search(checker: AdvancedChecker, reporter: AdvancedReporter):
    """Perform tag-based search."""
    print(f"\n{Fore.CYAN}TAG-BASED SEARCH{Style.RESET_ALL}\n")
    
    username = input(f"{Fore.YELLOW}Enter username: {Style.RESET_ALL}").strip()
    if not username:
        print(f"{Fore.RED}Username cannot be empty.{Style.RESET_ALL}")
        return
    
    # Show available tags
    tag_suggestions = checker.get_tag_suggestions()
    print(f"\n{Fore.CYAN}Available tags:{Style.RESET_ALL}")
    for tag, description in list(tag_suggestions.items())[:10]:  # Show first 10
        print(f"  {Fore.GREEN}{tag}{Style.RESET_ALL}: {description}")
    
    if len(tag_suggestions) > 10:
        print(f"  ... and {len(tag_suggestions) - 10} more tags")
    
    tags_input = input(f"\n{Fore.YELLOW}Enter tags (comma-separated, or press Enter for all): {Style.RESET_ALL}").strip()
    
    tags = []
    if tags_input:
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    
    print(f"\n{Fore.CYAN}Searching for {username} with tags: {', '.join(tags) if tags else 'all'}{Style.RESET_ALL}\n")
    
    try:
        results = await checker.search_with_tags(username, tags, extract_metadata=True)
        
        # Display results
        print(f"\n{Fore.GREEN}Found {len(results['found_profiles'])} profiles{Style.RESET_ALL}")
        
        for profile in results['found_profiles']:
            print(f"{Fore.GREEN}[+] {profile['name']}: {profile['url']}{Style.RESET_ALL}")
            if profile.get('metadata'):
                metadata = profile['metadata']
                if metadata.get('followers'):
                    print(f"{Fore.CYAN}    Followers: {metadata['followers']}{Style.RESET_ALL}")
                if metadata.get('bio'):
                    bio = metadata['bio'][:100] + '...' if len(metadata['bio']) > 100 else metadata['bio']
                    print(f"{Fore.CYAN}    Bio: {bio}{Style.RESET_ALL}")
        
        # Show categories
        if results.get('categories'):
            print(f"\n{Fore.CYAN}Profile categories:{Style.RESET_ALL}")
            for category, sites in results['categories'].items():
                print(f"  {Fore.YELLOW}{category.title()}{Style.RESET_ALL}: {', '.join(sites)}")
        
        # Generate reports
        print(f"\n{Fore.CYAN}Generating reports...{Style.RESET_ALL}")
        html_file = reporter.generate_html_report(results, username)
        json_file = reporter.generate_json_report(results, username)
        csv_file = reporter.generate_csv_summary(results, username)
        
        print(f"\n{Fore.GREEN}Reports generated:{Style.RESET_ALL}")
        print(f"  HTML: {html_file}")
        print(f"  JSON: {json_file}")
        print(f"  CSV: {csv_file}")
        
    except Exception as e:
        print(f"{Fore.RED}Search failed: {e}{Style.RESET_ALL}")

async def recursive_search(checker: AdvancedChecker, reporter: AdvancedReporter):
    """Perform recursive username search."""
    print(f"\n{Fore.CYAN}RECURSIVE USERNAME SEARCH{Style.RESET_ALL}\n")
    
    username = input(f"{Fore.YELLOW}Enter username: {Style.RESET_ALL}").strip()
    if not username:
        print(f"{Fore.RED}Username cannot be empty.{Style.RESET_ALL}")
        return
    
    depth_input = input(f"{Fore.YELLOW}Enter recursion depth (1-3, default=2): {Style.RESET_ALL}").strip()
    try:
        depth = int(depth_input) if depth_input else 2
        depth = max(1, min(3, depth))  # Limit to 1-3
    except ValueError:
        depth = 2
    
    print(f"\n{Fore.CYAN}Starting recursive search for {username} (depth: {depth}){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This may take a while as it searches for additional usernames...{Style.RESET_ALL}\n")
    
    try:
        results = await checker.recursive_search(username, max_depth=depth)
        
        # Display results
        root_results = results['search_tree'][username]
        print(f"\n{Fore.GREEN}Root search: {len(root_results['found_profiles'])} profiles{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Discovered {len(results['discovered_usernames'])} additional usernames:{Style.RESET_ALL}")
        for discovered in list(results['discovered_usernames'])[:10]:  # Show first 10
            print(f"  {Fore.YELLOW}@{discovered}{Style.RESET_ALL}")
        
        if len(results['discovered_usernames']) > 10:
            print(f"  ... and {len(results['discovered_usernames']) - 10} more")
        
        print(f"\n{Fore.GREEN}Total profiles found across all searches: {results['statistics']['total_profiles_found']}{Style.RESET_ALL}")
        
        # Generate report
        html_file = reporter.generate_html_report(results, username)
        json_file = reporter.generate_json_report(results, username)
        
        print(f"\n{Fore.GREEN}Reports generated:{Style.RESET_ALL}")
        print(f"  HTML: {html_file}")
        print(f"  JSON: {json_file}")
        
    except Exception as e:
        print(f"{Fore.RED}Recursive search failed: {e}{Style.RESET_ALL}")

async def batch_tagged_search(checker: AdvancedChecker, reporter: AdvancedReporter):
    """Perform batch tagged search."""
    print(f"\n{Fore.CYAN}BATCH TAGGED SEARCH{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Enter usernames (one per line), or press Enter to load from file:{Style.RESET_ALL}")
    
    usernames = []
    while True:
        username = input()
        if username.strip() == "":
            break
        usernames.append(username.strip())
    
    if not usernames:
        filepath = input(f"{Fore.YELLOW}Enter path to file with usernames: {Style.RESET_ALL}").strip()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}Loaded {len(usernames)} usernames from file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to load file: {e}{Style.RESET_ALL}")
            return
    
    if not usernames:
        print(f"{Fore.RED}No usernames to process.{Style.RESET_ALL}")
        return
    
    # Get tags
    tags_input = input(f"{Fore.YELLOW}Enter tags (comma-separated, or press Enter for all): {Style.RESET_ALL}").strip()
    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
    
    print(f"\n{Fore.CYAN}Processing {len(usernames)} usernames with tags: {', '.join(tags) if tags else 'all'}{Style.RESET_ALL}\n")
    
    try:
        results = await checker.batch_tagged_search(usernames, tags)
        
        # Display summary
        summary = results['summary']
        print(f"\n{Fore.GREEN}Batch Search Summary:{Style.RESET_ALL}")
        print(f"  Total usernames: {summary['total_usernames']}")
        print(f"  Usernames with profiles: {summary['usernames_with_profiles']}")
        print(f"  Total profiles found: {summary['total_profiles_found']}")
        
        # Generate report
        json_file = reporter.generate_json_report(results, f"batch_{len(usernames)}_usernames")
        
        print(f"\n{Fore.GREEN}Batch report generated: {json_file}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Batch search failed: {e}{Style.RESET_ALL}")

async def view_available_tags(checker: AdvancedChecker):
    """View available tags with descriptions."""
    print(f"\n{Fore.CYAN}AVAILABLE TAGS{Style.RESET_ALL}\n")
    
    tag_suggestions = checker.get_tag_suggestions()
    
    for tag, description in tag_suggestions.items():
        print(f"{Fore.GREEN}{tag}{Style.RESET_ALL}: {description}")
    
    print(f"\n{Fore.CYAN}Total: {len(tag_suggestions)} tag categories available{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Use these tags in the Tag-based Search to filter sites by category.{Style.RESET_ALL}\n")


async def alt_discovery(checker: AdvancedChecker, reporter: AdvancedReporter):
    """Discover alternative usernames using advanced pattern analysis."""
    print(f"\n{Fore.CYAN}ALT USERNAME DISCOVERY{Style.RESET_ALL}\n")
    
    username = input(f"{Fore.YELLOW}Enter username: {Style.RESET_ALL}").strip()
    if not username:
        print(f"{Fore.RED}Username cannot be empty.{Style.RESET_ALL}")
        return
    
    max_variations_input = input(f"{Fore.YELLOW}Max variations to test (default=50): {Style.RESET_ALL}").strip()
    try:
        max_variations = int(max_variations_input) if max_variations_input else 50
        max_variations = max(10, min(200, max_variations))  # Limit between 10-200
    except ValueError:
        max_variations = 50
    
    print(f"\n{Fore.CYAN}Discovering alternative usernames for {username}...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This will test up to {max_variations} variations across major platforms.{Style.RESET_ALL}\n")
    
    try:
        from username_chainer import UsernameChainer
        chainer = UsernameChainer(checker.config)
        
        results = await chainer.discover_alt_usernames(username, max_variations)
        
        # Display results
        print(f"\n{Fore.GREEN}ALT DISCOVERY RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Original Username: {results['original_username']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total Variations Generated: {results['total_variations']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Found Alternative Accounts: {len(results['found_alts'])}{Style.RESET_ALL}\n")
        
        # Show variation categories
        print(f"{Fore.YELLOW}Variation Categories Generated:{Style.RESET_ALL}")
        for category, count in results['variation_categories'].items():
            print(f"  {Fore.GREEN}{category.replace('_', ' ').title()}{Style.RESET_ALL}: {count}")
        print()
        
        # Show found alts
        if results['found_alts']:
            print(f"{Fore.GREEN}FOUND ALTERNATIVE ACCOUNTS:{Style.RESET_ALL}\n")
            
            for i, alt in enumerate(results['found_alts'][:10], 1):  # Show top 10
                confidence_color = Fore.GREEN if alt['confidence'] > 0.7 else Fore.YELLOW if alt['confidence'] > 0.5 else Fore.RED
                
                print(f"{i}. {confidence_color}{alt['username']}{Style.RESET_ALL} (Confidence: {alt['confidence']:.2f})")
                
                for profile in alt['profiles']:
                    platform_color = Fore.BLUE
                    print(f"   {platform_color}► {profile['name']}: {profile['url']}{Style.RESET_ALL}")
                
                print()
            
            if len(results['found_alts']) > 10:
                print(f"{Fore.CYAN}... and {len(results['found_alts']) - 10} more alternative accounts{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}No alternative accounts found with high confidence.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Try increasing the variation limit or check if the username has common patterns.{Style.RESET_ALL}\n")
        
        # Generate report
        if results['found_alts']:
            html_file = reporter.generate_html_report(results, username)
            json_file = reporter.generate_json_report(results, username)
            
            print(f"{Fore.GREEN}Reports generated:{Style.RESET_ALL}")
            print(f"  HTML: {html_file}")
            print(f"  JSON: {json_file}")
        
    except Exception as e:
        print(f"{Fore.RED}Alt discovery failed: {e}{Style.RESET_ALL}")


async def deep_profile_chain(checker: AdvancedChecker, reporter: AdvancedReporter):
    """Perform deep profile chaining across all data sources."""
    print(f"\n{Fore.CYAN}DEEP PROFILE CHAIN{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}This feature chains across ALL data sources to build a complete profile.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}It will search usernames, emails, IPs, domains, and breach data.{Style.RESET_ALL}\n")
    
    # Get input type and value
    print(f"{Fore.GREEN}What do you want to search?{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[1]{Style.RESET_ALL} Username")
    print(f"{Fore.GREEN}[2]{Style.RESET_ALL} Email Address")
    print(f"{Fore.GREEN}[3]{Style.RESET_ALL} IP Address")
    print(f"{Fore.GREEN}[4]{Style.RESET_ALL} Domain Name")
    
    input_choice = input(f"\n{Fore.YELLOW}Select input type (1-4): {Style.RESET_ALL}").strip()
    
    input_type_map = {
        '1': 'username',
        '2': 'email', 
        '3': 'ip',
        '4': 'domain'
    }
    
    if input_choice not in input_type_map:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")
        return
    
    input_type = input_type_map[input_choice]
    
    input_value = input(f"{Fore.YELLOW}Enter {input_type}: {Style.RESET_ALL}").strip()
    if not input_value:
        print(f"{Fore.RED}{input_type.title()} cannot be empty.{Style.RESET_ALL}")
        return
    
    # Get chain depth
    depth_input = input(f"{Fore.YELLOW}Chain depth (1-3, default=2): {Style.RESET_ALL}").strip()
    try:
        depth = int(depth_input) if depth_input else 2
        depth = max(1, min(3, depth))
    except ValueError:
        depth = 2
    
    print(f"\n{Fore.CYAN}Starting Deep Profile Chain for {input_type}: {input_value}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Chain depth: {depth} - This may take several minutes...{Style.RESET_ALL}\n")
    
    try:
        from deep_profile_chainer import DeepProfileChainer
        chainer = DeepProfileChainer(checker.config)
        
        # Set chain depth
        chainer.max_chain_depth = depth
        
        results = await chainer.deep_profile_chain(input_value, input_type)
        
        # Display comprehensive results
        print(f"\n{Fore.GREEN}DEEP PROFILE CHAIN RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}SUMMARY:{Style.RESET_ALL}")
        print(f"  Initial Input: {results['initial_input']}")
        print(f"  Duration: {results['duration_seconds']:.1f} seconds")
        print(f"  Total Profiles Discovered: {results['total_profiles_discovered']}")
        print(f"  High Confidence Profiles: {results['high_confidence_profiles']}")
        
        summary = results['summary']
        print(f"\n{Fore.YELLOW}DISCOVERED DATA:{Style.RESET_ALL}")
        print(f"  Usernames: {len(summary['usernames'])}")
        print(f"  Emails: {len(summary['emails'])}")
        print(f"  IPs: {len(summary['ips'])}")
        print(f"  Domains: {len(summary['domains'])}")
        print(f"  Social Profiles: {summary['social_profiles_found']}")
        print(f"  Breach Entries: {summary['breach_entries_found']}")
        
        # Show discovered usernames
        if summary['usernames']:
            print(f"\n{Fore.GREEN}DISCOVERED USERNAMES:{Style.RESET_ALL}")
            for username in summary['usernames'][:10]:
                if username:  # Skip empty strings
                    print(f"  {Fore.CYAN}@{username}{Style.RESET_ALL}")
            if len(summary['usernames']) > 10:
                print(f"  ... and {len(summary['usernames']) - 10} more")
        
        # Show discovered emails
        if summary['emails']:
            print(f"\n{Fore.GREEN}DISCOVERED EMAILS:{Style.RESET_ALL}")
            for email in summary['emails'][:10]:
                print(f"  {Fore.CYAN}{email}{Style.RESET_ALL}")
            if len(summary['emails']) > 10:
                print(f"  ... and {len(summary['emails']) - 10} more")
        
        # Show discovered domains
        if summary['domains']:
            print(f"\n{Fore.GREEN}DISCOVERED DOMAINS:{Style.RESET_ALL}")
            for domain in summary['domains'][:10]:
                print(f"  {Fore.CYAN}{domain}{Style.RESET_ALL}")
            if len(summary['domains']) > 10:
                print(f"  ... and {len(summary['domains']) - 10} more")
        
        # Show chain connections
        connections = results['chain_connections']
        if connections:
            print(f"\n{Fore.GREEN}CHAIN CONNECTIONS:{Style.RESET_ALL}")
            for profile_id, profile_connections in list(connections.items())[:5]:
                print(f"  {Fore.CYAN}{profile_id}:{Style.RESET_ALL}")
                for connection in profile_connections[:3]:
                    print(f"    {Fore.YELLOW}→ {connection}{Style.RESET_ALL}")
                if len(profile_connections) > 3:
                    print(f"    ... and {len(profile_connections) - 3} more connections")
        
        # Show recommendations
        recommendations = results['recommendations']
        if recommendations:
            print(f"\n{Fore.GREEN}INVESTIGATION RECOMMENDATIONS:{Style.RESET_ALL}")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {Fore.YELLOW}{rec}{Style.RESET_ALL}")
        
        # Generate reports
        html_file = reporter.generate_html_report(results, input_value)
        json_file = reporter.generate_json_report(results, input_value)
        
        print(f"\n{Fore.GREEN}COMPREHENSIVE REPORTS GENERATED:{Style.RESET_ALL}")
        print(f"  HTML: {html_file}")
        print(f"  JSON: {json_file}")
        
        print(f"\n{Fore.CYAN}Deep Profile Chain completed successfully!{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Deep Profile Chain failed: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


async def name_search():
    """Tool 9: Search for profiles using real names."""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}           SEARCH BY REAL NAME{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    config = ConfigManager()
    searcher = NameSearcher(config)
    
    # Get the person's name
    full_name = input(f"{Fore.YELLOW}Enter full name (First Last): {Style.RESET_ALL}").strip()
    
    if not full_name:
        print(f"{Fore.RED}Name cannot be empty.{Style.RESET_ALL}")
        return
    
    # Validate name format
    if len(full_name.split()) < 2:
        print(f"{Fore.RED}Please enter both first and last name.{Style.RESET_ALL}")
        return
    
    # Get search preferences
    max_variations = 20
    try:
        variations_input = input(f"{Fore.YELLOW}Max username variations to test (default=20): {Style.RESET_ALL}").strip()
        if variations_input:
            max_variations = min(int(variations_input), 50)  # Cap at 50 for performance
    except ValueError:
        print(f"{Fore.YELLOW}Using default of 20 variations{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Searching for profiles related to: {Style.BRIGHT}{full_name}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This will test up to {max_variations} username variations...{Style.RESET_ALL}\n")
    
    try:
        # Perform the search
        results = await searcher.search_by_name(full_name, max_variations)
        
        if 'error' in results:
            print(f"{Fore.RED}Error: {results['error']}{Style.RESET_ALL}")
            return
        
        # Display results
        print(f"\n{Fore.GREEN}NAME SEARCH RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}SEARCH SUMMARY:{Style.RESET_ALL}")
        print(f"  Searched Name: {results['search_name']}")
        print(f"  Username Variations Tested: {results['username_variations_tested']}")
        print(f"  Total Profiles Found: {results['total_profiles_found']}")
        print(f"  High-Confidence Matches: {len(results['high_confidence_matches'])}")
        
        # Show ALL found profiles (not just high confidence)
        if results['found_profiles']:
            print(f"\n{Fore.GREEN}ALL FOUND PROFILES (sorted by name match confidence):{Style.RESET_ALL}")
            for i, profile in enumerate(results['found_profiles'][:15]):  # Show top 15
                username = profile['username']
                platform = profile['platform']
                url = profile['url']
                display_name = profile['display_name']
                confidence = profile['name_confidence']
                bio = profile.get('bio', '')
                
                # Color code by confidence
                if confidence >= 0.7:
                    confidence_color = Fore.GREEN
                elif confidence >= 0.4:
                    confidence_color = Fore.YELLOW
                else:
                    confidence_color = Fore.RED
                
                print(f"\n  {Fore.CYAN}[{i+1}] {Style.BRIGHT}@{username}{Style.RESET_ALL} on {platform}")
                print(f"    {confidence_color}Name Match: {confidence:.2f}{Style.RESET_ALL}")
                if display_name:
                    print(f"    Display Name: {display_name}")
                if bio and len(bio) > 0:
                    bio_preview = bio[:100] + "..." if len(bio) > 100 else bio
                    print(f"    Bio: {bio_preview}")
                print(f"    URL: {url}")
            
            if len(results['found_profiles']) > 15:
                print(f"\n  ... and {len(results['found_profiles']) - 15} more profiles")
        
        # Show high confidence matches separately
        if results['high_confidence_matches']:
            print(f"\n{Fore.GREEN}HIGH CONFIDENCE MATCHES:{Style.RESET_ALL}")
            for result in results['high_confidence_matches'][:5]:
                username = result['username']
                confidence = result['confidence']
                profiles = result['profiles']
                
                print(f"\n  {Fore.YELLOW}@{username}{Style.RESET_ALL} (Overall Confidence: {confidence:.2f})")
                for profile in profiles:
                    platform = profile.get('name', 'Unknown')
                    url = profile.get('url', '')
                    print(f"    {Fore.CYAN}• {platform}: {Style.RESET_ALL}{url}")
        
        # Show name variations
        if results.get('name_variations'):
            print(f"\n{Fore.YELLOW}NAME VARIATIONS TO CONSIDER:{Style.RESET_ALL}")
            for variation in results['name_variations'][:8]:
                print(f"  {Fore.CYAN}{variation}{Style.RESET_ALL}")
        
        # Show recommendations
        if results.get('recommendations'):
            print(f"\n{Fore.YELLOW}INVESTIGATION RECOMMENDATIONS:{Style.RESET_ALL}")
            for rec in results['recommendations']:
                print(f"  • {rec}")
        
        # Export option
        if results['found_profiles']:
            export_choice = input(f"\n{Fore.YELLOW}Export results to file? (y/n): {Style.RESET_ALL}").strip().lower()
            if export_choice in ['y', 'yes']:
                await _export_name_results(results, full_name)
    
    except Exception as e:
        print(f"{Fore.RED}Error during name search: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

async def _export_name_results(results: Dict[str, Any], search_name: str):
    """Export name search results to file."""
    try:
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/name_search_{search_name.replace(' ', '_')}_{timestamp}.json"
        
        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}Results exported to: {filename}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Failed to export results: {e}{Style.RESET_ALL}")


async def main():
    """Main entry point with menu system."""
    config = ConfigManager()
    
    # First-time setup
    if not os.path.exists('config.json'):
        print(f"{Fore.CYAN}Welcome to Detective! Let's set up your configuration.{Style.RESET_ALL}")
        config.interactive_setup()
        print(f"\n{Fore.GREEN}Setup complete! Starting main menu...{Style.RESET_ALL}\n")
    
    while True:
        choice = display_menu()
        
        if choice == '0':
            print(f"{Fore.CYAN}Thank you for using Detective!{Style.RESET_ALL}")
            break
        elif choice == '1':
            await username_check()
        elif choice == '2':
            await breach_check()
        elif choice == '3':
            await domain_investigation()
        elif choice == '4':
            await ip_analysis()
        elif choice == '5':
            await email_header_analysis()
        elif choice == '6':
            await batch_processing_menu()
        elif choice == '7':
            await configuration_menu()
        elif choice == '8':
            await advanced_username_search()
        elif choice == '9':
            await name_search()
        
        # Ask if user wants to continue
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        continue_choice = input(f"{Fore.YELLOW}Return to main menu? (y/n): {Style.RESET_ALL}").strip().lower()
        if continue_choice not in ['y', 'yes', '']:
            print(f"{Fore.CYAN}Thank you for using Detective!{Style.RESET_ALL}")
            break
        print()  # Add spacing before returning to menu

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Exiting...{Style.RESET_ALL}")
        sys.exit(0)
