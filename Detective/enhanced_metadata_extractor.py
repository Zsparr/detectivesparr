import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import logging

class EnhancedMetadataExtractor:
    """Advanced metadata extraction system supporting 50+ platforms with username chaining."""
    
    def __init__(self):
        self.extracted_usernames: Set[str] = set()
        self.extracted_emails: Set[str] = set()
        self.extracted_urls: Set[str] = set()
        self.logger = logging.getLogger(__name__)
        
        # Platform-specific extraction rules
        self.platform_extractors = {
            'twitter': self.extract_twitter_advanced,
            'instagram': self.extract_instagram_advanced,
            'linkedin': self.extract_linkedin_advanced,
            'facebook': self.extract_facebook_advanced,
            'youtube': self.extract_youtube_advanced,
            'github': self.extract_github_advanced,
            'reddit': self.extract_reddit_advanced,
            'tiktok': self.extract_tiktok_advanced,
            'pinterest': self.extract_pinterest_advanced,
            'medium': self.extract_medium_advanced,
            'discord': self.extract_discord_advanced,
            'telegram': self.extract_telegram_advanced,
            'spotify': self.extract_spotify_advanced,
            'twitch': self.extract_twitch_advanced,
            'steam': self.extract_steam_advanced,
            'soundcloud': self.extract_soundcloud_advanced,
            'vimeo': self.extract_vimeo_advanced,
            'dribbble': self.extract_dribbble_advanced,
            'behance': self.extract_behance_advanced,
            'codepen': self.extract_codepen_advanced,
            'deviantart': self.extract_deviantart_advanced,
            'flickr': self.extract_flickr_advanced,
            'mastodon': self.extract_mastodon_advanced,
            'patreon': self.extract_patreon_advanced,
            'substack': self.extract_substack_advanced,
            'threads': self.extract_threads_advanced,
            'bluesky': self.extract_bluesky_advanced,
            'x.com': self.extract_twitter_advanced,
            'about.me': self.extract_aboutme_advanced,
            'carrd': self.extract_carrd_advanced,
            'linktree': self.extract_linktree_advanced,
            'taplink': self.extract_taplink_advanced,
            'bio.link': self.extract_biolink_advanced,
            'bento': self.extract_bento_advanced,
            'manylink': self.extract_manylink_advanced,
            'beacons': self.extract_beacons_advanced,
            'campsite': self.extract_campsite_advanced,
            'milkshake': self.extract_milkshake_advanced,
            'hub': self.extract_hub_advanced,
            'kofi': self.extract_kofi_advanced,
            'buymeacoffee': self.extract_buymeacoffee_advanced,
            'gumroad': self.extract_gumroad_advanced,
            'patreon': self.extract_patreon_advanced,
            'onlyfans': self.extract_onlyfans_advanced,
            'fansly': self.extract_fansly_advanced,
            'justforfans': self.extract_justforfans_advanced,
            'adultcontent': self.extract_adultcontent_advanced
        }
        
        # Username patterns for chaining
        self.username_patterns = [
            r'@([a-zA-Z0-9_]{3,30})',
            r'(?:https?://)?(?:www\.)?(?:twitter|instagram|tiktok|reddit|github|linkedin|facebook|youtube|twitch|steam|discord|telegram|spotify|soundcloud|vimeo|dribbble|behance|codepen|deviantart|flickr|mastodon|patreon|substack|threads|bluesky|x\.com|about\.me|carrd|linktree|taplink|bio\.link|bento\.me|manylink|beacons|campsite|milkshake|hub\.page|kofi\.com|buymeacoffee\.com|gumroad\.com|onlyfans\.com|fansly\.com|justforfans\.com)/(?:@)?([a-zA-Z0-9_]{3,30})',
            r'(?:username|user|handle|profile):\s*([a-zA-Z0-9_]{3,30})',
            r'(?:find|follow|connect):\s*@?([a-zA-Z0-9_]{3,30})',
        ]
        
        # Email patterns
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'(?:email|contact|mail):\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
        ]
        
        # URL patterns
        self.url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            r'(?:website|site|url|link):\s*(https?://[^\s<>"{}|\\^`\[\]]+)',
        ]

    async def extract_metadata(self, html_content: str, site_name: str, url: str) -> Dict[str, Any]:
        """Extract comprehensive metadata with username chaining."""
        metadata = {
            'site_name': site_name,
            'profile_url': url,
            'extraction_time': asyncio.get_event_loop().time(),
            'chained_usernames': [],
            'chained_emails': [],
            'chained_urls': [],
            'profile_images': [],
            'social_links': [],
            'external_links': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Basic metadata
            if soup.title:
                metadata['title'] = soup.title.string.strip()
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                metadata['description'] = meta_desc['content'].strip()
            
            # Platform-specific extraction
            platform_key = self._get_platform_key(site_name, url)
            if platform_key in self.platform_extractors:
                platform_metadata = await self.platform_extractors[platform_key](soup, url)
                metadata.update(platform_metadata)
            
            # Extract profile images
            metadata['profile_images'] = self._extract_profile_images(soup, url)
            
            # Extract social links
            metadata['social_links'] = self._extract_social_links(soup, url)
            
            # Extract external links
            metadata['external_links'] = self._extract_external_links(soup, url)
            
            # Username chaining
            chained_data = self._extract_chained_data(html_content, soup, url)
            metadata['chained_usernames'] = list(chained_data['usernames'])
            metadata['chained_emails'] = list(chained_data['emails'])
            metadata['chained_urls'] = list(chained_data['urls'])
            
            # Update global sets
            self.extracted_usernames.update(chained_data['usernames'])
            self.extracted_emails.update(chained_data['emails'])
            self.extracted_urls.update(chained_data['urls'])
            
        except Exception as e:
            metadata['extraction_error'] = str(e)
            self.logger.error(f"Metadata extraction failed for {site_name}: {e}")
        
        return metadata

    def _get_platform_key(self, site_name: str, url: str) -> str:
        """Get platform key for extraction rules."""
        site_lower = site_name.lower()
        url_lower = url.lower()
        
        for platform_key in self.platform_extractors.keys():
            if platform_key in site_lower or platform_key in url_lower:
                return platform_key
        
        return 'generic'

    def _extract_profile_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract profile images."""
        images = []
        
        # Common profile image selectors
        selectors = [
            'img[alt*="profile"]',
            'img[alt*="avatar"]',
            'img[alt*="photo"]',
            '.profile img',
            '.avatar img',
            '.photo img',
            '.user-image img',
            '.profile-picture img',
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            '[data-testid="profile-image"] img',
            '[data-testid="user-avatar"] img'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                src = elem.get('src') or elem.get('content')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in images:
                        images.append(full_url)
        
        return images[:5]  # Limit to first 5 images

    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract social media links."""
        social_links = []
        
        # Social media domains
        social_domains = [
            'twitter.com', 'x.com', 'instagram.com', 'facebook.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'reddit.com', 'github.com', 'pinterest.com',
            'snapchat.com', 'telegram.org', 'discord.com', 'twitch.tv', 'steam.com',
            'spotify.com', 'soundcloud.com', 'vimeo.com', 'dribbble.com', 'behance.net',
            'codepen.io', 'deviantart.com', 'flickr.com', 'mastodon.social', 'patreon.com',
            'substack.com', 'threads.net', 'bsky.app', 'about.me', 'carrd.co', 'linktr.ee',
            'taplink.co', 'bio.link', 'bento.me', 'manylink.co', 'beacons.ai',
            'campsite.bio', 'milkshake.app', 'hub.page', 'kofi.com', 'buymeacoffee.com'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                for domain in social_domains:
                    if domain in href.lower():
                        social_links.append({
                            'platform': domain.replace('.com', '').replace('.org', '').replace('.net', '').replace('.io', '').replace('.co', '').replace('.ai', '').replace('.bio', '').replace('.app', '').replace('.page', ''),
                            'url': href,
                            'text': link.get_text(strip=True)
                        })
                        break
        
        return social_links

    def _extract_external_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract external links (non-social)."""
        external_links = []
        social_domains = {'twitter.com', 'x.com', 'instagram.com', 'facebook.com', 'linkedin.com'}
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') and not any(domain in href.lower() for domain in social_domains):
                if href not in external_links:
                    external_links.append(href)
        
        return external_links[:10]  # Limit to first 10 external links

    def _extract_chained_data(self, html_content: str, soup: BeautifulSoup, url: str) -> Dict[str, Set[str]]:
        """Extract usernames, emails, and URLs for chaining."""
        usernames = set()
        emails = set()
        urls = set()
        
        # Extract from HTML content
        text_content = soup.get_text()
        
        # Extract usernames
        for pattern in self.username_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    usernames.update(m for m in match if m and len(m) >= 3)
                else:
                    if match and len(match) >= 3:
                        usernames.add(match)
        
        # Extract emails
        for pattern in self.email_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    emails.update(m for m in match if '@' in m)
                else:
                    if '@' in match:
                        emails.add(match)
        
        # Extract URLs
        for pattern in self.url_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    urls.update(m for m in match if m.startswith('http'))
                else:
                    if match.startswith('http'):
                        urls.add(match)
        
        return {
            'usernames': usernames,
            'emails': emails,
            'urls': urls
        }

    # Platform-specific extractors (enhanced versions)
    async def extract_twitter_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced Twitter/X metadata extraction."""
        metadata = {}
        
        # Basic info
        followers_elem = soup.find('a', href=re.compile(r'/followers'))
        if followers_elem:
            metadata['followers'] = followers_elem.get_text(strip=True)
        
        following_elem = soup.find('a', href=re.compile(r'/following'))
        if following_elem:
            metadata['following'] = following_elem.get_text(strip=True)
        
        # Bio
        bio_elem = soup.find('div', {'data-testid': 'UserDescription'})
        if bio_elem:
            metadata['bio'] = bio_elem.get_text(strip=True)
        
        # Location
        location_elem = soup.find('span', {'data-testid': 'UserLocation'})
        if location_elem:
            metadata['location'] = location_elem.get_text(strip=True)
        
        # Website
        website_elem = soup.find('a', {'data-testid': 'UserUrl'})
        if website_elem:
            metadata['website'] = website_elem.get('href')
        
        # Verified status
        verified_elem = soup.find('svg', {'data-testid': 'Icon-verified'})
        metadata['verified'] = bool(verified_elem)
        
        # Join date
        join_elem = soup.find('span', {'data-testid': 'UserJoinDate'})
        if join_elem:
            metadata['join_date'] = join_elem.get_text(strip=True)
        
        # Profile name
        name_elem = soup.find('div', {'data-testid': 'UserName'})
        if name_elem:
            metadata['display_name'] = name_elem.get_text(strip=True)
        
        return metadata

    async def extract_instagram_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced Instagram metadata extraction."""
        metadata = {}
        
        # Meta tags for Instagram
        meta_elem = soup.find('meta', property='og:description')
        if meta_elem and meta_elem.get('content'):
            content = meta_elem['content']
            
            # Extract followers, following, posts
            followers_match = re.search(r'(\d+[KMB]?)\s+Followers', content, re.IGNORECASE)
            if followers_match:
                metadata['followers'] = followers_match.group(1)
            
            following_match = re.search(r'(\d+[KMB]?)\s+Following', content, re.IGNORECASE)
            if following_match:
                metadata['following'] = following_match.group(1)
            
            posts_match = re.search(r'(\d+[KMB]?)\s+Posts', content, re.IGNORECASE)
            if posts_match:
                metadata['posts'] = posts_match.group(1)
        
        # Bio from meta description
        bio_elem = soup.find('meta', property='og:description')
        if bio_elem and bio_elem.get('content'):
            metadata['bio'] = bio_elem['content'].strip()
        
        # Profile name
        title_elem = soup.find('meta', property='og:title')
        if title_elem and title_elem.get('content'):
            metadata['display_name'] = title_elem['content'].strip()
        
        # Verified (blue check)
        verified_elem = soup.find('meta', property='og:site_name')
        metadata['verified'] = bool(verified_elem and 'Instagram' in verified_elem.get('content', ''))
        
        return metadata

    async def extract_linkedin_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced LinkedIn metadata extraction."""
        metadata = {}
        
        # Job title
        title_elem = soup.find('div', class_='text-body-medium')
        if title_elem:
            metadata['job_title'] = title_elem.get_text(strip=True)
        
        # Company
        company_elem = soup.find('div', {'data-field': 'experience_company'})
        if company_elem:
            metadata['company'] = company_elem.get_text(strip=True)
        
        # Location
        location_elem = soup.find('span', class_='pv-text-details__left-panel')
        if location_elem:
            metadata['location'] = location_elem.get_text(strip=True)
        
        # Headline
        headline_elem = soup.find('div', class_='text-body-large')
        if headline_elem:
            metadata['headline'] = headline_elem.get_text(strip=True)
        
        return metadata

    async def extract_facebook_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced Facebook metadata extraction."""
        metadata = {}
        
        # Profile name
        name_elem = soup.find('h1', id='fb-timeline-cover-name')
        if name_elem:
            metadata['display_name'] = name_elem.get_text(strip=True)
        
        # Profile info
        info_elem = soup.find('div', class_='x4k7w5x')
        if info_elem:
            metadata['profile_info'] = info_elem.get_text(strip=True)
        
        return metadata

    async def extract_youtube_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced YouTube metadata extraction."""
        metadata = {}
        
        # Subscribers
        subscribers_elem = soup.find('yt-formatted-string', id='subscriber-count')
        if subscribers_elem:
            metadata['subscribers'] = subscribers_elem.get_text(strip=True)
        
        # Channel description
        description_elem = soup.find('yt-formatted-string', id='description')
        if description_elem:
            metadata['description'] = description_elem.get_text(strip=True)
        
        # Channel name
        name_elem = soup.find('yt-dynamic-sizing-text', id='channel-name')
        if name_elem:
            metadata['channel_name'] = name_elem.get_text(strip=True)
        
        # Video count
        videos_elem = soup.find('span', id='videos-count')
        if videos_elem:
            metadata['video_count'] = videos_elem.get_text(strip=True)
        
        return metadata

    async def extract_github_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced GitHub metadata extraction."""
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
            metadata['followers'] = followers_elem.get_text(strip=True)
        
        following_elem = soup.find('a', href=re.compile(r'/following'))
        if following_elem:
            metadata['following'] = following_elem.get_text(strip=True)
        
        # Repositories
        repos_elem = soup.find('span', class_='Counter')
        if repos_elem:
            metadata['repositories'] = repos_elem.get_text(strip=True)
        
        # Company
        company_elem = soup.find('li', class_='vcard-detail')
        if company_elem:
            metadata['company'] = company_elem.get_text(strip=True)
        
        # Website
        website_elem = soup.find('a', class_='Link--primary')
        if website_elem:
            metadata['website'] = website_elem.get('href')
        
        return metadata

    # Add more platform extractors as needed...
    async def extract_reddit_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced Reddit metadata extraction."""
        metadata = {}
        
        # Karma
        karma_elem = soup.find('span', {'id': 'profile-karma'})
        if karma_elem:
            metadata['karma'] = karma_elem.get_text(strip=True)
        
        # Cake day
        cake_elem = soup.find('span', {'id': 'profile-cakeday'})
        if cake_elem:
            metadata['cake_day'] = cake_elem.get_text(strip=True)
        
        return metadata

    async def extract_tiktok_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Enhanced TikTok metadata extraction."""
        metadata = {}
        
        # Followers
        followers_elem = soup.find('strong', {'title': re.compile(r'Followers')})
        if followers_elem:
            metadata['followers'] = followers_elem.get_text(strip=True)
        
        # Following
        following_elem = soup.find('strong', {'title': re.compile(r'Following')})
        if following_elem:
            metadata['following'] = following_elem.get_text(strip=True)
        
        # Bio
        bio_elem = soup.find('h2', {'data-e2e': 'user-bio'})
        if bio_elem:
            metadata['bio'] = bio_elem.get_text(strip=True)
        
        return metadata

    # Placeholder methods for other platforms
    async def extract_pinterest_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_medium_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_discord_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_telegram_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_spotify_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_twitch_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_steam_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_soundcloud_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_vimeo_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_dribbble_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_behance_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_codepen_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_deviantart_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_flickr_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_mastodon_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_patreon_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_substack_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_threads_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_bluesky_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_aboutme_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_carrd_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_linktree_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_taplink_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_biolink_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_bento_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_manylink_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_beacons_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_campsite_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_milkshake_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_hub_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_kofi_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_buymeacoffee_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_gumroad_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_onlyfans_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_fansly_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_justforfans_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}
    
    async def extract_adultcontent_advanced(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        return {}

    def get_chained_usernames(self) -> List[str]:
        """Get all extracted usernames for chaining."""
        return list(self.extracted_usernames)
    
    def get_chained_emails(self) -> List[str]:
        """Get all extracted emails for chaining."""
        return list(self.extracted_emails)
    
    def get_chained_urls(self) -> List[str]:
        """Get all extracted URLs for chaining."""
        return list(self.extracted_urls)
    
    def clear_chained_data(self):
        """Clear chained data for new investigation."""
        self.extracted_usernames.clear()
        self.extracted_emails.clear()
        self.extracted_urls.clear()
