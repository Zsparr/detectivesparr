# Detective - Advanced OSINT Toolkit

A comprehensive Python CLI tool for OSINT (Open Source Intelligence) investigations with powerful features for digital forensics, security research, and online investigations.

## Core Features

### 1. **Username Search** - Enhanced Social Media Discovery
- Search across **300+** social media platforms
- **NEW:** Generate username variations automatically
- **NEW:** Extract profile metadata (followers, bio, etc.)
- **NEW:** Support for multiple username formats
- Async HTTP requests for maximum speed
- Color-coded results with detailed information

### 2. **Search by Real Name** - NEW! 
- **NEW:** Search for people using their real names
- **NEW:** Intelligent username generation from names
- **NEW:** Profile discovery with confidence scoring
- **NEW:** Display names, bios, and profile details
- **NEW:** Cross-platform name matching
- **NEW:** Export results for further analysis

### 3. **Data Breach Check** - Email & Phone Analysis
- Verify if email addresses or phone numbers have been exposed
- **NEW:** Enhanced breach data analysis
- Detailed breach information with dates and data types
- Support for international phone formats
- Integration with XposedOrNot API

### 4. **Domain/URL Investigation** - Complete Domain Intelligence
- **NEW:** WHOIS lookup with comprehensive details
- **NEW:** DNS record analysis (A, AAAA, MX, NS, TXT, CNAME, SOA)
- **NEW:** Subdomain enumeration with common patterns
- **NEW:** Website security header analysis
- **NEW:** Web technology and metadata extraction

### 5. **IP Address Analysis** - Network Intelligence
- **NEW:** Geolocation and ISP information via IPInfo
- **NEW:** Reverse DNS lookup
- **NEW:** Open port scanning (common ports)
- **NEW:** VirusTotal integration for threat intelligence
- **NEW:** Shodan integration for device enumeration
- Support for both IPv4 and IPv6

### 6. **Email Header Analysis** - Email Forensics
- **NEW:** Complete email header parsing
- **NEW:** SPF, DKIM, and DMARC authentication analysis
- **NEW:** Email path tracing through Received headers
- **NEW:** Spoofing detection and security analysis
- **NEW:** IP extraction from email headers

### 7. **Batch Processing** - Mass Investigation Tools
- **NEW:** Batch username searches
- **NEW:** Batch breach checks
- **NEW:** Batch domain investigations
- **NEW:** Batch IP analyses
- **NEW:** Progress tracking and summary reports
- Support for CSV, TXT, and JSON input files

### 8. **Data Export & Reporting**
- **NEW:** Professional PDF reports with formatting
- **NEW:** JSON export for data analysis
- **NEW:** CSV export for spreadsheet analysis
- **NEW:** Automated report generation
- **NEW:** Customizable export formats

### 9. **Configuration Management**
- **NEW:** Persistent configuration system
- **NEW:** User preferences and settings
- **NEW:** Investigation parameters customization
- **NEW:** First-time setup wizard
- **NEW:** Configuration import/export

### 10. **API Integration**
- **NEW:** VirusTotal API for threat intelligence
- **NEW:** Shodan API for device discovery
- **NEW:** IPInfo API for geolocation
- **NEW:** Hunter API for email verification
- **NEW:** API key testing and validation
- **NEW:** Rate limiting and error handling

## Prerequisites

- [Python 3.7+](https://www.python.org/downloads/) installed on your system
- `pip` (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd Detective
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Main Menu Options

Run `python main.py` to access the interactive menu with these options:

- **[1]** Username Check - Enhanced social media search
- **[2]** Email & Phone Data Breach Check
- **[3]** Domain/URL Investigation - NEW!
- **[4]** IP Address Analysis - NEW!
- **[5]** Email Header Analysis - NEW!
- **[6]** Batch Processing - NEW!
- **[7]** Configuration & API Management - NEW!
- **[8]** Advanced Username Search - NEW!
- **[9]** Search by Real Name - NEW!
- **[0]** Exit

### API Keys (Optional but Recommended)

For enhanced features, configure API keys:

1. **VirusTotal** - Get threat intelligence for IPs and domains
   - Free tier: 500 requests/day
   - Sign up: https://www.virustotal.com/

2. **Shodan** - Device and service enumeration
   - Free tier: 1,000 requests/month
   - Sign up: https://www.shodan.io/

3. **IPInfo** - Enhanced geolocation and ISP data
   - Free tier: 50,000 requests/month
   - Sign up: https://ipinfo.io/

4. **Hunter** - Email domain verification
   - Free tier: 100 requests/month
   - Sign up: https://hunter.io/

### Configuration Features

The tool includes a comprehensive configuration system:

- **Auto-export settings** - Automatically save results
- **Metadata extraction** - Toggle profile data collection
- **Username variations** - Generate alternative usernames
- **Rate limiting** - Respect API limits
- **Batch processing** - Configure mass investigation settings
- **Security options** - Tor support and proxy settings

### Batch Processing

Process multiple targets at once:

1. Create input files (CSV, TXT, or JSON format)
2. Select batch processing from menu
3. Choose investigation type
4. Load file or enter targets manually
5. Get comprehensive reports with statistics

### Export Formats

All investigations support multiple export formats:

- **PDF** - Professional reports with tables and formatting
- **JSON** - Machine-readable data for further analysis
- **CSV** - Spreadsheet-compatible format

## Advanced Features

### Username Variations
Automatically generate common username variations:
- Format variations (john_doe, johndoe, john.doe)
- Common prefixes/suffixes (the_real_john, john_official)
- Number variations (john123, john01)
- CamelCase separation (JohnDoe → john.doe)

### Metadata Extraction
Extract rich metadata from found profiles:
- Follower/following counts
- Profile bios and descriptions
- Account verification status
- Profile images and media
- Join dates and activity

### Security Analysis
Advanced security features:
- Email spoofing detection
- Authentication result analysis
- Malicious IP/domain detection
- Open port vulnerability scanning
- Website security header analysis

## File Structure

```
Detective/
├── main.py                 # Main application entry point
├── searcher.py             # Username search engine
├── breach_checker.py       # Data breach investigation
├── domain_investigator.py   # Domain intelligence (NEW!)
├── ip_analyzer.py          # IP address analysis (NEW!)
├── email_analyzer.py       # Email forensics (NEW!)
├── batch_processor.py      # Mass investigation tools (NEW!)
├── export_manager.py       # Report generation (NEW!)
├── config_manager.py       # Configuration system (NEW!)
├── api_manager.py          # API integration (NEW!)
├── sites.json             # Social media site definitions
├── config.json            # User configuration (auto-generated)
├── requirements.txt        # Python dependencies
└── exports/              # Generated reports (auto-created)
```

## Customization

### Adding Social Media Sites

Site sources auto-merge (deduped): `sites.json`, `sites_extra.json`, `sites_extended.json` (extended platform list ~300+ platforms). Add your own list to any of these or create a new JSON file and add it to `site_sources` in `config.json`.

Sample entry:

```json
{
  "name": "New Platform",
  "url": "https://example.com/user/{}",
  "check_type": "status_code",
  "expected_status": 200,
  "headers": {
    "User-Agent": "Custom-Agent"
  }
}
```

### Configuration Options

Key configuration settings in `config.json`:

```json
{
  "preferences": {
    "default_export_format": "pdf",
    "auto_export": true,
    "enable_metadata_extraction": true,
    "generate_username_variations": true,
    "randomize_site_order": false,
    "max_sites_to_check": 0,
    "retry_attempts": 2,
    "concurrency_limit": 50,
    "request_timeout": 10
  },
  "site_sources": ["sites.json", "sites_extra.json", "sites_extended.json"],
  "investigation_settings": {
    "username_variations_count": 10,
    "check_open_ports": false,
    "subdomain_scan_depth": "basic"
  }
}
```

## Privacy & Security

- **Local Processing**: Most operations work without external APIs
- **Optional APIs**: API keys are optional but enhance functionality
- **No Data Storage**: Your searches are not stored locally
- **Secure Headers**: Uses proper user agents and headers
- **Rate Limiting**: Respects service limits to avoid blocking

## Examples

### Basic Username Search
```bash
python main.py
# Select option 1
# Enter: john_doe
# Choose: Generate variations? y
# Choose: Extract metadata? y
```

### Domain Investigation
```bash
python main.py
# Select option 3
# Enter: example.com
# Get WHOIS, DNS, subdomains, web info
```

### Batch Processing
```bash
# Create usernames.txt
echo -e "john_doe\njane_smith\nbob_wilson" > usernames.txt

python main.py
# Select option 6 → 1
# Load from file: usernames.txt
# Get comprehensive batch report
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **API Failures**: Check API keys in configuration
3. **Rate Limits**: Wait between requests or upgrade API plans
4. **SSL Errors**: Some sites may have certificate issues
5. **Timeouts**: Increase timeout in configuration

### Debug Mode

Enable verbose output in configuration:
```json
{
  "ui_settings": {
    "verbose_output": true,
    "show_progress_bars": true
  }
}
```

## Contributing

Contributions welcome! Areas for enhancement:
- Additional social media platforms
- New API integrations
- UI/UX improvements
- Performance optimizations
- Documentation improvements

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Changelog

### v2.1.0 - Name Search Enhancement Release
- ✨ **NEW:** Search by Real Name feature
- ✨ **NEW:** Intelligent username generation from real names
- ✨ **NEW:** Cross-platform profile discovery with confidence scoring
- ✨ **NEW:** Display names, bios, and detailed profile information
- ✨ **NEW:** Advanced username search with deep profile chaining
- ✨ **NEW:** Enhanced metadata extraction and analysis
- 🔧 Fixed username chainer duplicate method bug
- 🔧 Improved error handling and performance optimizations
- 🔧 Enhanced result display with color-coded confidence levels

### v2.0.0 - Major Enhancement Release
- ✨ Added domain investigation with WHOIS/DNS/subdomains
- ✨ Added IP address analysis with geolocation and security
- ✨ Added email header analysis for forensics
- ✨ Added batch processing for mass investigations
- ✨ Added professional PDF/JSON/CSV export
- ✨ Added configuration management system
- ✨ Added API key management and testing
- ✨ Enhanced username search with metadata extraction
- ✨ Added username variation generation
- 🔧 Improved error handling and rate limiting
- 🔧 Added first-time setup wizard

### v1.0.0 - Initial Release
- ✅ Basic username search across 100+ platforms
- ✅ Email and phone breach checking
- ✅ Color-coded terminal output
- ✅ Async performance optimization

---

**Detective** - Your comprehensive OSINT toolkit for digital investigations and security research.
