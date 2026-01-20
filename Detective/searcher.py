import aiohttp
import asyncio
import json
import logging
import re
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from config_manager import ConfigManager
from enhanced_metadata_extractor import EnhancedMetadataExtractor
from advanced_integration import AdvancedIntegration

class SiteChecker:
    def __init__(self, sites_file: str = "sites.json", config: Optional[ConfigManager] = None):
        self.sites_file = sites_file
        self.config = config or ConfigManager()
        self.metadata_cache = {}
        self.enhanced_extractor = EnhancedMetadataExtractor()
        self.advanced = AdvancedIntegration(sites_file)
        self.sites = self.load_sites()

    def load_sites(self) -> List[Dict[str, Any]]:
        """Load site lists from primary and optional extra sources, de-duplicated by name."""
        # Determine site sources based on preference
        if self.config.get('preferences.use_extended_sites', True):
            site_sources = self.config.get('site_sources', [self.sites_file, 'sites_extra.json', 'sites_extended.json', 'sites_advanced.json'])
        else:
            # Only use reliable sources when extended sites are disabled
            site_sources = [self.sites_file]
            if 'sites_extra.json' in self.config.get('site_sources', []):
                site_sources.append('sites_extra.json')
        
        sites: List[Dict[str, Any]] = []
        seen_names = set()

        for source in site_sources:
            if not source:
                continue
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        continue
                    for entry in data:
                        name = entry.get('name')
                        if not name or name in seen_names:
                            continue
                        seen_names.add(name)
                        sites.append(entry)
            except FileNotFoundError:
                # Optional sources may not exist
                continue
            except json.JSONDecodeError:
                print(f"Error: Failed to decode {source}.")
                continue

        # Randomize order if desired to spread load
        if self.config.get('preferences.randomize_site_order', False):
            random.shuffle(sites)

        max_sites = self.config.get('preferences.max_sites_to_check', 0)
        if isinstance(max_sites, int) and max_sites > 0:
            sites = sites[:max_sites]

        return sites

    async def check_site(self, session: aiohttp.ClientSession, site: Dict[str, Any], username: str, extract_metadata: bool = False, timeout: int = 10, retry_attempts: int = 2) -> Dict[str, Any]:
        url = site["url"].format(username)
        # Use probe_url if available for the actual check
        check_url = site.get("probe_url", site["url"]).format(username)
        result = {
            "name": site["name"],
            "url": url,
            "found": False,
            "status": "Unknown",
            "error": None,
            "metadata": {}
        }

        # Some sites require a User-Agent to return correct content
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Override headers if site config specifies them (e.g. YouTube needs Googlebot)
        if "headers" in site:
            headers.update(site["headers"])

        start_time = asyncio.get_event_loop().time()
        last_error = None

        for attempt in range(max(1, retry_attempts)):
            try:
                # We disable ssl verification for simplicity as some sites (like Spotify in this env) might fail
                async with session.get(check_url, headers=headers, timeout=timeout, ssl=False) as response:
                    result["status"] = response.status
                    if site["check_type"] == "status_code":
                        if response.status == site.get("expected_status", 200):
                            require_content = site.get("username_must_be_in_content", True)
                            if require_content:
                                try:
                                    text = await response.text()
                                    result["found"] = username.lower() in text.lower()
                                except Exception:
                                    result["found"] = False
                            else:
                                result["found"] = True
                    elif site["check_type"] == "message":
                        if response.status == site.get("expected_status", 200):
                            text = await response.text()
                            if site["error_msg"] not in text:
                                # If the error message is NOT in the text, then we found the profile...
                                # But wait, for SPA sites, we might get a generic page.
                                # Let's check if we require the username to be present.
                                require_content = site.get("username_must_be_in_content", True)
                                if require_content:
                                    result["found"] = username.lower() in text.lower()
                                else:
                                    result["found"] = True
                            else:
                                result["found"] = False

                    # Extract metadata if found and requested
                    if result["found"] and extract_metadata:
                        try:
                            content = await response.text()
                            result["metadata"] = await self.enhanced_extractor.extract_metadata(content, site["name"], check_url)
                            
                            # Add captcha/censorship detection
                            blocking_detection = self.advanced.detect_captcha_or_censorship(content, response.status)
                            if blocking_detection['is_blocked']:
                                result['blocking_detected'] = blocking_detection['detected']
                                result['found'] = False  # Mark as not found if blocked
                                
                        except Exception as e:
                            result["metadata"] = {"error": f"Metadata extraction failed: {str(e)}"}
                    break
            except Exception as e:
                last_error = str(e)
                result["status"] = "Error"
                if attempt < max(1, retry_attempts) - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    result["error"] = last_error

        result["elapsed_ms"] = int((asyncio.get_event_loop().time() - start_time) * 1000)
        return result

    async def search_all(self, username: str, extract_metadata: bool = False) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        timeout = self.config.get('preferences.request_timeout', 10)
        retry_attempts = self.config.get('preferences.retry_attempts', 2)
        concurrency_limit = self.config.get('preferences.concurrency_limit', 50)

        connector = aiohttp.TCPConnector(limit=concurrency_limit, ssl=False)
        sem = asyncio.Semaphore(concurrency_limit)

        async with aiohttp.ClientSession(connector=connector, max_field_size=16384) as session:
            async def bounded_check(site):
                async with sem:
                    return await self.check_site(session, site, username, extract_metadata, timeout=timeout, retry_attempts=retry_attempts)

            tasks = [bounded_check(site) for site in self.sites]
            results = await asyncio.gather(*tasks)
        return results
    
    def generate_username_variations(self, username: str) -> List[str]:
        """Generate common username variations."""
        variations = [username]  # Start with original
        
        # Remove common separators
        clean_username = re.sub(r'[._-]', '', username)
        if clean_username != username:
            variations.append(clean_username)
        
        # Add common separators
        separators = ['.', '_', '-']
        for sep in separators:
            # Insert separator between words (camelCase detection)
            camel_parts = re.findall(r'[A-Z][a-z]*|[a-z]+', username)
            if len(camel_parts) > 1:
                variations.append(sep.join(camel_parts))
                variations.append(sep.join(camel_parts).lower())
        
        # Common prefixes/suffixes
        prefixes = ['the', 'real', 'official']
        suffixes = ['official', 'real', 'verified', '123']
        
        for prefix in prefixes:
            variations.append(prefix + username)
            variations.append(prefix + '_' + username)
        
        for suffix in suffixes:
            variations.append(username + suffix)
            variations.append(username + '_' + suffix)
        
        # Number variations
        variations.append(username + '1')
        variations.append(username + '01')
        variations.append(username + '123')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            if var not in seen and len(var) > 0:
                seen.add(var)
                unique_variations.append(var)
        
        return unique_variations
    
    def get_available_tags(self) -> Dict[str, int]:
        """Get available tags with site counts."""
        return self.advanced.get_available_tags()
    
    def get_sites_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get sites that match specified tags."""
        return self.advanced.get_sites_by_tags(tags)
    
    async def extract_metadata(self, html_content: str, site_name: str, url: str) -> Dict[str, Any]:
        """Extract metadata from profile pages."""
        metadata = {
            'site_name': site_name,
            'profile_url': url,
            'extraction_time': asyncio.get_event_loop().time()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            if soup.title:
                metadata['title'] = soup.title.string.strip()
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata['description'] = meta_desc['content'].strip()
            
            # Site-specific extractions
            if 'twitter' in site_name.lower() or 'x.com' in url:
                metadata.update(self.extract_twitter_metadata(soup))
            elif 'instagram' in site_name.lower():
                metadata.update(self.extract_instagram_metadata(soup))
            elif 'linkedin' in site_name.lower():
                metadata.update(self.extract_linkedin_metadata(soup))
            elif 'facebook' in site_name.lower():
                metadata.update(self.extract_facebook_metadata(soup))
            elif 'youtube' in site_name.lower():
                metadata.update(self.extract_youtube_metadata(soup))
            elif 'github' in site_name.lower():
                metadata.update(self.extract_github_metadata(soup))
            
            # Generic profile information extraction
            generic_info = self.extract_generic_profile_info(soup)
            metadata.update(generic_info)
            
        except Exception as e:
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def extract_twitter_metadata(self, soup) -> Dict[str, Any]:
        """Extract Twitter/X specific metadata."""
        metadata = {}
        
        # Followers count
        followers_elem = soup.find('a', href=re.compile(r'/followers'))
        if followers_elem:
            followers_text = followers_elem.get_text(strip=True)
            metadata['followers'] = followers_text
        
        # Following count
        following_elem = soup.find('a', href=re.compile(r'/following'))
        if following_elem:
            following_text = following_elem.get_text(strip=True)
            metadata['following'] = following_text
        
        # Bio/description
        bio_elem = soup.find('div', {'data-testid': 'UserDescription'})
        if bio_elem:
            metadata['bio'] = bio_elem.get_text(strip=True)
        
        # Verified status
        verified_elem = soup.find('svg', {'data-testid': 'Icon-verified'})
        metadata['verified'] = bool(verified_elem)
        
        return metadata
    
    def extract_instagram_metadata(self, soup) -> Dict[str, Any]:
        """Extract Instagram specific metadata."""
        metadata = {}
        
        # Followers and following
        meta_elem = soup.find('meta', property='og:description')
        if meta_elem and meta_elem.get('content'):
            content = meta_elem['content']
            # Extract followers from meta description
            followers_match = re.search(r'(\d+[KMB]?)\s+Followers', content, re.IGNORECASE)
            if followers_match:
                metadata['followers'] = followers_match.group(1)
            
            following_match = re.search(r'(\d+[KMB]?)\s+Following', content, re.IGNORECASE)
            if following_match:
                metadata['following'] = following_match.group(1)
            
            posts_match = re.search(r'(\d+[KMB]?)\s+Posts', content, re.IGNORECASE)
            if posts_match:
                metadata['posts'] = posts_match.group(1)
        
        return metadata
    
    def extract_linkedin_metadata(self, soup) -> Dict[str, Any]:
        """Extract LinkedIn specific metadata."""
        metadata = {}
        
        # Job title
        title_elem = soup.find('div', class_='text-body-medium')
        if title_elem:
            metadata['job_title'] = title_elem.get_text(strip=True)
        
        # Company
        company_elem = soup.find('div', {'data-field': 'experience_company'})
        if company_elem:
            metadata['company'] = company_elem.get_text(strip=True)
        
        return metadata
    
    def extract_facebook_metadata(self, soup) -> Dict[str, Any]:
        """Extract Facebook specific metadata."""
        metadata = {}
        
        # Profile name
        name_elem = soup.find('h1', id='fb-timeline-cover-name')
        if name_elem:
            metadata['profile_name'] = name_elem.get_text(strip=True)
        
        return metadata
    
    def extract_youtube_metadata(self, soup) -> Dict[str, Any]:
        """Extract YouTube specific metadata."""
        metadata = {}
        
        # Subscribers
        subscribers_elem = soup.find('yt-formatted-string', id='subscriber-count')
        if subscribers_elem:
            metadata['subscribers'] = subscribers_elem.get_text(strip=True)
        
        # Channel description
        description_elem = soup.find('yt-formatted-string', id='description')
        if description_elem:
            metadata['description'] = description_elem.get_text(strip=True)
        
        return metadata
    
    def extract_github_metadata(self, soup) -> Dict[str, Any]:
        """Extract GitHub specific metadata."""
        metadata = {}
        
        # Bio
        bio_elem = soup.find('div', class_='p-note')
        if bio_elem:
            metadata['bio'] = bio_elem.get_text(strip=True)
        
        # Location
        location_elem = soup.find('span', class_='p-label')
        if location_elem:
            metadata['location'] = location_elem.get_text(strip=True)
        
        # Followers and following
        followers_elem = soup.find('a', href=re.compile(r'/followers'))
        if followers_elem:
            followers_text = followers_elem.get_text(strip=True)
            metadata['followers'] = followers_text
        
        following_elem = soup.find('a', href=re.compile(r'/following'))
        if following_elem:
            following_text = following_elem.get_text(strip=True)
            metadata['following'] = following_text
        
        # Repositories count
        repos_elem = soup.find('span', class_='Counter')
        if repos_elem:
            metadata['repositories'] = repos_elem.get_text(strip=True)
        
        return metadata
    
    def extract_generic_profile_info(self, soup) -> Dict[str, Any]:
        """Extract generic profile information."""
        metadata = {}
        
        # Look for common profile elements
        profile_patterns = [
            ('bio', ['bio', 'about', 'description', 'profile-bio']),
            ('name', ['name', 'full-name', 'profile-name']),
            ('location', ['location', 'from', 'based']),
            ('website', ['website', 'url', 'site'])
        ]
        
        for field, classes in profile_patterns:
            for class_name in classes:
                elem = soup.find(class_=class_name) or soup.find(id=class_name)
                if elem:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 0:
                        metadata[field] = text
                        break
        
        return metadata
