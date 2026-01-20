import asyncio
import json
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import logging

from searcher import SiteChecker
from username_chainer import UsernameChainer
from email_analyzer import EmailAnalyzer
from ip_analyzer import IPAnalyzer
from domain_investigator import DomainInvestigator
from breach_checker import BreachChecker
from enhanced_metadata_extractor import EnhancedMetadataExtractor
from config_manager import ConfigManager

@dataclass
class ProfileChain:
    """Represents a chained profile with all discovered data."""
    username: str
    emails: Set[str]
    ips: Set[str]
    domains: Set[str]
    social_profiles: List[Dict[str, Any]]
    breach_data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence: float
    chain_source: str  # How this profile was discovered

class DeepProfileChainer:
    """Advanced profile chaining system that connects all data sources."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize all analyzers
        self.site_checker = SiteChecker(config=self.config)
        self.username_chainer = UsernameChainer(config=self.config)
        self.email_analyzer = EmailAnalyzer()
        
        # Get IP info token from config
        ipinfo_token = self.config.get('api_keys.ipinfo_token', None)
        self.ip_analyzer = IPAnalyzer(ipinfo_token=ipinfo_token)
        
        self.domain_investigator = DomainInvestigator()
        self.breach_checker = BreachChecker()
        self.metadata_extractor = EnhancedMetadataExtractor()
        
        # Chaining configuration
        self.max_chain_depth = self.config.get_investigation_setting('max_chain_depth', 3)
        self.max_profiles_per_chain = self.config.get_investigation_setting('max_profiles_per_chain', 50)
        self.min_confidence_threshold = self.config.get_investigation_setting('min_confidence_threshold', 0.3)
        
        # Chain results storage
        self.discovered_profiles: List[ProfileChain] = []
        self.processed_usernames: Set[str] = set()
        self.processed_emails: Set[str] = set()
        self.processed_ips: Set[str] = set()
        self.processed_domains: Set[str] = set()
    
    async def deep_profile_chain(self, initial_input: str, input_type: str = "username") -> Dict[str, Any]:
        """Perform deep profile chaining from initial input."""
        print(f"Starting Deep Profile Chain for: {initial_input} (type: {input_type})")
        print(f"This will search across ALL available data sources and chain connections...")
        
        start_time = datetime.now()
        
        # Reset chain data
        self.discovered_profiles = []
        self.processed_usernames = set()
        self.processed_emails = set()
        self.processed_ips = set()
        self.processed_domains = set()
        
        # Start the initial chain
        await self._chain_from_input(initial_input, input_type, depth=0, source="initial")
        
        # Build comprehensive report
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        report = self._generate_chain_report(initial_input, duration)
        
        print(f"Deep Profile Chain completed in {duration:.1f} seconds")
        print(f"Discovered {len(self.discovered_profiles)} total profiles")
        
        return report
    
    async def _chain_from_input(self, input_data: str, input_type: str, depth: int, source: str):
        """Chain from a specific input (username, email, IP, or domain)."""
        if depth >= self.max_chain_depth:
            return
        
        print(f"Chaining from {input_type}: {input_data} (depth: {depth})")
        
        if input_type == "username":
            await self._chain_username(input_data, depth, source)
        elif input_type == "email":
            await self._chain_email(input_data, depth, source)
        elif input_type == "ip":
            await self._chain_ip(input_data, depth, source)
        elif input_type == "domain":
            await self._chain_domain(input_data, depth, source)
    
    async def _chain_username(self, username: str, depth: int, source: str):
        """Chain from username across all platforms."""
        if username.lower() in self.processed_usernames:
            return
        
        self.processed_usernames.add(username.lower())
        
        # 1. Search across all social platforms
        print(f"  Searching social platforms for {username}...")
        social_results = await self.site_checker.search_all(username, extract_metadata=True)
        
        # 2. Discover alt usernames (limited for performance)
        print(f"  Discovering alt usernames for {username}...")
        alt_results = await self.username_chainer.discover_alt_usernames(username, max_variations=10)  # Further reduced from 20
        
        # 3. Extract emails, IPs, domains from metadata
        extracted_data = self._extract_from_metadata(social_results)
        
        # 4. Create profile chain
        profile = ProfileChain(
            username=username,
            emails=extracted_data['emails'],
            ips=extracted_data['ips'],
            domains=extracted_data['domains'],
            social_profiles=social_results,
            breach_data=[],
            metadata=extracted_data['metadata'],
            confidence=self._calculate_profile_confidence(username, social_results, alt_results),
            chain_source=source
        )
        
        self.discovered_profiles.append(profile)
        
        # 5. Chain to discovered data
        if depth < self.max_chain_depth - 1:
            # Chain to emails (limit to 3)
            for email in list(extracted_data['emails'])[:3]:
                if email not in self.processed_emails:
                    await self._chain_email(email, depth + 1, f"username:{username}")
            
            # Chain to alt usernames (limit to top 1)
            for alt in alt_results['found_alts'][:1]:  # Further reduced from 3 to 1
                alt_username = alt['username']
                if alt_username.lower() not in self.processed_usernames:
                    await self._chain_username(alt_username, depth + 1, f"alt_of:{username}")
    
    async def _chain_email(self, email: str, depth: int, source: str):
        """Chain from email across breach data and social platforms."""
        if email.lower() in self.processed_emails:
            return
        
        self.processed_emails.add(email.lower())
        
        # 1. Check breach data
        print(f"  Checking breach data for {email}...")
        try:
            breach_results = await self.breach_checker.check_email(email)
        except:
            breach_results = []
        
        # 2. Extract usernames from breach data
        breach_usernames = self._extract_usernames_from_breaches(breach_results)
        
        # 3. Search social platforms with email
        social_results = []
        for platform in ['GitHub', 'Twitter', 'Instagram', 'LinkedIn']:
            try:
                # Some platforms allow email search
                results = await self._search_platform_by_email(platform, email)
                social_results.extend(results)
            except:
                pass
        
        # 4. Create profile chain
        profile = ProfileChain(
            username="",  # Email-based profile
            emails={email},
            ips=set(),
        domains=set(),
            social_profiles=social_results,
            breach_data=breach_results,
            metadata={'breach_usernames': breach_usernames},
            confidence=self._calculate_email_confidence(email, breach_results, social_results),
            chain_source=source
        )
        
        self.discovered_profiles.append(profile)
        
        # 5. Chain to discovered usernames
        if depth < self.max_chain_depth - 1:
            for username in breach_usernames[:3]:  # Limit to top 3
                if username.lower() not in self.processed_usernames:
                    await self._chain_username(username, depth + 1, f"email:{email}")
    
    async def _chain_ip(self, ip: str, depth: int, source: str):
        """Chain from IP address to geolocation and other data."""
        if ip in self.processed_ips:
            return
        
        self.processed_ips.add(ip)
        
        # 1. Analyze IP
        print(f"  Analyzing IP: {ip}...")
        try:
            async with self.ip_analyzer:
                ip_results = await self.ip_analyzer.analyze_ip(ip)
        except:
            ip_results = {}
        
        # 2. Extract domains/hosts from IP analysis
        extracted_domains = set()
        if ip_results.get('domains'):
            extracted_domains.update(ip_results['domains'])
        
        # 3. Create profile chain
        profile = ProfileChain(
            username="",
            emails=set(),
            ips={ip},
            domains=extracted_domains,
            social_profiles=[],
            breach_data=[],
            metadata=ip_results,
            confidence=0.5,  # Medium confidence for IP data
            chain_source=source
        )
        
        self.discovered_profiles.append(profile)
        
        # 4. Chain to discovered domains
        if depth < self.max_chain_depth - 1:
            for domain in extracted_domains:
                if domain not in self.processed_domains:
                    await self._chain_domain(domain, depth + 1, f"ip:{ip}")
    
    async def _chain_domain(self, domain: str, depth: int, source: str):
        """Chain from domain to owner information and linked sites."""
        if domain.lower() in self.processed_domains:
            return
        
        self.processed_domains.add(domain.lower())
        
        # 1. Investigate domain
        print(f"  Investigating domain: {domain}...")
        try:
            async with self.domain_investigator:
                domain_results = await self.domain_investigator.investigate_domain(domain)
        except:
            domain_results = {}
        
        # 2. Extract emails from domain
        domain_emails = set()
        if domain_results.get('emails'):
            domain_emails.update(domain_results['emails'])
        
        # 3. Create profile chain
        profile = ProfileChain(
            username="",
            emails=domain_emails,
            ips=set(),
            domains={domain},
            social_profiles=[],
            breach_data=[],
            metadata=domain_results,
            confidence=0.6,  # Good confidence for domain data
            chain_source=source
        )
        
        self.discovered_profiles.append(profile)
        
        # 4. Chain to discovered emails
        if depth < self.max_chain_depth - 1:
            for email in domain_emails:
                if email not in self.processed_emails:
                    await self._chain_email(email, depth + 1, f"domain:{domain}")
    
    def _extract_from_metadata(self, social_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract emails, IPs, domains from social media metadata."""
        emails = set()
        ips = set()
        domains = set()
        all_metadata = {}
        
        for result in social_results:
            if result.get('metadata'):
                metadata = result['metadata']
                all_metadata[result['name']] = metadata
                
                # Extract emails
                if metadata.get('chained_emails'):
                    emails.update(metadata['chained_emails'])
                
                # Extract URLs that might contain IPs/domains
                if metadata.get('chained_urls'):
                    for url in metadata['chained_urls']:
                        # Extract domains from URLs
                        try:
                            import re
                            domain_match = re.search(r'https?://([^/]+)', url)
                            if domain_match:
                                domain = domain_match.group(1)
                                domains.add(domain)
                        except:
                            pass
                
                # Extract profile descriptions for pattern matching
                if metadata.get('description'):
                    desc = metadata['description']
                    # Email pattern
                    email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', desc)
                    emails.update(email_matches)
        
        return {
            'emails': emails,
            'ips': ips,
            'domains': domains,
            'metadata': all_metadata
        }
    
    def _extract_usernames_from_breaches(self, breach_results: List[Dict[str, Any]]) -> List[str]:
        """Extract potential usernames from breach data."""
        usernames = set()
        
        for breach in breach_results:
            # Look for username fields in breach data
            if isinstance(breach, dict):
                for key, value in breach.items():
                    if key.lower() in ['username', 'user', 'login', 'account']:
                        if isinstance(value, str) and len(value) > 2:
                            usernames.add(value)
        
        return list(usernames)
    
    async def _search_platform_by_email(self, platform: str, email: str) -> List[Dict[str, Any]]:
        """Search for profiles by email on specific platforms."""
        # This would need platform-specific implementations
        # For now, return empty list as most platforms don't support email search
        return []
    
    def _calculate_profile_confidence(self, username: str, social_results: List[Dict[str, Any]], alt_results: Dict[str, Any]) -> float:
        """Calculate confidence score for a username profile."""
        confidence = 0.0
        
        # Base confidence from found profiles
        found_profiles = [r for r in social_results if r.get('found')]
        confidence += len(found_profiles) * 0.2
        
        # Bonus for high-confidence alts
        high_confidence_alts = [alt for alt in alt_results.get('found_alts', []) if alt.get('confidence', 0) > 0.7]
        confidence += len(high_confidence_alts) * 0.1
        
        # Bonus for major platforms
        major_platforms = ['GitHub', 'Instagram', 'Twitter', 'TikTok', 'LinkedIn']
        for profile in found_profiles:
            if profile['name'] in major_platforms:
                confidence += 0.15
        
        return min(confidence, 1.0)
    
    def _calculate_email_confidence(self, email: str, breach_results: List[Dict[str, Any]], social_results: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for an email profile."""
        confidence = 0.3  # Base confidence for any email
        
        # Bonus for breach data
        if breach_results:
            confidence += 0.3
        
        # Bonus for social profiles
        if social_results:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _generate_chain_report(self, initial_input: str, duration: float) -> Dict[str, Any]:
        """Generate comprehensive chain report."""
        # Aggregate all discovered data
        all_usernames = set()
        all_emails = set()
        all_ips = set()
        all_domains = set()
        all_social_profiles = []
        all_breach_data = []
        
        for profile in self.discovered_profiles:
            all_usernames.add(profile.username) if profile.username else None
            all_emails.update(profile.emails)
            all_ips.update(profile.ips)
            all_domains.update(profile.domains)
            all_social_profiles.extend(profile.social_profiles)
            all_breach_data.extend(profile.breach_data)
        
        # Filter high-confidence profiles
        high_confidence_profiles = [p for p in self.discovered_profiles if p.confidence >= self.min_confidence_threshold]
        
        return {
            'initial_input': initial_input,
            'duration_seconds': duration,
            'total_profiles_discovered': len(self.discovered_profiles),
            'high_confidence_profiles': len(high_confidence_profiles),
            'summary': {
                'usernames': list(all_usernames),
                'emails': list(all_emails),
                'ips': list(all_ips),
                'domains': list(all_domains),
                'social_profiles_found': len([p for p in all_social_profiles if p.get('found')]),
                'breach_entries_found': len(all_breach_data)
            },
            'profiles': [self._serialize_profile(p) for p in high_confidence_profiles],
            'chain_connections': self._build_connection_map(high_confidence_profiles),
            'recommendations': self._generate_recommendations(high_confidence_profiles)
        }
    
    def _serialize_profile(self, profile: ProfileChain) -> Dict[str, Any]:
        """Serialize profile to dictionary."""
        return {
            'username': profile.username,
            'emails': list(profile.emails),
            'ips': list(profile.ips),
            'domains': list(profile.domains),
            'social_profiles': profile.social_profiles,
            'breach_data': profile.breach_data,
            'metadata': profile.metadata,
            'confidence': profile.confidence,
            'chain_source': profile.chain_source
        }
    
    def _build_connection_map(self, profiles: List[ProfileChain]) -> Dict[str, List[str]]:
        """Build a map of connections between profiles."""
        connections = {}
        
        for profile in profiles:
            profile_id = profile.username or f"email:{list(profile.emails)[0]}" if profile.emails else f"ip:{list(profile.ips)[0]}" if profile.ips else f"domain:{list(profile.domains)[0]}"
            connections[profile_id] = []
            
            # Find connections to other profiles
            for other_profile in profiles:
                if profile != other_profile:
                    # Check for shared data
                    if profile.emails & other_profile.emails:
                        connections[profile_id].append(f"shared_email_with:{other_profile.username or 'unknown'}")
                    if profile.ips & other_profile.ips:
                        connections[profile_id].append(f"shared_ip_with:{other_profile.username or 'unknown'}")
                    if profile.domains & other_profile.domains:
                        connections[profile_id].append(f"shared_domain_with:{other_profile.username or 'unknown'}")
        
        return connections
    
    def _generate_recommendations(self, profiles: List[ProfileChain]) -> List[str]:
        """Generate investigation recommendations."""
        recommendations = []
        
        # Count different types of data
        total_emails = len(set().union(*[p.emails for p in profiles]))
        total_ips = len(set().union(*[p.ips for p in profiles]))
        total_domains = len(set().union(*[p.domains for p in profiles]))
        
        if total_emails > 5:
            recommendations.append(f"High number of emails ({total_emails}) - suggests multiple online identities")
        
        if total_ips > 3:
            recommendations.append(f"Multiple IP addresses ({total_ips}) - possible VPN usage or geographic movement")
        
        if total_domains > 5:
            recommendations.append(f"Many domains ({total_domains}) - technically sophisticated user")
        
        # Check for breach data
        total_breaches = sum(len(p.breach_data) for p in profiles)
        if total_breaches > 0:
            recommendations.append(f"Found {total_breaches} breach entries - security compromised accounts")
        
        # Check for high-confidence profiles
        high_conf_count = len([p for p in profiles if p.confidence > 0.8])
        if high_conf_count > 0:
            recommendations.append(f"{high_conf_count} high-confidence profiles found - strong digital footprint")
        
        return recommendations
