import asyncio
import re
from typing import List, Dict, Set, Any, Optional
from enhanced_metadata_extractor import EnhancedMetadataExtractor
from searcher import SiteChecker
from config_manager import ConfigManager
import logging

class UsernameChainer:
    """Advanced username chaining system for discovering related accounts."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.metadata_extractor = EnhancedMetadataExtractor()
        self.site_checker = SiteChecker(config=self.config)
        self.logger = logging.getLogger(__name__)
        
        # Chaining configuration
        self.max_chaining_depth = self.config.get_investigation_setting('max_chaining_depth', 3)
        self.min_username_similarity = self.config.get_investigation_setting('min_username_similarity', 0.7)
        self.enable_cross_platform_chaining = self.config.get_investigation_setting('enable_cross_platform_chaining', True)
        
        # Username similarity patterns
        self.username_variations = {
            'separators': ['.', '_', '-', ''],
            'prefixes': ['the', 'real', 'official', 'iam', 'im', 'its', 'itsme', 'hey', 'hi', 'yo'],
            'suffixes': ['official', 'real', 'verified', '123', '01', '2023', '2024', '2025', 'tv', 'yt', 'gg', 'lp', '2k', '4k', 'pro', 'max', 'x', 'z', 'xo', 'ex', 'xr'],
            'common_substitutions': {
                'a': ['4', '@'],
                'e': ['3'],
                'i': ['1', '!'],
                'o': ['0'],
                's': ['5', '$'],
                't': ['7'],
                'l': ['1'],
                'g': ['9'],
                'b': ['8'],
                'z': ['2'],
                'c': ['(']
            },
            'gaming_variations': {
                'x': ['xx', 'xxx', 'xxxx'],
                'z': ['zz', 'zzz'],
                'common_gaming_suffixes': ['gamer', 'pro', 'legend', 'master', 'king', 'queen', 'god', 'lord', 'ninja', 'assassin', 'warrior', 'hunter', 'sniper', 'shadow', 'dark', 'light', 'fire', 'ice', 'storm', 'thunder'],
                'common_gaming_prefixes': ['mr', 'mrs', 'dr', 'captain', 'general', 'major', 'colonel', 'sergeant', 'lieutenant', 'commander', 'chief', 'boss', 'king', 'queen']
            },
            'social_patterns': {
                'instagram_patterns': ['iam', 'its', 'the', 'real', 'official'],
                'twitter_patterns': ['the', 'real', 'not', 'iam'],
                'gaming_patterns': ['x', 'z', 'pro', 'gamer', 'tv', 'gg'],
                'professional_patterns': ['real', 'official', 'verified', 'the']
            }
        }
        
        # Platform priority for chaining
        self.platform_priority = {
            'twitter': 10,
            'instagram': 9,
            'github': 8,
            'linkedin': 8,
            'youtube': 7,
            'reddit': 7,
            'tiktok': 6,
            'facebook': 6,
            'discord': 5,
            'telegram': 5,
            'steam': 4,
            'spotify': 4,
            'twitch': 4
        }

    async def discover_alt_usernames(self, username: str, max_variations: int = 20) -> Dict[str, Any]:
        """Discover alternative usernames using intelligent pattern analysis and profile connections."""
        print(f"Discovering alternative usernames for: {username}")
        
        # First, get the original username's profiles to analyze patterns
        original_profiles = await self.site_checker.search_all(username, extract_metadata=True)
        found_profiles = [p for p in original_profiles if p.get('found')]
        
        # Extract patterns from existing profiles
        discovered_patterns = self._analyze_username_patterns(found_profiles, username)
        
        # Extract connected usernames from profile metadata
        connected_usernames = self._extract_connected_usernames(found_profiles)
        
        # Generate intelligent variations based on discovered patterns
        variations = set()
        variations.add(username)  # Always include original
        
        # 1. Add connected usernames (completely different ones)
        variations.update(connected_usernames)
        
        # 2. Pattern-based variations from existing profiles
        if discovered_patterns:
            pattern_variations = self._generate_pattern_based_variations(username, discovered_patterns)
            variations.update(pattern_variations)
        
        # 3. Generate variations from connected usernames
        if connected_usernames:
            connected_variations = self._generate_variations_from_connected(connected_usernames, discovered_patterns)
            variations.update(connected_variations)
        
        # 4. Common variations (reduced set)
        common_variations = self._generate_smart_common_variations(username)
        variations.update(common_variations)
        
        # 5. Cross-platform pattern variations
        cross_platform = self._generate_cross_platform_variations(username, found_profiles)
        variations.update(cross_platform)
        
        # Convert to list and prioritize
        all_variations = list(variations)[:max_variations]
        prioritized_variations = self._prioritize_variations(all_variations, discovered_patterns, connected_usernames)
        
        print(f"Generated {len(prioritized_variations)} potential alt usernames")
        print(f"Found {len(connected_usernames)} connected usernames from profiles")
        
        # Test variations against platforms where original was found + major platforms
        target_platforms = [p['name'] for p in found_profiles][:3]  # Focus on platforms where user exists
        major_platforms = ['GitHub', 'Instagram', 'Twitter', 'TikTok', 'LinkedIn', 'Reddit']
        all_target_platforms = list(set(target_platforms + major_platforms))
        
        found_alts = []
        
        for i, variation in enumerate(prioritized_variations[:8]):  # Test top 8 instead of 5
            try:
                print(f"    Checking variation {i+1}/8: {variation}")
                # Quick check on relevant platforms
                results = await self.site_checker.search_all(variation, extract_metadata=False)
                
                found_profiles = [r for r in results if r.get('found') and r['name'] in all_target_platforms]
                if found_profiles:
                    found_alts.append({
                        'username': variation,
                        'profiles': found_profiles,
                        'confidence': self._calculate_alt_confidence(variation, username, found_profiles),
                        'source': 'connected' if variation in connected_usernames else 'pattern'
                    })
                    
                await asyncio.sleep(0.1)
                    
            except Exception as e:
                self.logger.warning(f"Error checking variation {variation}: {e}")
        
        # Sort by confidence
        found_alts.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'original_username': username,
            'total_variations': len(prioritized_variations),
            'found_alts': found_alts,
            'discovered_patterns': discovered_patterns,
            'connected_usernames': connected_usernames,
            'target_platforms': target_platforms
        }
    
    def _generate_leet_variations(self, username: str) -> Set[str]:
        """Generate leet speak variations."""
        variations = set()
        substitutions = self.username_variations['common_substitutions']
        
        # Single character substitutions
        for char, subs in substitutions.items():
            if char in username:
                for sub in subs:
                    variations.add(username.replace(char, sub))
        
        # Multiple character substitutions
        for _ in range(3):  # Generate up to 3 variations
            variation = username
            for char, subs in substitutions.items():
                if char in variation and len(subs) > 0:
                    variation = variation.replace(char, subs[0])
            variations.add(variation)
        
        return variations
    
    def _generate_gaming_variations(self, username: str) -> Set[str]:
        """Generate gaming-specific variations."""
        variations = set()
        gaming = self.username_variations['gaming_variations']
        
        # Add gaming prefixes
        for prefix in gaming['common_gaming_prefixes']:
            variations.add(f"{prefix}{username}")
            variations.add(f"{prefix}_{username}")
            variations.add(f"{prefix}{username}")
        
        # Add gaming suffixes
        for suffix in gaming['common_gaming_suffixes']:
            variations.add(f"{username}{suffix}")
            variations.add(f"{username}_{suffix}")
            variations.add(f"{username}{suffix}")
        
        # Add X and Z variations
        for x_var in gaming['x']:
            variations.add(f"{username}{x_var}")
            variations.add(f"{x_var}{username}")
        
        for z_var in gaming['z']:
            variations.add(f"{username}{z_var}")
            variations.add(f"{z_var}{username}")
        
        return variations
    
    def _generate_social_variations(self, username: str) -> Set[str]:
        """Generate social media platform variations."""
        variations = set()
        social = self.username_variations['social_patterns']
        
        # Platform-specific patterns
        for platform, patterns in social.items():
            for pattern in patterns:
                variations.add(f"{pattern}{username}")
                variations.add(f"{pattern}_{username}")
                variations.add(f"{username}{pattern}")
                variations.add(f"{username}_{pattern}")
        
        return variations
    
    def _generate_separator_variations(self, username: str) -> Set[str]:
        """Generate variations with different separators."""
        variations = set()
        separators = self.username_variations['separators']
        
        # Add separators between characters (for short usernames)
        if len(username) <= 8:
            for sep in separators:
                if sep:
                    variations.add(sep.join(username))
        
        # Add separators at start/end
        for sep in separators:
            variations.add(f"{sep}{username}")
            variations.add(f"{username}{sep}")
        
        return variations
    
    def _generate_number_variations(self, username: str) -> Set[str]:
        """Generate variations with numbers."""
        variations = set()
        
        # Common number patterns
        number_patterns = ['123', '01', '02', '03', '007', '101', '2023', '2024', '2025', '1', '2', '3', '7', '8', '9', '0']
        
        for num in number_patterns:
            variations.add(f"{username}{num}")
            variations.add(f"{num}{username}")
            variations.add(f"{username}_{num}")
            variations.add(f"{num}_{username}")
        
        return variations
    
    def _generate_case_variations(self, username: str) -> Set[str]:
        """Generate case variations."""
        variations = set()
        
        # Common case patterns
        variations.add(username.upper())
        variations.add(username.capitalize())
        variations.add(username.title())
        
        # Camel case for longer usernames
        if len(username) > 4:
            variations.add(username[0].upper() + username[1:])
        
        return variations
    
    def _generate_typo_variations(self, username: str) -> Set[str]:
        """Generate common typo variations."""
        variations = set()
        
        # Common character swaps
        swaps = {
            'm': 'n',
            'n': 'm',
            'b': 'd',
            'd': 'b',
            'p': 'q',
            'q': 'p',
            'u': 'v',
            'v': 'u'
        }
        
        for char, swap in swaps.items():
            if char in username:
                variations.add(username.replace(char, swap))
        
        # Double letter variations
        for i in range(len(username) - 1):
            if username[i] == username[i + 1]:
                # Remove double
                variations.add(username[:i] + username[i] + username[i + 2:])
            else:
                # Add double
                variations.add(username[:i + 1] + username[i] + username[i + 1:])
        
        return variations
    
    def _extract_connected_usernames(self, found_profiles: List[Dict]) -> Set[str]:
        """Extract completely different usernames from profile metadata and connections."""
        connected_usernames = set()
        
        for profile in found_profiles:
            metadata = profile.get('metadata', {})
            
            # Extract usernames from bio/description
            if metadata.get('description'):
                bio_usernames = self._extract_usernames_from_text(metadata['description'])
                connected_usernames.update(bio_usernames)
            
            # Extract from social links
            if metadata.get('social_links'):
                for link in metadata['social_links']:
                    username = self._extract_username_from_url(link, "")
                    if username and len(username) > 2:
                        connected_usernames.add(username)
            
            # Extract from chained usernames (from metadata extractor)
            if metadata.get('chained_usernames'):
                connected_usernames.update(metadata['chained_usernames'])
            
            # Extract from profile URLs that might contain different usernames
            profile_url = profile.get('url', '')
            if profile_url:
                url_username = self._extract_username_from_url(profile_url, "")
                if url_username and url_username != profile.get('username', '') and len(url_username) > 2:
                    connected_usernames.add(url_username)
        
        # Filter out the original username and obvious variations
        original_username = found_profiles[0].get('username', '') if found_profiles else ''
        filtered_usernames = set()
        
        for username in connected_usernames:
            if (username.lower() != original_username.lower() and 
                not self._is_obvious_variation(username, original_username) and
                len(username) >= 3 and len(username) <= 30):
                filtered_usernames.add(username.lower())
        
        return filtered_usernames
    
    def _extract_usernames_from_text(self, text: str) -> Set[str]:
        """Extract usernames from bio/description text."""
        usernames = set()
        
        # Social media mentions and patterns
        patterns = [
            r'@([a-zA-Z0-9_]{3,30})',  # @username
            r'(?:instagram|ig|twitter|x\.com|tiktok|github|linkedin|facebook|fb|discord|telegram|spotify|steam|twitch)\.com/([a-zA-Z0-9_]{3,30})',
            r'(?:username|user|handle|find|follow):\s*([a-zA-Z0-9_]{3,30})',
            r'(?:also\s+found\s+as|aka|also\s+known\s+as):\s*([a-zA-Z0-9_]{3,30})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            usernames.update(matches)
        
        return usernames
    
    def _is_obvious_variation(self, variation: str, original: str) -> bool:
        """Check if a username is an obvious variation of the original."""
        if not original:
            return False
        
        # Remove separators and compare
        clean_variation = re.sub(r'[._-]', '', variation.lower())
        clean_original = re.sub(r'[._-]', '', original.lower())
        
        # If they're very similar after cleaning, it's an obvious variation
        if clean_variation == clean_original:
            return True
        
        # If one contains the other completely
        if clean_original in clean_variation or clean_variation in clean_original:
            return True
        
        # Check if they have high similarity
        similarity = self._calculate_username_score(variation, original)
        if similarity > 0.8:
            return True
        
        return False
    
    def _generate_variations_from_connected(self, connected_usernames: Set[str], patterns: Dict) -> Set[str]:
        """Generate variations based on connected usernames."""
        variations = set()
        
        for connected in connected_usernames:
            # Add the connected username itself
            variations.add(connected)
            
            # Apply discovered patterns to connected usernames
            if patterns.get('separators_used'):
                for sep in patterns['separators_used']:
                    if sep and sep not in connected:
                        variations.add(connected.replace('_', sep).replace('.', sep).replace('-', sep))
            
            # Add common variations of connected usernames
            if len(connected) <= 10:
                common_additions = ['_', '.', 'x', '1']
                for addition in common_additions:
                    variations.add(connected + addition)
        
        return variations
    
    def _prioritize_variations(self, variations: List[str], patterns: Dict, connected_usernames: Set[str]) -> List[str]:
        """Prioritize variations based on discovered patterns, connections, and likelihood."""
        scored_variations = []
        
        for variation in variations:
            score = 0.0
            
            # Highest priority: connected usernames (completely different ones)
            if variation in connected_usernames:
                score += 1.0
            
            # Higher score for pattern-based variations
            if any(sep in variation for sep in patterns.get('separators_used', set())):
                score += 0.3
            
            # Higher score for using discovered prefixes/suffixes
            if any(prefix in variation.lower() for prefix in patterns.get('prefixes_used', set())):
                score += 0.4
            
            if any(suffix in variation.lower() for suffix in patterns.get('suffixes_used', set())):
                score += 0.4
            
            # Penalty for too long or too short
            if len(variation) < 3 or len(variation) > 30:
                score -= 0.2
            
            # Bonus for reasonable length
            if 3 <= len(variation) <= 15:
                score += 0.1
            
            # Bonus for usernames that look like real names (common patterns)
            if self._looks_like_real_username(variation):
                score += 0.2
            
            scored_variations.append((variation, score))
        
        # Sort by score (descending) and return just the usernames
        scored_variations.sort(key=lambda x: x[1], reverse=True)
        return [var[0] for var in scored_variations]
    
    def _looks_like_real_username(self, username: str) -> bool:
        """Check if username looks like a real, manually created username."""
        # Avoid obviously auto-generated ones
        if re.match(r'^[a-z]+\d{4}$', username.lower()):  # letters + 4 digits
            return False
        
        if username.count('x') > 2 or username.count('z') > 2:  # too many x/z
            return False
        
        # Prefer mixed patterns
        has_letters = any(c.isalpha() for c in username)
        has_numbers = any(c.isdigit() for c in username)
        
        if has_letters and has_numbers:
            return True
        
        # All letters with reasonable length
        if has_letters and not has_numbers and 4 <= len(username) <= 12:
            return True
        
        return False
    
    def _analyze_username_patterns(self, found_profiles: List[Dict], username: str) -> Dict[str, Any]:
        """Analyze patterns from existing profiles to understand user's naming conventions."""
        patterns = {
            'separators_used': set(),
            'prefixes_used': set(),
            'suffixes_used': set(),
            'number_patterns': set(),
            'case_preferences': set(),
            'platform_specific_patterns': {}
        }
        
        for profile in found_profiles:
            profile_url = profile.get('url', '')
            platform_name = profile.get('name', '').lower()
            
            # Analyze the username in this profile's URL
            url_username = self._extract_username_from_url(profile_url, username)
            if url_username and url_username != username:
                self._analyze_username_differences(username, url_username, patterns)
            
            # Platform-specific patterns
            if platform_name:
                patterns['platform_specific_patterns'][platform_name] = {
                    'url_pattern': profile_url,
                    'username_format': url_username
                }
        
        return patterns
    
    def _extract_username_from_url(self, url: str, original_username: str) -> str:
        """Extract username from profile URL, accounting for variations."""
        if not url:
            return ""
        
        # Remove domain and extract path
        path_parts = url.split('/')
        for part in path_parts:
            if part and part != original_username and len(part) > 2:
                # Check if this could be a username variation
                if self._is_username_variation(part, original_username):
                    return part
        
        return ""
    
    def _is_username_variation(self, candidate: str, original: str) -> bool:
        """Check if candidate is likely a variation of original username."""
        # Remove common separators and compare
        clean_candidate = re.sub(r'[._-]', '', candidate.lower())
        clean_original = re.sub(r'[._-]', '', original.lower())
        
        # Check similarity
        if clean_candidate == clean_original:
            return True
        
        # Check if original is contained in candidate or vice versa
        if clean_original in clean_candidate or clean_candidate in clean_original:
            return True
        
        # Check Levenshtein distance (simplified)
        distance = sum(1 for i, c in enumerate(clean_original) 
                       if i < len(clean_candidate) and c != clean_candidate[i])
        if distance <= 2 and abs(len(clean_candidate) - len(clean_original)) <= 2:
            return True
        
        return False
    
    def _analyze_username_differences(self, original: str, variation: str, patterns: Dict):
        """Analyze differences between original and variation to extract patterns."""
        # Find separators
        if '.' in variation:
            patterns['separators_used'].add('.')
        if '_' in variation:
            patterns['separators_used'].add('_')
        if '-' in variation:
            patterns['separators_used'].add('-')
        
        # Find prefixes
        if variation.lower().startswith('the'):
            patterns['prefixes_used'].add('the')
        if variation.lower().startswith('real'):
            patterns['prefixes_used'].add('real')
        if variation.lower().startswith('official'):
            patterns['prefixes_used'].add('official')
        
        # Find suffixes
        if variation.lower().endswith('official'):
            patterns['suffixes_used'].add('official')
        if variation.lower().endswith('real'):
            patterns['suffixes_used'].add('real')
        if any(variation.lower().endswith(str(i)) for i in range(10)):
            patterns['number_patterns'].add('numeric_suffix')
        
        # Case patterns
        if variation.isupper():
            patterns['case_preferences'].add('uppercase')
        if variation[0].isupper() and variation[1:].islower():
            patterns['case_preferences'].add('capitalized')
    
    def _generate_pattern_based_variations(self, username: str, patterns: Dict) -> Set[str]:
        """Generate variations based on discovered patterns."""
        variations = set()
        
        # Use discovered separators
        for sep in patterns['separators_used']:
            if sep:
                # Insert separator in common positions
                if len(username) > 3:
                    mid = len(username) // 2
                    variations.add(username[:mid] + sep + username[mid:])
                variations.add(sep + username)
                variations.add(username + sep)
        
        # Use discovered prefixes
        for prefix in patterns['prefixes_used']:
            variations.add(prefix + username)
            variations.add(prefix + '_' + username)
        
        # Use discovered suffixes
        for suffix in patterns['suffixes_used']:
            variations.add(username + suffix)
            variations.add(username + '_' + suffix)
        
        return variations
    
    def _generate_smart_common_variations(self, username: str) -> Set[str]:
        """Generate intelligent common variations based on username characteristics."""
        variations = set()
        
        # Only generate relevant variations based on username length and type
        if len(username) <= 8:
            # For short usernames, try common additions
            common_additions = ['x', 'xx', 'pro', 'tv', 'gg', 'io']
            for addition in common_additions:
                variations.add(username + addition)
        
        if any(c.isdigit() for c in username):
            # If username has numbers, try number variations
            base = re.sub(r'\d+', '', username)
            for i in range(1, 100):
                variations.add(base + str(i))
                if len(variations) > 10:  # Limit
                    break
        
        # Try common separators
        for sep in ['.', '_', '-']:
            variations.add(username.replace(sep, ''))
            if not any(sep in username for sep in ['.', '_', '-']):
                variations.add(username + sep)
        
        return variations
    
    def _generate_cross_platform_variations(self, username: str, found_profiles: List[Dict]) -> Set[str]:
        """Generate variations based on cross-platform patterns."""
        variations = set()
        
        # Platform-specific adjustments
        for profile in found_profiles:
            platform = profile.get('name', '').lower()
            
            if 'instagram' in platform:
                # Instagram often has underscores and prefixes
                variations.add(username.replace('.', '_'))
                variations.add('the_' + username)
            
            elif 'twitter' in platform or 'x.com' in profile.get('url', ''):
                # Twitter/X often has no underscores
                variations.add(username.replace('_', ''))
                variations.add(username.replace('.', ''))
            
            elif 'github' in platform:
                # GitHub prefers lowercase and hyphens
                variations.add(username.lower().replace('_', '-'))
            
            elif 'tiktok' in platform:
                # TikTok often has numbers and special chars
                if not any(c.isdigit() for c in username):
                    variations.add(username + '1')
        
        return variations
    
        
    def _calculate_alt_confidence(self, alt_username: str, original_username: str, profiles: List[Dict]) -> float:
        """Calculate confidence score for an alternative username."""
        confidence = 0.0
        
        # Base similarity score
        similarity = self._calculate_username_score(alt_username, original_username)
        confidence += similarity * 0.4
        
        # Profile count bonus
        profile_count = len(profiles)
        confidence += min(profile_count * 0.2, 0.4)
        
        # Platform priority bonus
        platform_bonus = 0.0
        for profile in profiles:
            platform_name = profile['name'].lower()
            if platform_name in self.platform_priority:
                platform_bonus += self.platform_priority[platform_name] / 100
        
        confidence += min(platform_bonus, 0.2)
        
        return min(confidence, 1.0)
    
    async def chain_usernames(self, initial_username: str, depth: int = 0) -> Dict[str, Any]:
        if depth >= self.max_chaining_depth:
            return {'usernames': [], 'profiles': [], 'chains': []}
        
        self.logger.info(f"Chaining username: {initial_username} at depth {depth}")
        
        # Clear previous metadata
        self.metadata_extractor.clear_chained_data()
        
        # Search for initial username
        results = await self.site_checker.search_all(initial_username, extract_metadata=True)
        
        # Extract chained usernames from found profiles
        chained_usernames = set()
        chained_profiles = []
        chains = []
        
        for result in results:
            if result.get('found') and result.get('metadata'):
                metadata = result['metadata']
                
                # Extract usernames from metadata
                if metadata.get('chained_usernames'):
                    chained_usernames.update(metadata['chained_usernames'])
                
                # Store profile info
                chained_profiles.append({
                    'username': initial_username,
                    'platform': result['name'],
                    'url': result['url'],
                    'metadata': metadata,
                    'depth': depth
                })
                
                # Create chain relationships
                if metadata.get('chained_usernames'):
                    for chained_username in metadata['chained_usernames']:
                        chains.append({
                            'from_username': initial_username,
                            'to_username': chained_username,
                            'platform': result['name'],
                            'source': 'profile_metadata',
                            'confidence': self._calculate_chain_confidence(initial_username, chained_username, metadata)
                        })
        
        # Filter and prioritize chained usernames
        prioritized_usernames = self._prioritize_chained_usernames(chained_usernames, initial_username)
        
        # Recursively chain high-confidence usernames
        if depth < self.max_chaining_depth - 1:
            for username in prioritized_usernames[:5]:  # Limit to top 5 for performance
                if username != initial_username:
                    sub_chain = await self.chain_usernames(username, depth + 1)
                    chained_profiles.extend(sub_chain['profiles'])
                    chains.extend(sub_chain['chains'])
        
        return {
            'usernames': list(prioritized_usernames),
            'profiles': chained_profiles,
            'chains': chains
        }

    def _prioritize_chained_usernames(self, usernames: Set[str], original_username: str) -> List[str]:
        """Prioritize chained usernames based on similarity and relevance."""
        scored_usernames = []
        
        for username in usernames:
            if username.lower() == original_username.lower():
                continue
            
            score = self._calculate_username_score(username, original_username)
            scored_usernames.append((username, score))
        
        # Sort by score (descending)
        scored_usernames.sort(key=lambda x: x[1], reverse=True)
        
        return [username for username, score in scored_usernames if score >= self.min_username_similarity]

    def _calculate_username_score(self, username: str, original_username: str) -> float:
        """Calculate similarity score between usernames."""
        username_lower = username.lower()
        original_lower = original_username.lower()
        
        # Exact match (shouldn't happen due to filtering)
        if username_lower == original_lower:
            return 1.0
        
        # Contains original username
        if original_lower in username_lower or username_lower in original_lower:
            return 0.9
        
        # Levenshtein distance
        distance = self._levenshtein_distance(username_lower, original_lower)
        max_len = max(len(username_lower), len(original_lower))
        similarity = 1 - (distance / max_len)
        
        # Bonus for similar patterns
        if self._has_similar_pattern(username_lower, original_lower):
            similarity += 0.2
        
        return min(similarity, 1.0)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _has_similar_pattern(self, username1: str, username2: str) -> bool:
        """Check if usernames follow similar patterns."""
        # Check for common separators
        for sep in self.username_variations['separators']:
            if sep in username1 and sep in username2:
                parts1 = username1.split(sep)
                parts2 = username2.split(sep)
                if len(parts1) == len(parts2):
                    similar_parts = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
                    if similar_parts >= len(parts1) / 2:
                        return True
        
        return False

    def _calculate_chain_confidence(self, from_username: str, to_username: str, metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for a username chain."""
        confidence = 0.5  # Base confidence
        
        # Username similarity
        similarity = self._calculate_username_score(to_username, from_username)
        confidence += similarity * 0.3
        
        # Platform priority bonus
        platform = metadata.get('site_name', '').lower()
        for platform_name, priority in self.platform_priority.items():
            if platform_name in platform:
                confidence += (priority / 100) * 0.2
                break
        
        # Metadata quality bonus
        if metadata.get('bio'):
            confidence += 0.1
        if metadata.get('profile_images'):
            confidence += 0.1
        if metadata.get('social_links'):
            confidence += 0.1
        
        # Cross-platform bonus
        if metadata.get('chained_usernames') and len(metadata['chained_usernames']) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)

    async def generate_username_variations(self, username: str) -> List[str]:
        """Generate username variations for chaining."""
        variations = [username]
        
        # Separator variations
        for sep in self.username_variations['separators']:
            # Insert separators between words
            camel_parts = re.findall(r'[A-Z][a-z]*|[a-z]+', username)
            if len(camel_parts) > 1:
                variations.append(sep.join(camel_parts))
                variations.append(sep.join(camel_parts).lower())
        
        # Prefix variations
        for prefix in self.username_variations['prefixes']:
            variations.append(prefix + username)
            variations.append(prefix + '_' + username)
            variations.append(prefix + username + '_')
        
        # Suffix variations
        for suffix in self.username_variations['suffixes']:
            variations.append(username + suffix)
            variations.append(username + '_' + suffix)
            variations.append(suffix + username)
        
        # Substitution variations
        for original, substitutes in self.username_variations['common_substitutions'].items():
            for sub in substitutes:
                variations.append(username.replace(original, sub))
                variations.append(username.replace(original.upper(), sub))
        
        # Remove duplicates and invalid usernames
        unique_variations = []
        for var in variations:
            if var != username and len(var) >= 3 and re.match(r'^[a-zA-Z0-9_.-]+$', var):
                unique_variations.append(var)
        
        return unique_variations[:50]  # Limit to 50 variations

    async def cross_platform_analysis(self, username: str) -> Dict[str, Any]:
        """Perform cross-platform analysis of username."""
        # Search across all platforms
        results = await self.site_checker.search_all(username, extract_metadata=True)
        
        # Analyze platform presence
        platform_analysis = {}
        total_followers = 0
        verified_platforms = []
        
        for result in results:
            if result.get('found'):
                platform = result['name']
                metadata = result.get('metadata', {})
                
                platform_analysis[platform] = {
                    'url': result['url'],
                    'followers': self._parse_count(metadata.get('followers', '0')),
                    'verified': metadata.get('verified', False),
                    'bio': metadata.get('bio', ''),
                    'profile_images': metadata.get('profile_images', []),
                    'social_links': metadata.get('social_links', [])
                }
                
                total_followers += platform_analysis[platform]['followers']
                if platform_analysis[platform]['verified']:
                    verified_platforms.append(platform)
        
        # Calculate platform consistency score
        consistency_score = self._calculate_platform_consistency(platform_analysis)
        
        return {
            'username': username,
            'platforms': platform_analysis,
            'total_platforms': len(platform_analysis),
            'verified_platforms': verified_platforms,
            'total_followers': total_followers,
            'consistency_score': consistency_score,
            'recommendations': self._generate_recommendations(platform_analysis)
        }

    def _parse_count(self, count_str: str) -> int:
        """Parse follower count string to integer."""
        if not count_str:
            return 0
        
        # Remove commas and spaces
        count_str = count_str.replace(',', '').replace(' ', '')
        
        # Handle K, M, B suffixes
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, multiplier in multipliers.items():
            if count_str.upper().endswith(suffix):
                try:
                    number = float(count_str[:-1])
                    return int(number * multiplier)
                except ValueError:
                    continue
        
        try:
            return int(count_str)
        except ValueError:
            return 0

    def _calculate_platform_consistency(self, platform_analysis: Dict[str, Any]) -> float:
        """Calculate consistency score across platforms."""
        if len(platform_analysis) <= 1:
            return 1.0
        
        bios = [info['bio'] for info in platform_analysis.values() if info['bio']]
        profile_images = [info['profile_images'] for info in platform_analysis.values() if info['profile_images']]
        
        # Bio similarity
        bio_similarity = 0
        if len(bios) > 1:
            total_similarity = 0
            comparisons = 0
            for i in range(len(bios)):
                for j in range(i + 1, len(bios)):
                    similarity = self._calculate_text_similarity(bios[i], bios[j])
                    total_similarity += similarity
                    comparisons += 1
            bio_similarity = total_similarity / comparisons if comparisons > 0 else 0
        
        # Profile image similarity (simplified - just check if platforms have images)
        image_consistency = len(profile_images) / len(platform_analysis)
        
        # Verified consistency
        verified_count = sum(1 for info in platform_analysis.values() if info['verified'])
        verified_consistency = verified_count / len(platform_analysis)
        
        return (bio_similarity * 0.5 + image_consistency * 0.3 + verified_consistency * 0.2)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _generate_recommendations(self, platform_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on platform analysis."""
        recommendations = []
        
        # Platform presence recommendations
        if len(platform_analysis) < 5:
            recommendations.append("Consider expanding to more platforms for better visibility")
        
        # Verification recommendations
        verified_count = sum(1 for info in platform_analysis.values() if info['verified'])
        if verified_count == 0 and len(platform_analysis) > 2:
            recommendations.append("Consider verification on major platforms to increase credibility")
        
        # Bio consistency recommendations
        bios = [info['bio'] for info in platform_analysis.values() if info['bio']]
        if len(bios) > 1:
            consistency = self._calculate_platform_consistency(platform_analysis)
            if consistency < 0.5:
                recommendations.append("Update bios to be more consistent across platforms")
        
        # Profile image recommendations
        platforms_with_images = [platform for platform, info in platform_analysis.items() if info['profile_images']]
        if len(platforms_with_images) < len(platform_analysis) / 2:
            recommendations.append("Add profile images to platforms without them")
        
        return recommendations

    async def generate_chain_report(self, chain_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive chain analysis report."""
        profiles = chain_results.get('profiles', [])
        chains = chain_results.get('chains', [])
        
        # Analyze chain depth
        max_depth = max(profile['depth'] for profile in profiles) if profiles else 0
        
        # Platform distribution
        platform_counts = {}
        for profile in profiles:
            platform = profile['platform']
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Chain confidence analysis
        high_confidence_chains = [c for c in chains if c.get('confidence', 0) > 0.8]
        medium_confidence_chains = [c for c in chains if 0.5 < c.get('confidence', 0) <= 0.8]
        low_confidence_chains = [c for c in chains if c.get('confidence', 0) <= 0.5]
        
        # Unique usernames discovered
        unique_usernames = set()
        for profile in profiles:
            unique_usernames.add(profile['username'])
        
        return {
            'summary': {
                'total_profiles_found': len(profiles),
                'unique_usernames_discovered': len(unique_usernames),
                'max_chain_depth': max_depth,
                'total_chains': len(chains),
                'platform_distribution': platform_counts,
                'high_confidence_chains': len(high_confidence_chains),
                'medium_confidence_chains': len(medium_confidence_chains),
                'low_confidence_chains': len(low_confidence_chains)
            },
            'profiles': profiles,
            'chains': chains,
            'recommendations': self._generate_chain_recommendations(chains, profiles)
        }

    def _generate_chain_recommendations(self, chains: List[Dict], profiles: List[Dict]) -> List[str]:
        """Generate recommendations based on chain analysis."""
        recommendations = []
        
        if len(chains) == 0:
            recommendations.append("No username chains found. Try different variations or check more platforms.")
        
        if len(chains) > 50:
            recommendations.append("Many chains found. Consider focusing on high-confidence connections.")
        
        high_confidence_chains = [c for c in chains if c.get('confidence', 0) > 0.8]
        if len(high_confidence_chains) > 0:
            recommendations.append(f"Found {len(high_confidence_chains)} high-confidence chains. These are most likely correct.")
        
        platforms = set(profile['platform'] for profile in profiles)
        if len(platforms) < 3:
            recommendations.append("Limited platform coverage. Consider expanding to more platforms.")
        
        return recommendations
