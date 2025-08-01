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

# Configuration: Add author names here to automatically include their papers
# These authors' papers will be included even if they don't contain the main search keywords
TARGET_AUTHORS = [
    "Clough, Katy",              # Queen Mary University of London
    # Examples of other prominent numerical relativity researchers:
    # "Pretorius, Frans",           # Princeton University
    # "Campanelli, Manuela",       # RIT
    # "Zlochower, Yosef",          # RIT  
    # "Lousto, Carlos O.",         # RIT
    # "Buonanno, Alessandra",      # Max Planck Institute
    # "Pfeiffer, Harald P.",       # Max Planck Institute
    # "Kidder, Lawrence E.",       # Cornell University
    # "Teukolsky, Saul A.",        # Cornell University
    # "Schnetter, Erik",           # Perimeter Institute
    # "Rezzolla, Luciano",         # Goethe University Frankfurt
    # Add/remove authors as needed - use format "Last, First" or partial names
]

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

def search_arxiv(query: str, max_results: int = 50, days_back: int = 30, target_authors: List[str] = None) -> List[ArxivPaper]:
    """
    Search arXiv for papers matching the query or from specific authors.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        days_back: How many days back to search
        target_authors: List of author names to search for (optional)
        
    Returns:
        List of ArxivPaper objects
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # arXiv API URL
    base_url = "http://export.arxiv.org/api/query"
    
    all_papers = []
    seen_arxiv_ids = set()
    
    # Search for keyword-based papers
    search_query = f'all:"{query}"'
    
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    print(f"Searching arXiv for: {query}")
    keyword_papers = fetch_papers_from_query(base_url, params, start_date)
    
    for paper in keyword_papers:
        if paper.arxiv_id not in seen_arxiv_ids:
            all_papers.append(paper)
            seen_arxiv_ids.add(paper.arxiv_id)
    
    # Search for papers by specific authors if provided
    if target_authors:
        print(f"Also searching for papers by specific authors: {', '.join(target_authors)}")
        for author in target_authors:
            author_query = f'au:"{author}"'
            author_params = {
                'search_query': author_query,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            print(f"  - Searching for papers by: {author}")
            author_papers = fetch_papers_from_query(base_url, author_params, start_date)
            
            for paper in author_papers:
                if paper.arxiv_id not in seen_arxiv_ids:
                    all_papers.append(paper)
                    seen_arxiv_ids.add(paper.arxiv_id)
    
    # Sort all papers by publication date (newest first)
    all_papers.sort(key=lambda p: p.published, reverse=True)
    
    print(f"Found {len(all_papers)} unique papers from the last {days_back} days")
    return all_papers

def fetch_papers_from_query(base_url: str, params: dict, start_date: datetime) -> List[ArxivPaper]:
    """
    Fetch papers from arXiv API for a given query.
    
    Args:
        base_url: arXiv API base URL
        params: Query parameters
        start_date: Earliest date to include papers from
        
    Returns:
        List of ArxivPaper objects
    """
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
    
    return papers

def process_latex_text(text: str) -> str:
    """
    Convert LaTeX text commands to HTML.
    
    Args:
        text: Text possibly containing LaTeX commands
        
    Returns:
        Text with LaTeX commands converted to HTML
    """
    # Replace common LaTeX text commands with HTML equivalents
    import re
    
    # LaTeX accent commands - handle these first before other commands
    accent_map = {
        r"\\'\{([^}]+)\}": lambda m: m.group(1) + '\u0301',  # acute accent combining
        r"\\'([a-zA-Z])": lambda m: m.group(1) + '\u0301',    # acute accent \'a
        r"\\`\{([^}]+)\}": lambda m: m.group(1) + '\u0300',  # grave accent combining
        r"\\`([a-zA-Z])": lambda m: m.group(1) + '\u0300',    # grave accent \`a
        r'\\\^\{([^}]+)\}': lambda m: m.group(1) + '\u0302',  # circumflex combining
        r'\\\^([a-zA-Z])': lambda m: m.group(1) + '\u0302',   # circumflex \^a
        r'\\"\{([^}]+)\}': lambda m: m.group(1) + '\u0308',   # diaeresis combining
        r'\\"([a-zA-Z])': lambda m: m.group(1) + '\u0308',    # diaeresis \"a
        r'\\~\{([^}]+)\}': lambda m: m.group(1) + '\u0303',   # tilde combining
        r'\\~([a-zA-Z])': lambda m: m.group(1) + '\u0303',    # tilde \~a
        r'\\=\{([^}]+)\}': lambda m: m.group(1) + '\u0304',   # macron combining
        r'\\=([a-zA-Z])': lambda m: m.group(1) + '\u0304',    # macron \=a
        r'\\u\{([^}]+)\}': lambda m: m.group(1) + '\u0306',   # breve combining
        r'\\u([a-zA-Z])': lambda m: m.group(1) + '\u0306',    # breve \u{a}
        r'\\v\{([^}]+)\}': lambda m: m.group(1) + '\u030C',   # caron combining
        r'\\v([a-zA-Z])': lambda m: m.group(1) + '\u030C',    # caron \v{a}
        r'\\c\{([^}]+)\}': lambda m: m.group(1) + '\u0327',   # cedilla combining
        r'\\c([a-zA-Z])': lambda m: m.group(1) + '\u0327',    # cedilla \c{c}
    }
    
    # Apply accent transformations
    for pattern, replacement in accent_map.items():
        text = re.sub(pattern, replacement, text)
    
    # Handle escaped underscore
    text = re.sub(r'\\_', '_', text)
    text = re.sub(r'\\%', '%', text)
    
    # Apply all LaTeX text formatting transformations first
    # \emph{text} -> <em>text</em>
    text = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', text)
    
    # \textbf{text} -> <strong>text</strong>
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    
    # \textit{text} -> <em>text</em>
    text = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', text)
    
    # \textsc{text} -> <span style="font-variant: small-caps;">text</span>
    text = re.sub(r'\\textsc\{([^}]+)\}', r'<span style="font-variant: small-caps;">\1</span>', text)
    
    # \texttt{text} -> <code>text</code>
    text = re.sub(r'\\texttt\{([^}]+)\}', r'<code>\1</code>', text)
    
    # \textrm{text} -> <span style="font-style: normal;">text</span>
    text = re.sub(r'\\textrm\{([^}]+)\}', r'<span style="font-style: normal;">\1</span>', text)
    
    return text

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
    <script>
    MathJax = {{
        tex: {{
            inlineMath: [['$', '$']],
            displayMath: [['$$', '$$']],
            processEscapes: true,
            processEnvironments: true
        }},
        options: {{
            ignoreHtmlClass: 'tex2jax_ignore',
            processHtmlClass: 'tex2jax_process'
        }}
    }};
    </script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
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
            margin-bottom: 30px;
            border-bottom: 2px solid #45818e;
            padding-bottom: 15px;
        }}
        
        .header h1 {{
            color: #45818e;
            margin: 0 0 5px 0;
            font-size: 2.2em;
        }}
        
        .last-updated {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .paper {{
            margin: 3px 0;
            padding: 3px 0;
            border-bottom: 1px solid #e9ecef;
            transition: transform 0.2s ease;
        }}
        
        .paper:hover {{
            transform: translateY(-1px);
        }}
        
        .paper:last-child {{
            border-bottom: none;
        }}
        
        .paper-header {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 1px;
        }}
        
        .paper-date {{
            font-size: 0.85em;
            color: #6c757d;
            font-weight: bold;
            min-width: 90px;
            flex-shrink: 0;
            padding-top: 4px;
            padding-bottom: 4px;
        }}
        
        .paper-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #2c3e50;
            flex: 1;
            line-height: 1.3;
            margin-bottom: 6px;
        }}
        
        .paper-title a {{
            color: #45818e;
            text-decoration: none;
        }}
        
        .paper-title a:hover {{
            text-decoration: underline;
        }}
        
        .paper-meta {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            margin-bottom: 10px;
        }}
        
        .paper-authors {{
            color: #6c757d;
            font-style: italic;
            font-size: 0.9em;
            line-height: 1.4;
            flex: 1;
            padding-top: 4px;
            padding-bottom: 4px;
        }}
        
        .abstract-section {{
            min-width: 90px;
            flex-shrink: 0;
        }}
        
        .abstract-toggle {{
            background: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 4px;
            cursor: pointer;
            user-select: none;
            font-size: 0.8em;
            color: #495057;
            transition: background-color 0.2s ease;
            display: flex;
            align-items: center;
            gap: 4px;
            flex-shrink: 0;
            font-style: normal;
            line-height: 1.4;
        }}
        
        .abstract-toggle:hover {{
            background: #f8f9fa;
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
            margin: 0 0 10px 0;
            line-height: 1.6;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #45818e;
            font-size: 0.9em;
        }}
        
        .paper-abstract.show {{
            display: block;
        }}
        
        .paper-abstract code {{
            background-color: #f1f3f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }}
        
        .paper-abstract [style*="small-caps"], .paper-title [style*="small-caps"] {{
            font-variant: small-caps;
            letter-spacing: 0.05em;
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
            color: #76AFB5;
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
                padding: 15px;
            }}
            
            .header {{
                align-items: flex-start;
                gap: 10px;
            }}
            
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .paper {{
                padding: 15px 0;
            }}
            
            .paper-header {{
                flex-direction: column;
                gap: 5px;
            }}
            
            .paper-date {{
                min-width: auto;
                font-size: 0.8em;
            }}
            
            .paper-meta {{
                flex-direction: column;
                gap: 5px;
            }}
            
            .paper-authors {{
                margin-left: 0;
            }}
            
            .abstract-section {{
                margin-left: 0;
            }}
            
            .abstract-toggle {{
                align-self: flex-start;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Numerical Relativity Papers</h1>
            <div class="last-updated">Last updated: {timestamp}</div>
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
            formatted_date = pub_date.strftime("%d %B %Y")
            
            # Format authors (limit to first 5 for display)
            if len(paper.authors) > 5:
                authors_display = ", ".join(paper.authors[:5]) + f" and {len(paper.authors) - 5} others"
            else:
                authors_display = ", ".join(paper.authors)
            
            # Use full abstract without truncation
            abstract = process_latex_text(paper.abstract)
            title_processed = process_latex_text(paper.title)
            
            html_content += f"""
            <article class="paper">
                <div class="paper-header">
                    <div class="paper-date">{formatted_date}</div>
                    <div class="paper-title">
                        <a href="{paper.arxiv_url}" target="_blank" rel="noopener">{title_processed}</a>
                    </div>
                </div>
                <div class="paper-meta">
                    <div class="abstract-section">
                        <div class="abstract-toggle">
                            <span class="arrow">▶</span>
                            <span>Abstract</span>
                        </div>
                    </div>
                    <div class="paper-authors">{authors_display}</div>
                </div>
                <div class="paper-abstract">{abstract}</div>
            </article>
"""

    html_content += f"""
        </main>
        
        <footer class="footer">
            <p>
                Generated automatically from arXiv.org • 
                <a href="https://github.com/robynlm/UKNR_papers" class="github-link" target="_blank" rel="noopener">
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
                    // Find the abstract element - it's after the paper-meta div
                    const paperMeta = this.closest('.paper-meta');
                    const abstract = paperMeta.nextElementSibling;
                    abstract.classList.toggle('show');
                    
                    // Re-render MathJax for the newly shown abstract
                    if (abstract.classList.contains('show') && window.MathJax) {{
                        MathJax.typesetPromise([abstract]).catch(function (err) {{
                            console.log('MathJax typeset failed: ' + err.message);
                        }});
                    }}
                }});
            }});
            
            // Initial MathJax processing for titles that are already visible
            if (window.MathJax) {{
                MathJax.typesetPromise().catch(function (err) {{
                    console.log('Initial MathJax typeset failed: ' + err.message);
                }});
            }}
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
    parser.add_argument('--authors', nargs='*', default=None,
                       help='List of author names to search for (e.g., --authors "John Doe" "Jane Smith")')
    parser.add_argument('--output', default='index.html',
                       help='Output HTML file (default: index.html)')
    
    args = parser.parse_args()
    
    # Use command line authors if provided, otherwise use configured TARGET_AUTHORS
    authors_to_search = args.authors if args.authors else (TARGET_AUTHORS if TARGET_AUTHORS else None)
    
    # Search arXiv
    papers = search_arxiv(args.query, args.max_results, args.days_back, authors_to_search)
    
    # Generate HTML
    generate_html(papers, args.output)
    
    print(f"Done! Found {len(papers)} papers and generated {args.output}")

if __name__ == "__main__":
    main()
