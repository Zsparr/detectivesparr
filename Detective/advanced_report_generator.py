import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
from io import BytesIO
import logging

# For HTML reports
from jinja2 import Template

# For PDF reports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("ReportLab not available. PDF reports will be disabled.")

# For mindmaps
try:
    import graphviz
    MINDMAP_AVAILABLE = True
except ImportError:
    MINDMAP_AVAILABLE = False
    logging.warning("Graphviz not available. Mindmap generation will be disabled.")

class AdvancedReportGenerator:
    """Advanced report generation system supporting HTML, PDF, and mindmaps."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # HTML template
        self.html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detective OSINT Report - {{ username }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .summary-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .summary-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .summary-card .label {
            color: #666;
            font-size: 0.9em;
        }
        
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .section-header {
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .section-content {
            padding: 25px;
        }
        
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .profile-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            background: #fafafa;
        }
        
        .profile-card.found {
            border-left: 4px solid #4caf50;
            background: #f1f8e9;
        }
        
        .profile-card.not-found {
            border-left: 4px solid #f44336;
            background: #ffebee;
            opacity: 0.7;
        }
        
        .profile-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .profile-image {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 15px;
            object-fit: cover;
        }
        
        .profile-info h4 {
            color: #333;
            margin-bottom: 5px;
        }
        
        .profile-info .platform {
            color: #666;
            font-size: 0.9em;
        }
        
        .profile-stats {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat .number {
            font-weight: bold;
            color: #667eea;
        }
        
        .stat .label {
            font-size: 0.8em;
            color: #666;
        }
        
        .profile-bio {
            font-size: 0.9em;
            color: #555;
            margin-top: 10px;
            font-style: italic;
        }
        
        .chain-visualization {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .chain-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }
        
        .chain-confidence {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .confidence-high {
            background: #4caf50;
            color: white;
        }
        
        .confidence-medium {
            background: #ff9800;
            color: white;
        }
        
        .confidence-low {
            background: #f44336;
            color: white;
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .metadata-item {
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
        }
        
        .metadata-item strong {
            color: #667eea;
        }
        
        .social-links {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 10px;
        }
        
        .social-link {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            text-decoration: none;
            font-size: 0.8em;
        }
        
        .social-link:hover {
            background: #5a6fd8;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .profile-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Detective OSINT Report</h1>
            <div class="subtitle">Username Investigation: {{ username }}</div>
            <div class="subtitle">Generated: {{ timestamp }}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Profiles Found</h3>
                <div class="number">{{ summary.total_profiles_found }}</div>
                <div class="label">across {{ summary.platforms_checked }} platforms</div>
            </div>
            
            <div class="summary-card">
                <h3>Chain Depth</h3>
                <div class="number">{{ summary.max_chain_depth }}</div>
                <div class="label">levels deep</div>
            </div>
            
            <div class="summary-card">
                <h3>Chains Discovered</h3>
                <div class="number">{{ summary.total_chains }}</div>
                <div class="label">username connections</div>
            </div>
            
            <div class="summary-card">
                <h3>High Confidence</h3>
                <div class="number">{{ summary.high_confidence_chains }}</div>
                <div class="label">strong matches</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">Discovered Profiles</div>
            <div class="section-content">
                <div class="profile-grid">
                    {% for profile in profiles %}
                    <div class="profile-card {% if profile.found %}found{% else %}not-found{% endif %}">
                        <div class="profile-header">
                            {% if profile.metadata.profile_images %}
                                <img src="{{ profile.metadata.profile_images[0] }}" alt="Profile" class="profile-image">
                            {% else %}
                                <div class="profile-image" style="background: #ddd; display: flex; align-items: center; justify-content: center; color: #666;">No Image</div>
                            {% endif %}
                            <div class="profile-info">
                                <h4>{{ profile.platform }}</h4>
                                <div class="platform">{{ profile.username }}</div>
                            </div>
                        </div>
                        
                        {% if profile.found %}
                            <div class="profile-stats">
                                {% if profile.metadata.followers %}
                                    <div class="stat">
                                        <div class="number">{{ profile.metadata.followers }}</div>
                                        <div class="label">Followers</div>
                                    </div>
                                {% endif %}
                                {% if profile.metadata.following %}
                                    <div class="stat">
                                        <div class="number">{{ profile.metadata.following }}</div>
                                        <div class="label">Following</div>
                                    </div>
                                {% endif %}
                                {% if profile.metadata.posts %}
                                    <div class="stat">
                                        <div class="number">{{ profile.metadata.posts }}</div>
                                        <div class="label">Posts</div>
                                    </div>
                                {% endif %}
                            </div>
                            
                            {% if profile.metadata.bio %}
                                <div class="profile-bio">{{ profile.metadata.bio[:200] }}{% if profile.metadata.bio|length > 200 %}...{% endif %}</div>
                            {% endif %}
                            
                            {% if profile.metadata.location %}
                                <div style="margin-top: 10px;"><strong>Location:</strong> {{ profile.metadata.location }}</div>
                            {% endif %}
                            
                            {% if profile.metadata.verified %}
                                <div style="margin-top: 10px;"><span style="background: #4caf50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">✓ Verified</span></div>
                            {% endif %}
                        {% endif %}
                        
                        <div style="margin-top: 15px;">
                            <a href="{{ profile.url }}" target="_blank" style="color: #667eea; text-decoration: none;">View Profile →</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        {% if chains %}
        <div class="section">
            <div class="section-header">Username Chains</div>
            <div class="section-content">
                <div class="chain-visualization">
                    {% for chain in chains %}
                    <div class="chain-item">
                        <strong>{{ chain.from_username }}</strong> → <strong>{{ chain.to_username }}</strong>
                        <span class="chain-confidence confidence-{{ chain.confidence_level }}">
                            {{ (chain.confidence * 100)|round(0) }}% confidence
                        </span>
                        <div style="margin-top: 5px; color: #666; font-size: 0.9em;">
                            Found on {{ chain.platform }} via {{ chain.source }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}
        
        {% if recommendations %}
        <div class="section">
            <div class="section-header">Recommendations</div>
            <div class="section-content">
                <ul style="padding-left: 20px;">
                    {% for recommendation in recommendations %}
                    <li style="margin-bottom: 10px;">{{ recommendation }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Generated by Detective OSINT Toolkit | {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
        """

    def generate_html_report(self, data: Dict[str, Any], username: str) -> str:
        """Generate comprehensive HTML report."""
        try:
            template = Template(self.html_template)
            
            # Prepare data for template
            template_data = {
                'username': username,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': data.get('summary', {}),
                'profiles': data.get('profiles', []),
                'chains': self._prepare_chains_for_template(data.get('chains', [])),
                'recommendations': data.get('recommendations', [])
            }
            
            html_content = template.render(**template_data)
            
            # Save to file
            filename = f"{username}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            raise

    def generate_pdf_report(self, data: Dict[str, Any], username: str) -> str:
        """Generate PDF report."""
        if not PDF_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation")
        
        try:
            filename = f"{username}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            story.append(Paragraph("Detective OSINT Report", title_style))
            story.append(Paragraph(f"Username Investigation: {username}", styles['Heading2']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Summary
            summary = data.get('summary', {})
            story.append(Paragraph("Summary", styles['Heading2']))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Profiles Found', str(summary.get('total_profiles_found', 0))],
                ['Platforms Checked', str(summary.get('platforms_checked', 0))],
                ['Chain Depth', str(summary.get('max_chain_depth', 0))],
                ['Chains Discovered', str(summary.get('total_chains', 0))],
                ['High Confidence Chains', str(summary.get('high_confidence_chains', 0))]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Profiles
            profiles = data.get('profiles', [])
            if profiles:
                story.append(Paragraph("Discovered Profiles", styles['Heading2']))
                
                for profile in profiles[:10]:  # Limit to first 10 profiles
                    story.append(Paragraph(f"<b>{profile['platform']}</b> - {profile['username']}", styles['Heading3']))
                    
                    if profile.get('found'):
                        metadata = profile.get('metadata', {})
                        
                        # Profile stats
                        stats = []
                        if metadata.get('followers'):
                            stats.append(f"Followers: {metadata['followers']}")
                        if metadata.get('following'):
                            stats.append(f"Following: {metadata['following']}")
                        if metadata.get('posts'):
                            stats.append(f"Posts: {metadata['posts']}")
                        
                        if stats:
                            story.append(Paragraph(" | ".join(stats), styles['Normal']))
                        
                        # Bio
                        if metadata.get('bio'):
                            bio = metadata['bio'][:200] + "..." if len(metadata['bio']) > 200 else metadata['bio']
                            story.append(Paragraph(f"Bio: {bio}", styles['Normal']))
                        
                        # Location
                        if metadata.get('location'):
                            story.append(Paragraph(f"Location: {metadata['location']}", styles['Normal']))
                        
                        # Verified status
                        if metadata.get('verified'):
                            story.append(Paragraph("✓ Verified Account", styles['Normal']))
                    
                    story.append(Paragraph(f"URL: {profile['url']}", styles['Normal']))
                    story.append(Spacer(1, 10))
                
                if len(profiles) > 10:
                    story.append(Paragraph(f"... and {len(profiles) - 10} more profiles", styles['Normal']))
            
            # Chains
            chains = data.get('chains', [])
            if chains:
                story.append(PageBreak())
                story.append(Paragraph("Username Chains", styles['Heading2']))
                
                for chain in chains[:20]:  # Limit to first 20 chains
                    confidence = chain.get('confidence', 0)
                    confidence_text = f"{confidence * 100:.0f}%"
                    
                    chain_text = f"{chain.get('from_username', 'Unknown')} → {chain.get('to_username', 'Unknown')} ({confidence_text} confidence)"
                    story.append(Paragraph(chain_text, styles['Normal']))
                    story.append(Paragraph(f"Found on {chain.get('platform', 'Unknown')} via {chain.get('source', 'Unknown')}", styles['Normal']))
                    story.append(Spacer(1, 5))
                
                if len(chains) > 20:
                    story.append(Paragraph(f"... and {len(chains) - 20} more chains", styles['Normal']))
            
            # Recommendations
            recommendations = data.get('recommendations', [])
            if recommendations:
                story.append(PageBreak())
                story.append(Paragraph("Recommendations", styles['Heading2']))
                
                for recommendation in recommendations:
                    story.append(Paragraph(f"• {recommendation}", styles['Normal']))
                    story.append(Spacer(1, 5))
            
            doc.build(story)
            self.logger.info(f"PDF report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF report: {e}")
            raise

    def generate_mindmap(self, data: Dict[str, Any], username: str) -> str:
        """Generate mindmap visualization."""
        if not MINDMAP_AVAILABLE:
            raise ImportError("Graphviz is required for mindmap generation")
        
        try:
            filename = f"{username}_mindmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create mindmap
            dot = graphviz.Digraph(comment=f'Username Investigation Mindmap: {username}',
                                 graph_attr={'rankdir': 'LR', 'splines': 'ortho'},
                                 node_attr={'shape': 'box', 'style': 'rounded,filled', 'fontname': 'Arial'},
                                 edge_attr={'fontname': 'Arial'})
            
            # Central node
            dot.node(username, username, fillcolor='lightblue', fontsize='14', fontweight='bold')
            
            # Platform nodes
            profiles = data.get('profiles', [])
            platform_nodes = {}
            
            for profile in profiles:
                if profile.get('found'):
                    platform = profile['platform']
                    profile_username = profile['username']
                    
                    # Platform node
                    platform_node = f"{platform}_{profile_username}"
                    platform_nodes[platform_node] = platform
                    
                    # Color based on verification status
                    metadata = profile.get('metadata', {})
                    if metadata.get('verified'):
                        fillcolor = 'lightgreen'
                    else:
                        fillcolor = 'lightyellow'
                    
                    dot.node(platform_node, f"{platform}\\n{profile_username}", 
                           fillcolor=fillcolor, fontsize='10')
                    
                    # Edge from central username to platform
                    dot.edge(username, platform_node, label='found on')
            
            # Chain nodes
            chains = data.get('chains', [])
            chain_nodes = set()
            
            for chain in chains:
                from_user = chain.get('from_username')
                to_user = chain.get('to_username')
                confidence = chain.get('confidence', 0)
                platform = chain.get('platform', 'Unknown')
                
                # Create chain nodes if they don't exist
                from_node = f"chain_{from_user}"
                to_node = f"chain_{to_user}"
                
                if from_user != username and from_node not in chain_nodes:
                    dot.node(from_node, from_user, fillcolor='lightpink', fontsize='10')
                    chain_nodes.add(from_node)
                
                if to_user != username and to_node not in chain_nodes:
                    dot.node(to_node, to_user, fillcolor='lightpink', fontsize='10')
                    chain_nodes.add(to_node)
                
                # Edge with confidence label
                edge_label = f"{platform}\\n{confidence*100:.0f}%"
                edge_color = 'green' if confidence > 0.8 else 'orange' if confidence > 0.5 else 'red'
                
                dot.edge(from_node, to_node, label=edge_label, color=edge_color)
            
            # Render mindmap
            dot.render(filepath, format='png', cleanup=True)
            
            self.logger.info(f"Mindmap generated: {filepath}.png")
            return f"{filepath}.png"
            
        except Exception as e:
            self.logger.error(f"Failed to generate mindmap: {e}")
            raise

    def generate_json_report(self, data: Dict[str, Any], username: str) -> str:
        """Generate JSON report for machine processing."""
        try:
            filename = f"{username}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            report_data = {
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to generate JSON report: {e}")
            raise

    def generate_csv_report(self, data: Dict[str, Any], username: str) -> str:
        """Generate CSV report for spreadsheet analysis."""
        try:
            import csv
            
            filename = f"{username}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['username', 'platform', 'url', 'found', 'followers', 'following', 
                            'posts', 'verified', 'bio', 'location', 'profile_images', 'social_links']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                profiles = data.get('profiles', [])
                for profile in profiles:
                    metadata = profile.get('metadata', {})
                    
                    row = {
                        'username': profile.get('username', ''),
                        'platform': profile.get('platform', ''),
                        'url': profile.get('url', ''),
                        'found': profile.get('found', False),
                        'followers': metadata.get('followers', ''),
                        'following': metadata.get('following', ''),
                        'posts': metadata.get('posts', ''),
                        'verified': metadata.get('verified', False),
                        'bio': metadata.get('bio', ''),
                        'location': metadata.get('location', ''),
                        'profile_images': ';'.join(metadata.get('profile_images', [])),
                        'social_links': ';'.join([link.get('url', '') for link in metadata.get('social_links', [])])
                    }
                    
                    writer.writerow(row)
            
            self.logger.info(f"CSV report generated: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV report: {e}")
            raise

    def generate_all_reports(self, data: Dict[str, Any], username: str) -> Dict[str, str]:
        """Generate all available report formats."""
        reports = {}
        
        try:
            # HTML report (always available)
            reports['html'] = self.generate_html_report(data, username)
        except Exception as e:
            self.logger.error(f"HTML report generation failed: {e}")
        
        try:
            # PDF report
            if PDF_AVAILABLE:
                reports['pdf'] = self.generate_pdf_report(data, username)
        except Exception as e:
            self.logger.error(f"PDF report generation failed: {e}")
        
        try:
            # Mindmap
            if MINDMAP_AVAILABLE:
                reports['mindmap'] = self.generate_mindmap(data, username)
        except Exception as e:
            self.logger.error(f"Mindmap generation failed: {e}")
        
        try:
            # JSON report (always available)
            reports['json'] = self.generate_json_report(data, username)
        except Exception as e:
            self.logger.error(f"JSON report generation failed: {e}")
        
        try:
            # CSV report (always available)
            reports['csv'] = self.generate_csv_report(data, username)
        except Exception as e:
            self.logger.error(f"CSV report generation failed: {e}")
        
        return reports

    def _prepare_chains_for_template(self, chains: List[Dict]) -> List[Dict]:
        """Prepare chains data for HTML template."""
        prepared_chains = []
        
        for chain in chains:
            confidence = chain.get('confidence', 0)
            
            # Determine confidence level
            if confidence > 0.8:
                confidence_level = 'high'
            elif confidence > 0.5:
                confidence_level = 'medium'
            else:
                confidence_level = 'low'
            
            prepared_chain = chain.copy()
            prepared_chain['confidence_level'] = confidence_level
            
            prepared_chains.append(prepared_chain)
        
        return prepared_chains
