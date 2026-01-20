import aiohttp
import asyncio
import re
from typing import Dict, Any, Optional
from colorama import Fore, Style

class BreachChecker:
    """Check if email addresses or phone numbers have been exposed in data breaches."""
    
    def __init__(self):
        self.api_base_url = "https://api.xposedornot.com/v1"
        # Email regex pattern (basic validation)
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        # Phone number pattern (E.164 format: +1234567890)
        self.phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
    async def check_leakcheck_breach(self, email: str) -> Dict[str, Any]:
        """
        Check if an email has been exposed using the LeakCheck public API.
        
        Args:
            email: Email address to check
            
        Returns:
            Dictionary with breach information
        """
        url = f"https://leakcheck.io/api/public?check={email}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10, ssl=False) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("success") and data.get("found", 0) > 0:
                            breaches = []
                            for source in data.get("sources", []):
                                breaches.append({
                                    "breach": source.get("name", "Unknown"),
                                    "xposed_date": source.get("date", "Unknown"),
                                    "xposed_data": ", ".join(data.get("fields", []))
                                })
                            return {"found": True, "breaches": breaches}
        except:
            pass
        return {"found": False, "breaches": []}

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(self.email_pattern.match(email))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate and normalize phone number format."""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        return bool(self.phone_pattern.match(cleaned))
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        return cleaned
    
    async def check_email_breach(self, email: str) -> Dict[str, Any]:
        """
        Check if an email has been exposed in data breaches.
        
        Args:
            email: Email address to check
            
        Returns:
            Dictionary with breach information
        """
        result = {
            "email": email,
            "found": False,
            "breach_count": 0,
            "breaches": [],
            "error": None
        }
        
        if not self.validate_email(email):
            result["error"] = "Invalid email format"
            return result
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. First, use XposedOrNot "Public" check-email endpoint
                check_url = f"{self.api_base_url}/check-email/{email}"
                found_breach_names = []
                
                async with session.get(check_url, headers=headers, timeout=10, ssl=False) as resp:
                    if resp.status == 200:
                        check_data = await resp.json()
                        if check_data and "breaches" in check_data:
                            breaches_list = check_data["breaches"]
                            if breaches_list and isinstance(breaches_list, list) and len(breaches_list) > 0:
                                found_breach_names = breaches_list[0]

                # 2. Then, try XposedOrNot detailed analytics
                analytics_url = f"{self.api_base_url}/breach-analytics"
                params = {"email": email}
                
                async with session.get(analytics_url, headers=headers, params=params, timeout=15, ssl=False) as resp:
                    if resp.status == 200:
                        analytics_data = await resp.json()
                        if analytics_data and isinstance(analytics_data, dict):
                            exposed = analytics_data.get("ExposedBreaches", {})
                            if isinstance(exposed, dict):
                                details = exposed.get("breaches_details", [])
                                if details:
                                    result["found"] = True
                                    result["breaches"].extend(details)

                # 3. Use LeakCheck as secondary source for better coverage
                leakcheck_res = await self.check_leakcheck_breach(email)
                if leakcheck_res["found"]:
                    result["found"] = True
                    result["breaches"].extend(leakcheck_res["breaches"])

                # 4. Merging and Deduplication
                if found_breach_names or result["breaches"]:
                    merged_breaches = []
                    seen_names = set()
                    
                    # Sort result["breaches"] to prioritize entries with more detail (data/date)
                    for b in result["breaches"]:
                        name = b.get("breach", "").lower()
                        if name and name not in seen_names:
                            merged_breaches.append(b)
                            seen_names.add(name)
                    
                    # Add names from found_breach_names that were not found in either analytics or leakcheck
                    for name in found_breach_names:
                        if name.lower() not in seen_names:
                            merged_breaches.append({
                                "breach": name, 
                                "xposed_data": "Unknown (Found via discovery API)", 
                                "xposed_date": "Unknown"
                            })
                            seen_names.add(name.lower())
                            result["found"] = True
                    
                    result["breaches"] = merged_breaches
                    result["breach_count"] = len(merged_breaches)
                    if merged_breaches:
                        result["found"] = True

                # Handle case where both might return 404 or other errors
                # But if we already found something, we don't care about a 404 on the other call
                
        except asyncio.TimeoutError:
            if not result["found"]:
                result["error"] = "Request timed out. Please check your internet connection."
        except aiohttp.ClientError as e:
            if not result["found"]:
                result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            if not result["found"]:
                result["error"] = f"Unexpected error while parsing response: {str(e)}"
        
        return result
    
    async def check_phone_breach(self, phone: str) -> Dict[str, Any]:
        """
        Check if a phone number has been exposed in data breaches.
        
        Note: Phone number breach checking may not be supported by all APIs.
        
        Args:
            phone: Phone number to check
            
        Returns:
            Dictionary with breach information
        """
        result = {
            "phone": phone,
            "found": False,
            "breach_count": 0,
            "breaches": [],
            "error": None
        }
        
        if not self.validate_phone(phone):
            result["error"] = "Invalid phone number format. Use format: +1234567890"
            return result
        
        normalized_phone = self.normalize_phone(phone)
        
        # XposedOrNot primarily focuses on emails
        # Phone number checking may not be available
        result["error"] = "Phone number breach checking is not currently supported by this service. Please use an email address instead."
        
        return result
    
    def format_breach_output(self, result: Dict[str, Any], input_type: str = "email") -> None:
        """
        Format and print breach check results with color coding.
        
        Args:
            result: Breach check result dictionary
            input_type: Type of input ("email" or "phone")
        """
        identifier = result.get("email") or result.get("phone")
        
        if result.get("error"):
            print(f"{Fore.YELLOW}[!] Error: {result['error']}{Style.RESET_ALL}")
            return
        
        if result["found"]:
            print(f"\n{Fore.RED}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.RED}[!] BREACH ALERT: {identifier} has been exposed!{Style.RESET_ALL}")
            print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
            
            print(f"{Fore.YELLOW}Total breaches found: {result['breach_count']}{Style.RESET_ALL}\n")
            
            # Known breach URLs for manual overrides
            KNOWN_BREACH_URLS = {
                "stealer logs": "https://haveibeenpwned.com/PwnedWebsites#StealerLogs",
                "collection #1": "https://haveibeenpwned.com/PwnedWebsites#Collection1",
                "verifications.io": "https://haveibeenpwned.com/PwnedWebsites#VerificationsIO",
            }

            # Display breach details
            for i, breach in enumerate(result["breaches"], 1):
                if isinstance(breach, dict):
                    breach_name = breach.get("breach", breach.get("name", "Unknown"))
                    breach_date = breach.get("xposed_date", breach.get("breachdate", breach.get("date", "Unknown")))
                    exposed_data = breach.get("xposed_data", breach.get("exposeddata", breach.get("data", [])))
                    references = breach.get("references", breach.get("reference", ""))
                    
                    print(f"{Fore.RED}[{i}] {breach_name}{Style.RESET_ALL}")
                    print(f"    Date: {breach_date}")
                    
                    if exposed_data:
                        if isinstance(exposed_data, list):
                            print(f"    Exposed data: {', '.join(exposed_data)}")
                        else:
                            print(f"    Exposed data: {exposed_data}")
                    
                    # Determine the best link to show
                    link_to_show = ""
                    if references:
                        link_to_show = references
                    
                    # Check manual overrides (case-insensitive)
                    if not link_to_show:
                        lower_name = breach_name.lower()
                        # Check exact match or partial match for specific cases
                        for key, url in KNOWN_BREACH_URLS.items():
                            if key in lower_name:
                                link_to_show = url
                                break
                    
                    # Fallback to HaveIBeenPwned
                    if not link_to_show:
                        # HIBP uses PascalCase usually, but the anchor might vary. 
                        # This is a best-effort guess.
                        clean_name = re.sub(r'[^a-zA-Z0-9]', '', breach_name)
                        link_to_show = f"https://haveibeenpwned.com/PwnedWebsites#{clean_name}"

                    # Final fallback (though HIBP link is always generated above, we can check if it's "Stealer Logs" for a specific message)
                    if "stealer logs" in breach_name.lower():
                        print(f"    {Fore.YELLOW}Note: This is malware that steals credentials from infected devices.{Style.RESET_ALL}")
                    
                    print(f"    More Info: {link_to_show}")

                    print()
                else:
                    print(f"{Fore.RED}[{i}] {breach}{Style.RESET_ALL}")
                    # Simple string case
                    clean_name = re.sub(r'[^a-zA-Z0-9]', '', str(breach))
                    link_to_show = f"https://haveibeenpwned.com/PwnedWebsites#{clean_name}"
                     
                    if "stealer logs" in str(breach).lower():
                         print(f"    {Fore.YELLOW}Note: This is malware that steals credentials from infected devices.{Style.RESET_ALL}")
                         link_to_show = "https://haveibeenpwned.com/PwnedWebsites#StealerLogs"

                    print(f"    More Info: {link_to_show}\n")
            
            print(f"{Fore.YELLOW}[!] Recommendation: Change passwords and enable 2FA on affected accounts.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[i] Verify detailed report: https://haveibeenpwned.com/account/{identifier}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[+] Good news! {identifier} was not found in any known breaches.{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
            print(f"{Fore.CYAN}Note: This doesn't guarantee complete safety. Always use strong, unique passwords.{Style.RESET_ALL}")
