import asyncio
import re
from typing import List, Dict, Set, Any, Optional
from searcher import SiteChecker
from username_chainer import UsernameChainer
from config_manager import ConfigManager
from colorama import Fore, Style
import logging

class NameSearcher:
    """Search for people by their real name across various platforms."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.site_checker = SiteChecker(config=self.config)
        self.username_chainer = UsernameChainer(config=self.config)
        self.logger = logging.getLogger(__name__)
        
        # Common name patterns and variations
        self.name_patterns = {
            'separators': ['.', '_', '-', ''],
            'prefixes': ['the', 'real', 'official', 'iam', 'im', 'its'],
            'suffixes': ['official', 'real', 'verified', 'pro', 'tv', 'gg'],
            'common_combinations': {
                'first_last': ['{first}{last}', '{first}_{last}', '{first}.{last}', '{first}-{last}'],
                'last_first': ['{last}{first}', '{last}_{first}', '{last}.{first}', '{last}-{first}'],
                'first_initial_last': ['{f}{last}', '{f}_{last}', '{f}.{last}', '{f}-{last}'],
                'first_last_initial': ['{first}{l}', '{first}_{l}', '{first}.{l}', '{first}-{l}'],
                'f_initial_last': ['{f}{last}', '{f}_{last}', '{f}.{last}', '{f}-{last}'],
                'first_middle_last': ['{first}{middle}{last}', '{first}_{middle}_{last}']
            }
        }
        
        # Platform-specific name patterns
        self.platform_patterns = {
            'linkedin': {
                'format': '{first}-{last}',
                'variations': ['{first}{last}', '{first}.{last}', '{first}_{last}']
            },
            'github': {
                'format': '{first}{last}',
                'variations': ['{first}-{last}', '{first}_{last}', '{first}{l}']
            },
            'twitter': {
                'format': '{first}{last}',
                'variations': ['{first}_{last}', '{first}{l}', '{f}{last}']
            },
            'instagram': {
                'format': '{first}_{last}',
                'variations': ['{first}{last}', '{first}.{last}', '{first}{l}']
            }
        }
    
    async def search_by_name(self, full_name: str, max_variations: int = 20) -> Dict[str, Any]:
        """Search for profiles using a person's real name."""
        print(f"Searching for profiles with name: {full_name}")
        
        # Parse the name
        name_parts = self._parse_name(full_name)
        if not name_parts:
            return {'error': 'Invalid name format'}
        
        # Generate username variations from name
        username_variations = self._generate_username_variations(name_parts, max_variations)
        
        # Search for each variation
        all_results = []
        found_profiles = []
        direct_matches = []
        
        print(f"Testing {len(username_variations)} username variations...")
        
        for i, username in enumerate(username_variations):
            try:
                print(f"    Checking variation {i+1}/{len(username_variations)}: {username}")
                results = await self.site_checker.search_all(username, extract_metadata=True)
                
                # Show all found profiles first
                found_any = False
                for result in results:
                    if result.get('found'):
                        found_any = True
                        platform = result.get('name', 'Unknown')
                        url = result.get('url', '')
                        metadata = result.get('metadata', {})
                        
                        # Extract display name from metadata
                        display_name = (metadata.get('display_name') or 
                                      metadata.get('name') or 
                                      metadata.get('full_name') or 
                                      '')
                        
                        # Calculate name confidence
                        name_confidence = self._calculate_name_confidence(result, name_parts)
                        
                        profile_info = {
                            'username': username,
                            'platform': platform,
                            'url': url,
                            'display_name': display_name,
                            'bio': metadata.get('description', ''),
                            'name_confidence': name_confidence,
                            'metadata': metadata
                        }
                        
                        found_profiles.append(profile_info)
                        
                        # Show immediate feedback for found profiles
                        print(f"      {Fore.GREEN}FOUND{Style.RESET_ALL}: {platform} - @{username}")
                        if display_name:
                            print(f"        Name: {display_name} (Match: {name_confidence:.2f})")
                        print(f"        URL: {url}")
                
                if not found_any:
                    print(f"      No profiles found for @{username}")
                
                # Filter for high-confidence matches for detailed results
                high_confidence_results = self._filter_by_name_confidence(results, name_parts)
                
                if high_confidence_results:
                    direct_matches.extend(high_confidence_results)
                    all_results.append({
                        'username': username,
                        'profiles': high_confidence_results,
                        'confidence': self._calculate_overall_confidence(high_confidence_results, name_parts)
                    })
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                self.logger.warning(f"Error checking username {username}: {e}")
        
        # Sort all found profiles by confidence
        found_profiles.sort(key=lambda x: x['name_confidence'], reverse=True)
        
        # Generate additional name-based searches
        name_variations = self._generate_name_variations(name_parts)
        
        return {
            'search_name': full_name,
            'name_parts': name_parts,
            'username_variations_tested': len(username_variations),
            'found_profiles': found_profiles,  # All profiles found
            'high_confidence_matches': all_results,  # High confidence matches
            'total_profiles_found': len(found_profiles),
            'name_variations': name_variations,
            'recommendations': self._generate_name_recommendations(found_profiles, name_parts)
        }
    
    def _parse_name(self, full_name: str) -> Optional[Dict[str, str]]:
        """Parse a full name into components."""
        # Remove extra spaces and convert to lowercase for processing
        clean_name = ' '.join(full_name.split()).strip()
        if not clean_name or len(clean_name.split()) < 2:
            return None
        
        parts = clean_name.split()
        
        result = {
            'full_name': clean_name,
            'first_name': parts[0].lower(),
            'last_name': parts[-1].lower(),
            'first_initial': parts[0][0].lower(),
            'last_initial': parts[-1][0].lower()
        }
        
        # Handle middle names/initials
        if len(parts) > 2:
            result['middle_name'] = parts[1].lower()
            result['middle_initial'] = parts[1][0].lower()
        else:
            result['middle_name'] = ''
            result['middle_initial'] = ''
        
        return result
    
    def _generate_username_variations(self, name_parts: Dict[str, str], max_variations: int) -> List[str]:
        """Generate username variations from name parts."""
        variations = set()
        
        # Use common combinations
        for pattern_type, patterns in self.name_patterns['common_combinations'].items():
            for pattern in patterns:
                try:
                    username = pattern.format(**name_parts)
                    if len(username) >= 3 and len(username) <= 30:
                        variations.add(username.lower())
                except KeyError as e:
                    continue  # Skip patterns that require missing parts
        
        # Add platform-specific variations
        for platform, patterns in self.platform_patterns.items():
            try:
                username = patterns['format'].format(**name_parts)
                if len(username) >= 3 and len(username) <= 30:
                    variations.add(username.lower())
            except KeyError:
                continue
        
        # Add simple combinations manually
        first = name_parts['first_name']
        last = name_parts['last_name']
        f = name_parts['first_initial']
        l = name_parts['last_initial']
        
        # Basic combinations
        variations.update([
            f"{first}{last}",
            f"{first}_{last}",
            f"{first}.{last}",
            f"{first}-{last}",
            f"{last}{first}",
            f"{last}_{first}",
            f"{last}.{first}",
            f"{last}-{first}",
            f"{f}{last}",
            f"{f}_{last}",
            f"{f}.{last}",
            f"{first}{l}",
            f"{first}_{l}",
            f"{first}.{l}",
        ])
        
        # Add common variations with numbers
        base_variations = list(variations)
        for base in base_variations[:10]:  # Limit to avoid explosion
            for num in ['1', '2', '01', '123', '2023', '2024']:
                variations.add(f"{base}{num}")
        
        # Add common prefixes/suffixes
        for base in list(variations)[:5]:
            for prefix in self.name_patterns['prefixes'][:3]:
                variations.add(f"{prefix}{base}")
            for suffix in self.name_patterns['suffixes'][:3]:
                variations.add(f"{base}{suffix}")
        
        result = list(variations)[:max_variations]
        return result
    
    def _generate_name_variations(self, name_parts: Dict[str, str]) -> List[str]:
        """Generate variations of the full name for searching."""
        variations = []
        
        first = name_parts['first_name'].title()
        last = name_parts['last_name'].title()
        
        # Standard variations
        variations.extend([
            f"{first} {last}",
            f"{first} {last[0]}.",
            f"{first[0]}. {last}",
            f"{last}, {first}",
            f"{last}, {first[0]}."
        ])
        
        # Add middle name if present
        if name_parts.get('middle_name'):
            middle = name_parts['middle_name'].title()
            middle_initial = name_parts['middle_initial'].upper()
            variations.extend([
                f"{first} {middle} {last}",
                f"{first} {middle_initial}. {last}",
                f"{first[0]}. {middle_initial}. {last}"
            ])
        
        return variations
    
    def _filter_by_name_confidence(self, results: List[Dict], name_parts: Dict[str, str]) -> List[Dict]:
        """Filter results by confidence that they match the target name."""
        high_confidence = []
        
        for result in results:
            if not result.get('found'):
                continue
            
            confidence = self._calculate_name_confidence(result, name_parts)
            if confidence >= 0.3:  # Minimum threshold
                result['name_confidence'] = confidence
                high_confidence.append(result)
        
        return high_confidence
    
    def _calculate_name_confidence(self, result: Dict, name_parts: Dict[str, str]) -> float:
        """Calculate confidence that a profile matches the target name."""
        confidence = 0.0
        
        metadata = result.get('metadata', {})
        profile_name = metadata.get('display_name', '') or metadata.get('name', '')
        bio = metadata.get('description', '') or metadata.get('bio', '')
        
        # Check display name against target name
        if profile_name:
            name_similarity = self._compare_names(profile_name, name_parts['full_name'])
            confidence += name_similarity * 0.5
        
        # Check bio for name mentions
        if bio:
            bio_score = self._check_bio_for_name(bio, name_parts)
            confidence += bio_score * 0.3
        
        # Check username similarity
        username = result.get('username', '')
        if username:
            username_score = self._check_username_name_similarity(username, name_parts)
            confidence += username_score * 0.2
        
        return min(confidence, 1.0)
    
    def _compare_names(self, found_name: str, target_name: str) -> float:
        """Compare two names for similarity."""
        found_clean = re.sub(r'[^\w\s]', '', found_name.lower()).strip()
        target_clean = re.sub(r'[^\w\s]', '', target_name.lower()).strip()
        
        if found_clean == target_clean:
            return 1.0
        
        # Check if parts match
        found_parts = found_clean.split()
        target_parts = target_clean.split()
        
        matching_parts = len(set(found_parts) & set(target_parts))
        total_parts = len(set(found_parts) | set(target_parts))
        
        if total_parts > 0:
            return matching_parts / total_parts
        
        return 0.0
    
    def _check_bio_for_name(self, bio: str, name_parts: Dict[str, str]) -> float:
        """Check if bio contains name information."""
        bio_lower = bio.lower()
        score = 0.0
        
        # Check for first name
        if name_parts['first_name'] in bio_lower:
            score += 0.3
        
        # Check for last name
        if name_parts['last_name'] in bio_lower:
            score += 0.3
        
        # Check for full name
        if name_parts['full_name'] in bio_lower:
            score += 0.4
        
        return min(score, 1.0)
    
    def _check_username_name_similarity(self, username: str, name_parts: Dict[str, str]) -> float:
        """Check if username resembles the name."""
        username_lower = username.lower()
        score = 0.0
        
        # Check for first name
        if name_parts['first_name'] in username_lower:
            score += 0.3
        
        # Check for last name
        if name_parts['last_name'] in username_lower:
            score += 0.3
        
        # Check for initials
        if name_parts['first_initial'] in username_lower and name_parts['last_initial'] in username_lower:
            score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_overall_confidence(self, results: List[Dict], name_parts: Dict[str, str]) -> float:
        """Calculate overall confidence for a set of results."""
        if not results:
            return 0.0
        
        # Average of individual confidences
        total_confidence = sum(r.get('name_confidence', 0) for r in results)
        base_confidence = total_confidence / len(results)
        
        # Bonus for multiple platforms
        platform_bonus = min(len(results) * 0.1, 0.3)
        
        # Bonus for major platforms
        major_platforms = ['LinkedIn', 'GitHub', 'Twitter', 'Instagram']
        major_platform_count = sum(1 for r in results if r.get('name') in major_platforms)
        major_bonus = min(major_platform_count * 0.1, 0.2)
        
        return min(base_confidence + platform_bonus + major_bonus, 1.0)
    
    def _generate_name_recommendations(self, found_profiles: List[Dict], name_parts: Dict[str, str]) -> List[str]:
        """Generate investigation recommendations based on name search results."""
        recommendations = []
        
        if not found_profiles:
            recommendations.append("No profiles found with high confidence. Consider:")
            recommendations.append("- Checking name spelling variations")
            recommendations.append("- Including middle names or initials")
            recommendations.append("- Trying nickname variations")
            return recommendations
        
        # Count platforms
        platforms = set(p.get('name') for p in found_profiles)
        if len(platforms) >= 3:
            recommendations.append("Strong digital footprint found across multiple platforms")
        
        # Check for professional platforms
        professional_platforms = ['LinkedIn', 'GitHub']
        if any(p in platforms for p in professional_platforms):
            recommendations.append("Professional presence detected - consider career-focused investigation")
        
        # Check confidence levels
        high_conf_count = sum(1 for p in found_profiles if p.get('name_confidence', 0) > 0.7)
        if high_conf_count > 0:
            recommendations.append(f"{high_conf_count} high-confidence profile matches found")
        
        # Suggest further investigation
        if len(found_profiles) > 0:
            recommendations.append("Consider cross-referencing found usernames with other investigation tools")
            recommendations.append("Check profile metadata for additional identifying information")
        
        return recommendations
