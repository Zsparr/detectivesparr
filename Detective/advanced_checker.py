import asyncio
import aiohttp
from typing import List, Dict, Any, Set
from searcher import SiteChecker
from advanced_integration import AdvancedIntegration
from config_manager import ConfigManager

class AdvancedChecker:
    """Enhanced checker with advanced username search features."""
    
    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.base_checker = SiteChecker(config=self.config)
        self.advanced = AdvancedIntegration()
        self.recursive_depth = self.config.get_investigation_setting('recursive_search_depth', 2)
        self.max_recursive_usernames = self.config.get_investigation_setting('max_recursive_usernames', 20)
    
    async def search_with_tags(self, username: str, tags: List[str] = None, 
                              extract_metadata: bool = True) -> Dict[str, Any]:
        """Search username with optional tag filtering."""
        print(f"Searching for username: {username}")
        
        if tags:
            sites = self.advanced.get_sites_by_tags(tags)
            print(f"Filtered to {len(sites)} sites with tags: {', '.join(tags)}")
            # Temporarily replace sites list
            original_sites = self.base_checker.sites
            self.base_checker.sites = sites
            results = await self.base_checker.search_all(username, extract_metadata)
            self.base_checker.sites = original_sites
        else:
            results = await self.base_checker.search_all(username, extract_metadata)
        
        # Generate comprehensive report
        report = self.advanced.generate_search_report(results, username)
        
        # Add captcha/censorship detection
        for result in results:
            if result.get('error'):
                # Try to detect the type of blocking
                detection = self.advanced.detect_captcha_or_censorship(
                    result.get('error', ''), 
                    result.get('status', 0)
                )
                result['blocking_detection'] = detection
        
        return report
    
    async def recursive_search(self, username: str, max_depth: int = None, 
                             visited_usernames: Set[str] = None) -> Dict[str, Any]:
        """Perform recursive username search from found profiles."""
        if max_depth is None:
            max_depth = self.recursive_depth
        
        if visited_usernames is None:
            visited_usernames = {username.lower()}
        
        print(f"Starting recursive search for {username} (depth: {max_depth})")
        
        # Initial search
        initial_results = await self.search_with_tags(username, extract_metadata=True)
        
        all_results = {
            'root_username': username,
            'search_tree': {},
            'all_found_profiles': initial_results['found_profiles'].copy(),
            'discovered_usernames': [],
            'statistics': initial_results['statistics']
        }
        
        all_results['search_tree'][username] = initial_results
        
        # Extract new usernames from metadata
        new_usernames = set()
        for profile in initial_results['found_profiles']:
            if profile.get('metadata'):
                extracted = self.advanced.extract_usernames_from_metadata(profile['metadata'])
                new_usernames.update(extracted)
        
        # Filter out already visited usernames
        new_usernames = {u for u in new_usernames if u.lower() not in visited_usernames}
        all_results['discovered_usernames'] = list(new_usernames)
        
        if max_depth > 0 and new_usernames:
            print(f"Found {len(new_usernames)} new usernames, searching recursively...")
            
            # Limit the number of recursive searches
            usernames_to_search = list(new_usernames)[:self.max_recursive_usernames]
            
            for new_username in usernames_to_search:
                visited_usernames.add(new_username.lower())
                
                try:
                    recursive_results = await self.recursive_search(
                        new_username, 
                        max_depth - 1, 
                        visited_usernames.copy()
                    )
                    
                    # Merge results
                    all_results['search_tree'][new_username] = recursive_results['search_tree'][new_username]
                    all_results['all_found_profiles'].extend(recursive_results['all_found_profiles'])
                    # Merge discovered usernames while avoiding duplicates
                    for username in recursive_results['discovered_usernames']:
                        if username not in all_results['discovered_usernames']:
                            all_results['discovered_usernames'].append(username)
                    
                except Exception as e:
                    print(f"Error in recursive search for {new_username}: {e}")
                    continue
        
        # Update final statistics
        all_results['statistics']['total_profiles_found'] = len(all_results['all_found_profiles'])
        all_results['statistics']['usernames_discovered'] = len(all_results['discovered_usernames'])
        
        return all_results
    
    def get_tag_suggestions(self) -> Dict[str, str]:
        """Get available tags with descriptions."""
        tag_descriptions = {
            'social': 'Social media platforms (Facebook, Twitter, Instagram, etc.)',
            'development': 'Development platforms (GitHub, GitLab, etc.)',
            'professional': 'Professional networks (LinkedIn, etc.)',
            'video': 'Video platforms (YouTube, Twitch, etc.)',
            'forum': 'Forums and discussion platforms (Reddit, Discord, etc.)',
            'photo': 'Photo sharing platforms (Instagram, Flickr, etc.)',
            'dating': 'Dating and relationship platforms',
            'blog': 'Blogging platforms (Medium, Blogger, etc.)',
            'ru': 'Russian sites',
            'de': 'German sites',
            'fr': 'French sites',
            'uk': 'UK sites',
            'ca': 'Canadian sites',
            'au': 'Australian sites',
            'jp': 'Japanese sites',
            'br': 'Brazilian sites'
        }
        
        available_tags = self.advanced.get_available_tags()
        suggestions = {}
        
        for tag in available_tags:
            if tag in tag_descriptions:
                suggestions[tag] = f"{tag_descriptions[tag]} ({available_tags[tag]} sites)"
            else:
                suggestions[tag] = f"{tag.title()} ({available_tags[tag]} sites)"
        
        return dict(sorted(suggestions.items()))
    
    async def batch_tagged_search(self, usernames: List[str], tags: List[str] = None) -> Dict[str, Any]:
        """Batch search with tag filtering."""
        print(f"Starting batch search for {len(usernames)} usernames")
        
        batch_results = {
            'usernames': usernames,
            'tags': tags or [],
            'results': {},
            'summary': {
                'total_usernames': len(usernames),
                'total_profiles_found': 0,
                'usernames_with_profiles': 0
            }
        }
        
        for username in usernames:
            print(f"\nSearching: {username}")
            try:
                results = await self.search_with_tags(username, tags, extract_metadata=True)
                batch_results['results'][username] = results
                
                if results['found_profiles']:
                    batch_results['summary']['usernames_with_profiles'] += 1
                    batch_results['summary']['total_profiles_found'] += len(results['found_profiles'])
                
            except Exception as e:
                print(f"Error searching {username}: {e}")
                batch_results['results'][username] = {'error': str(e)}
        
        return batch_results
