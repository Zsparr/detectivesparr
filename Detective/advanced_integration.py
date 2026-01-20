import json
import re
from typing import List, Dict, Set, Any, Optional
from collections import defaultdict

class AdvancedIntegration:
    """Integrates advanced username search features into Detective."""
    
    def __init__(self, sites_file: str = "sites.json"):
        self.sites_file = sites_file
        self.sites = self._load_sites()
        self.tagged_sites = self._build_tag_index()
        
    def _load_sites(self) -> List[Dict[str, Any]]:
        """Load sites from JSON files."""
        try:
            with open(self.sites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _build_tag_index(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build index of sites by tags."""
        tagged = defaultdict(list)
        
        for site in self.sites:
            tags = site.get('tags', [])
            if not tags:
                tags = self._infer_tags(site)
            
            for tag in tags:
                tagged[tag.lower()].append(site)
        
        return dict(tagged)
    
    def _infer_tags(self, site: Dict[str, Any]) -> List[str]:
        """Infer tags from site name and URL."""
        tags = []
        name = site.get('name', '').lower()
        url = site.get('url', '').lower()
        
        # Platform categories
        if any(platform in name for platform in ['twitter', 'x.com', 'facebook', 'instagram', 'tiktok']):
            tags.append('social')
        if any(platform in name for platform in ['github', 'gitlab', 'bitbucket']):
            tags.append('development')
        if any(platform in name for platform in ['linkedin', 'indeed']):
            tags.append('professional')
        if any(platform in name for platform in ['youtube', 'vimeo', 'twitch']):
            tags.append('video')
        if any(platform in name for platform in ['reddit', 'discord', 'telegram']):
            tags.append('forum')
        
        # Country/region tags
        country_domains = {
            '.ru': 'ru', '.de': 'de', '.fr': 'fr', '.uk': 'uk', 
            '.ca': 'ca', '.au': 'au', '.jp': 'jp', '.br': 'br'
        }
        for domain, country in country_domains.items():
            if domain in url:
                tags.append(country)
        
        # Content type tags
        if 'photo' in name or 'imgur' in name or 'flickr' in name:
            tags.append('photo')
        if 'dating' in name or 'match' in name:
            tags.append('dating')
        if 'blog' in name or 'medium' in name:
            tags.append('blog')
        
        return tags
    
    def get_sites_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get sites that match ALL specified tags."""
        if not tags:
            return self.sites
        
        tag_sets = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self.tagged_sites:
                tag_sets.append(set(self.tagged_sites[tag_lower]))
        
        if not tag_sets:
            return []
        
        # Find intersection of all tag sets
        common_sites = set.intersection(*tag_sets)
        return [site for site in self.sites if site in common_sites]
    
    def get_available_tags(self) -> Dict[str, int]:
        """Get all available tags with site counts."""
        tag_counts = {}
        for tag, sites in self.tagged_sites.items():
            tag_counts[tag] = len(sites)
        return dict(sorted(tag_counts.items()))
    
    def extract_usernames_from_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Extract potential usernames from profile metadata."""
        usernames = []
        
        # Look for links to other profiles
        if 'links' in metadata:
            for link in metadata['links']:
                # Extract username from common URL patterns
                patterns = [
                    r'github\.com/([^/?]+)',
                    r'twitter\.com/([^/?]+)',
                    r'instagram\.com/([^/?]+)',
                    r'reddit\.com/user/([^/?]+)',
                    r'linkedin\.com/in/([^/?]+)',
                    r'youtube\.com/(@[^/?]+)',
                    r'tiktok\.com/@([^/?]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, link, re.IGNORECASE)
                    if match:
                        username = match.group(1).strip('@')
                        if username and username not in usernames:
                            usernames.append(username)
        
        # Look for mentions in bio/description
        for field in ['bio', 'description', 'about']:
            if field in metadata:
                text = metadata[field]
                # Find @mentions
                mentions = re.findall(r'@(\w+)', text)
                for mention in mentions:
                    if mention not in usernames:
                        usernames.append(mention)
        
        return usernames
    
    def detect_captcha_or_censorship(self, response_text: str, status_code: int) -> Dict[str, Any]:
        """Detect if site is blocking access with captcha or censorship."""
        indicators = {
            'captcha': [
                'captcha', 'recaptcha', 'verify you are human', 
                'prove you are human', 'security check', 'robot check'
            ],
            'censorship': [
                'access denied', 'forbidden', 'blocked', 'unavailable',
                'geo-blocked', 'region locked', 'not available in your country'
            ],
            'rate_limit': [
                'too many requests', 'rate limit', 'try again later',
                'temporarily blocked', 'cooldown'
            ]
        }
        
        text_lower = response_text.lower()
        detected = []
        
        for check_type, phrases in indicators.items():
            if any(phrase in text_lower for phrase in phrases):
                detected.append(check_type)
        
        return {
            'detected': detected,
            'status_code': status_code,
            'is_blocked': len(detected) > 0
        }
    
    def generate_search_report(self, results: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """Generate comprehensive search report."""
        found_sites = [r for r in results if r.get('found')]
        error_sites = [r for r in results if r.get('error')]
        
        # Extract statistics
        stats = {
            'total_sites_checked': len(results),
            'profiles_found': len(found_sites),
            'sites_with_errors': len(error_sites),
            'success_rate': len(found_sites) / len(results) * 100 if results else 0
        }
        
        # Categorize found sites
        categories = defaultdict(list)
        for site in found_sites:
            site_tags = self._infer_tags(site)
            for tag in site_tags:
                categories[tag].append(site['name'])
        
        # Extract additional usernames from metadata
        additional_usernames = []
        for site in found_sites:
            if site.get('metadata'):
                usernames = self.extract_usernames_from_metadata(site['metadata'])
                additional_usernames.extend(usernames)
        
        return {
            'username': username,
            'timestamp': str(asyncio.get_event_loop().time()) if 'asyncio' in globals() else None,
            'statistics': stats,
            'found_profiles': found_sites,
            'categories': dict(categories),
            'additional_usernames': list(set(additional_usernames)),
            'errors': error_sites
        }
