#!/usr/bin/env python3
"""
arXiv Numerical Relativity Papers Scraper
Fetches recent papers with 'numerical relativity' keywords and generates an HTML page.
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
import argparse
from typing import List, Dict
import os

class ArxivPaper:
    """Class to represent an arXiv paper."""
    
    def __init__(self, title: str, authors: List[str], abstract: str, 
                 arxiv_id: str, published: str, updated: str, categories: List[str]):
        self.title = title.strip()
        self.authors = authors
        self.abstract = abstract.strip()
        self.arxiv_id = arxiv_id
        self.published = published
        self.updated = updated
        self.categories = categories
        self.arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
        self.pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

def search_arxiv(query: str, max_results: int = 50, days_back: int = 30) -> List[ArxivPaper]:
    """
    Search arXiv for papers matching the query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        days_back: How many days back to search
        
    Returns:
        List of ArxivPaper objects
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # arXiv API URL
    base_url = "http://export.arxiv.org/api/query"
    
    # Build search query
    search_query = f'all:"{query}"'
    
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    print(f"Searching arXiv for: {query}")
    print(f"Looking for papers from the last {days_back} days...")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from arXiv: {e}")
        return []
    
    # Parse XML response
    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        return []
    
    # Extract papers
    papers = []
    namespace = {'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'}
    
    entries = root.findall('atom:entry', namespace)
    print(f"Found {len(entries)} total papers")
    
    for entry in entries:
        try:
            # Extract basic info
            title = entry.find('atom:title', namespace).text
            title = re.sub(r'\s+', ' ', title)  # Clean whitespace
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', namespace):
                name = author.find('atom:name', namespace).text
                authors.append(name)
            
            # Extract abstract
            abstract = entry.find('atom:summary', namespace).text
            abstract = re.sub(r'\s+', ' ', abstract)  # Clean whitespace
            
            # Extract arXiv ID
            arxiv_id = entry.find('atom:id', namespace).text.split('/')[-1]
            
            # Extract dates
            published = entry.find('atom:published', namespace).text
            updated_elem = entry.find('atom:updated', namespace)
            updated = updated_elem.text if updated_elem is not None else published
            
            # Extract categories
            categories = []
            for category in entry.findall('atom:category', namespace):
                categories.append(category.get('term'))
            
            # Check if paper is within date range
            published_date = datetime.fromisoformat(published.replace('Z', '+00:00')).replace(tzinfo=None)
            if published_date >= start_date:
                paper = ArxivPaper(title, authors, abstract, arxiv_id, 
                                 published, updated, categories)
                papers.append(paper)
            
        except Exception as e:
            print(f"Error processing entry: {e}")
            continue
    
    print(f"Found {len(papers)} papers from the last {days_back} days")
    return papers

def generate_html(papers: List[ArxivPaper], output_file: str = "index.html"):
    """
    Generate HTML page with the papers.
    
    Args:
        papers: List of ArxivPaper objects
        output_file: Output HTML file path
    """
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recent Numerical Relativity Papers - arXiv</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        
        .container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
        }}
        
        .header h1 {{
            color: #007bff;
            margin: 0;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            color: #6c757d;
            font-size: 1.1em;
            margin: 10px 0;
        }}
        
        .last-updated {{
            color: #6c757d;
            font-size: 0.9em;
            margin: 5px 0;
        }}
        
        .paper-count {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .paper {{
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin: 20px 0;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .paper:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .paper-header {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 10px;
        }}
        
        .paper-date {{
            font-size: 0.9em;
            color: #6c757d;
            font-weight: bold;
            min-width: 100px;
            flex-shrink: 0;
            padding-top: 2px;
        }}
        
        .paper-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            flex: 1;
            line-height: 1.3;
        }}
        
        .paper-title a {{
            color: #007bff;
            text-decoration: none;
        }}
        
        .paper-title a:hover {{
            text-decoration: underline;
        }}
        
        .paper-authors {{
            color: #6c757d;
            margin-bottom: 15px;
            font-style: italic;
            font-size: 0.95em;
        }}
        
        .abstract-toggle {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px 15px;
            margin: 10px 0;
            cursor: pointer;
            user-select: none;
            font-size: 0.9em;
            color: #495057;
            transition: background-color 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .abstract-toggle:hover {{
            background: #e9ecef;
        }}
        
        .abstract-toggle .arrow {{
            transition: transform 0.2s ease;
            font-weight: bold;
        }}
        
        .abstract-toggle.expanded .arrow {{
            transform: rotate(90deg);
        }}
        
        .paper-abstract {{
            display: none;
            text-align: justify;
            margin: 0 0 15px 0;
            line-height: 1.7;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        
        .paper-abstract.show {{
            display: block;
        }}
        
        .no-papers {{
            text-align: center;
            color: #6c757d;
            font-style: italic;
            margin: 40px 0;
            font-size: 1.1em;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .github-link {{
            color: #007bff;
            text-decoration: none;
        }}
        
        .github-link:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .container {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .paper {{
                padding: 20px;
            }}
            
            .paper-header {{
                flex-direction: column;
                gap: 5px;
            }}
            
            .paper-date {{
                min-width: auto;
                font-size: 0.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📡 Numerical Relativity Papers</h1>
            <div class="subtitle">Recent papers from arXiv</div>
            <div class="last-updated">Last updated: {timestamp}</div>
            <div class="paper-count">{len(papers)} papers found</div>
        </div>
        
        <main>
"""

    if not papers:
        html_content += """
            <div class="no-papers">
                <p>No recent papers found with "numerical relativity" keywords.</p>
                <p>Check back later for new submissions!</p>
            </div>
"""
    else:
        for paper in papers:
            # Format publication date
            pub_date = datetime.fromisoformat(paper.published.replace('Z', '+00:00'))
            formatted_date = pub_date.strftime("%B %d, %Y")
            
            # Format authors (limit to first 5 for display)
            if len(paper.authors) > 5:
                authors_display = ", ".join(paper.authors[:5]) + f" and {len(paper.authors) - 5} others"
            else:
                authors_display = ", ".join(paper.authors)
            
            # Truncate abstract if too long
            abstract = paper.abstract
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            html_content += f"""
            <article class="paper">
                <div class="paper-header">
                    <div class="paper-date">{formatted_date}</div>
                    <div class="paper-title">
                        <a href="{paper.arxiv_url}" target="_blank" rel="noopener">{paper.title}</a>
                    </div>
                </div>
                <div class="paper-authors">{authors_display}</div>
                <div class="abstract-toggle">
                    <span class="arrow">▶</span>
                    <span>Show Abstract</span>
                </div>
                <div class="paper-abstract">{abstract}</div>
            </article>
"""

    html_content += f"""
        </main>
        
        <footer class="footer">
            <p>
                Generated automatically from arXiv.org • 
                <a href="https://github.com/yourusername/UKNR_papers" class="github-link" target="_blank" rel="noopener">
                    View on GitHub
                </a>
            </p>
            <p>Data provided by <a href="https://arxiv.org/" target="_blank" rel="noopener" class="github-link">arXiv.org</a></p>
        </footer>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const toggles = document.querySelectorAll('.abstract-toggle');
            toggles.forEach(function(toggle) {{
                toggle.addEventListener('click', function() {{
                    this.classList.toggle('expanded');
                    const abstract = this.nextElementSibling;
                    abstract.classList.toggle('show');
                }});
            }});
        }});
    </script>
</body>
</html>"""

    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file generated: {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Scrape arXiv for numerical relativity papers')
    parser.add_argument('--query', default='numerical relativity', 
                       help='Search query (default: "numerical relativity")')
    parser.add_argument('--max-results', type=int, default=50,
                       help='Maximum number of results (default: 50)')
    parser.add_argument('--days-back', type=int, default=30,
                       help='How many days back to search (default: 30)')
    parser.add_argument('--output', default='index.html',
                       help='Output HTML file (default: index.html)')
    
    args = parser.parse_args()
    
    # Search arXiv
    papers = search_arxiv(args.query, args.max_results, args.days_back)
    
    # Generate HTML
    generate_html(papers, args.output)
    
    print(f"Done! Found {len(papers)} papers and generated {args.output}")

if __name__ == "__main__":
    main()
