import aiohttp
import asyncio
import json
import logging
from typing import List, Dict, Any

class SiteChecker:
    def __init__(self, sites_file: str = "sites.json"):
        self.sites_file = sites_file
        self.sites = self.load_sites()

    def load_sites(self) -> List[Dict[str, Any]]:
        try:
            with open(self.sites_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.sites_file} not found.")
            return []
        except json.JSONDecodeError:
            print(f"Error: Failed to decode {self.sites_file}.")
            return []

    async def check_site(self, session: aiohttp.ClientSession, site: Dict[str, Any], username: str) -> Dict[str, Any]:
        url = site["url"].format(username)
        # Use probe_url if available for the actual check
        check_url = site.get("probe_url", site["url"]).format(username)
        result = {
            "name": site["name"],
            "url": url,
            "found": False,
            "status": "Unknown",
            "error": None
        }

        # Some sites require a User-Agent to return correct content
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Override headers if site config specifies them (e.g. YouTube needs Googlebot)
        if "headers" in site:
            headers.update(site["headers"])

        try:
            # We disable ssl verification for simplicity as some sites (like Spotify in this env) might fail
            async with session.get(check_url, headers=headers, timeout=10, ssl=False) as response:
                result["status"] = response.status
                if site["check_type"] == "status_code":
                    if response.status == site.get("expected_status", 200):
                        result["found"] = True
                elif site["check_type"] == "message":
                    if response.status == site.get("expected_status", 200):
                        text = await response.text()
                        if site["error_msg"] not in text:
                            # If the error message is NOT in the text, then we found the profile...
                            # But wait, for SPA sites, we might get a generic page.
                            # Let's check if we require the username to be present.
                            if site.get("username_must_be_in_content", False):
                                if username in text:
                                    result["found"] = True
                                else:
                                    result["found"] = False
                            else:
                                result["found"] = True
                        else:
                            result["found"] = False
        except Exception as e:
            result["error"] = str(e)
            result["status"] = "Error"
        
        return result

    async def search_all(self, username: str) -> List[Dict[str, Any]]:
        results = []
        # Using a single session is efficient
        connector = aiohttp.TCPConnector(limit=50, ssl=False) # Global SSL disable for this tool
        # Increase max_field_size to handle large headers (e.g. from Twitter)
        # Note: max_field_size is supported in ClientSession in recent aiohttp versions or via other means.
        # If this fails on older aiohttp, we might need a try-except or check version. 
        # Assuming modern environment.
        async with aiohttp.ClientSession(connector=connector, max_field_size=16384) as session:
            tasks = []
            for site in self.sites:
                tasks.append(self.check_site(session, site, username))
            results = await asyncio.gather(*tasks)
        return results
