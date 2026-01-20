import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class AdvancedReporter:
    """Generate comprehensive reports (HTML, PDF, XMind)."""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_html_report(self, report_data: Dict[str, Any], username: str) -> str:
        """Generate comprehensive HTML report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detective Report - {username}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .profile {{ border-left: 4px solid #4CAF50; padding: 15px; margin: 10px 0; background: #f9f9f9; }}
        .profile.error {{ border-left-color: #f44336; }}
        .profile-name {{ font-weight: bold; font-size: 1.2em; color: #333; }}
        .profile-url {{ color: #667eea; text-decoration: none; }}
        .profile-url:hover {{ text-decoration: underline; }}
        .metadata {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        .tag {{ background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block; font-size: 0.8em; }}
        .categories {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }}
        .category {{ background: #f3e5f5; padding: 10px; border-radius: 6px; }}
        .recursive {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
        .username-tree {{ margin: 20px 0; }}
        .tree-node {{ margin-left: 20px; padding: 10px; border-left: 2px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Detective Investigation Report</h1>
        <h2>{username}</h2>
        <p>Generated on {timestamp}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{report_data.get('statistics', {}).get('total_sites_checked', 0)}</div>
            <div>Sites Checked</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{report_data.get('statistics', {}).get('profiles_found', 0)}</div>
            <div>Profiles Found</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{report_data.get('statistics', {}).get('success_rate', 0):.1f}%</div>
            <div>Success Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(report_data.get('additional_usernames', []))}</div>
            <div>Additional Usernames</div>
        </div>
    </div>
    
    {self._generate_profiles_section(report_data.get('found_profiles', []))}
    
    {self._generate_categories_section(report_data.get('categories', {}))}
    
    {self._generate_recursive_section(report_data)}
    
    {self._generate_errors_section(report_data.get('errors', []))}
    
    <div class="section">
        <h3>📊 Raw Data</h3>
        <button onclick="toggleRawData()">Show/Hide JSON</button>
        <pre id="rawData" style="display:none; background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">
{json.dumps(report_data, indent=2, ensure_ascii=False)}
        </pre>
    </div>
    
    <script>
        function toggleRawData() {{
            document.getElementById('rawData').style.display = 
                document.getElementById('rawData').style.display === 'none' ? 'block' : 'none';
        }}
    </script>
</body>
</html>
        """
        
        filename = self.output_dir / f"advanced_report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        return str(filename)
    
    def _generate_profiles_section(self, profiles: List[Dict[str, Any]]) -> str:
        """Generate HTML section for found profiles."""
        if not profiles:
            return ""
        
        html = '<div class="section"><h3>🎯 Found Profiles</h3>'
        
        for profile in profiles:
            css_class = "profile" if not profile.get('error') else "profile error"
            html += f'''
            <div class="{css_class}">
                <div class="profile-name">{profile['name']}</div>
                <a href="{profile['url']}" class="profile-url" target="_blank">{profile['url']}</a>
                {self._generate_metadata_html(profile.get('metadata', {}))}
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_metadata_html(self, metadata: Dict[str, Any]) -> str:
        """Generate HTML for profile metadata."""
        if not metadata:
            return ""
        
        html = '<div class="metadata">'
        
        for key, value in metadata.items():
            if key == 'links' and isinstance(value, list):
                html += f'<div><strong>Links:</strong> '
                html += ', '.join(f'<a href="{link}" target="_blank">{link}</a>' for link in value)
                html += '</div>'
            elif key not in ['extraction_error', 'site_name', 'profile_url', 'extraction_time']:
                html += f'<div><strong>{key.title()}:</strong> {value}</div>'
        
        html += '</div>'
        return html
    
    def _generate_categories_section(self, categories: Dict[str, List[str]]) -> str:
        """Generate HTML section for profile categories."""
        if not categories:
            return ""
        
        html = '<div class="section"><h3>📂 Profile Categories</h3><div class="categories">'
        
        for category, sites in categories.items():
            html += f'''
            <div class="category">
                <strong>{category.title()}</strong>
                <div>{', '.join(sites)}</div>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    def _generate_recursive_section(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML section for recursive search results."""
        if 'search_tree' not in report_data or len(report_data['search_tree']) <= 1:
            return ""
        
        html = '<div class="section recursive"><h3>🔄 Recursive Search Results</h3>'
        html += '<div class="username-tree">'
        
        for username, results in report_data['search_tree'].items():
            html += f'''
            <div class="tree-node">
                <strong>{username}</strong> - {len(results.get('found_profiles', []))} profiles
                {len(results.get('additional_usernames', []))} new usernames discovered
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    def _generate_errors_section(self, errors: List[Dict[str, Any]]) -> str:
        """Generate HTML section for errors and blocking."""
        if not errors:
            return ""
        
        html = '<div class="section"><h3>⚠️ Errors & Blocking</h3>'
        
        for error in errors:
            blocking = error.get('blocking_detection', {})
            if blocking.get('detected'):
                detected_types = ', '.join(blocking['detected'])
                html += f'''
                <div class="profile error">
                    <div class="profile-name">{error['name']}</div>
                    <div><strong>Blocking detected:</strong> {detected_types}</div>
                    <div><strong>Status:</strong> {error.get('status', 'Unknown')}</div>
                </div>
                '''
            else:
                html += f'''
                <div class="profile error">
                    <div class="profile-name">{error['name']}</div>
                    <div><strong>Error:</strong> {error.get('error', 'Unknown error')}</div>
                </div>
                '''
        
        html += '</div>'
        return html
    
    def generate_json_report(self, report_data: Dict[str, Any], username: str) -> str:
        """Generate JSON report for further processing."""
        filename = self.output_dir / f"advanced_report_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(filename)
    
    def generate_csv_summary(self, report_data: Dict[str, Any], username: str) -> str:
        """Generate CSV summary of found profiles."""
        import csv
        
        filename = self.output_dir / f"advanced_summary_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        profiles = report_data.get('found_profiles', [])
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Site', 'URL', 'Status', 'Response Time (ms)', 'Metadata'])
            
            for profile in profiles:
                metadata_str = json.dumps(profile.get('metadata', {})) if profile.get('metadata') else ''
                writer.writerow([
                    profile.get('name', ''),
                    profile.get('url', ''),
                    'Found' if profile.get('found') else 'Not Found',
                    profile.get('elapsed_ms', ''),
                    metadata_str
                ])
        
        return str(filename)
