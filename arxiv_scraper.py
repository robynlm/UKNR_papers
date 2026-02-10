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
import os
import json

# Configuration
DATABASE = "papers.json"
HTML_OUTPUT = "index.html"
NBR_AUTHORS_TO_DISPLAY = 7

# Add author names here to automatically include their papers
# UKNR authors that haven't used "numerical relativity" 
# in their recent paper's title/abstract
TARGET_AUTHORS = [
    "Katy Clough",
    "Harry L. H. Shum",
    "Miguel Bezares",
    "Pau Figueras",
    "Eugene A. Lim"
]

def search_arxiv(query: str, days_back: int = 30, target_authors: list = None) -> list:
    """
    Search arXiv for papers matching the query or from specific authors.
    
    Args:
        query: Search query string
        days_back: How many days back to search
        target_authors: List of author names to search for (optional)
        
    Returns:
        List of dictionary objects
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Search for keyword-based papers
    search_query = f'all:"{query}"'
    print(f"Searching arXiv for: {query}")
    print(f"  -> Keyword query: {search_query} | days_back={days_back}")
    keyword_papers = fetch_papers_from_query(search_query, start_date)
    print(f"  -> Keyword query returned {len(keyword_papers)} papers before filtering")
    
    # Remove duplicates
    all_papers = []
    seen_arxiv_ids = set()
    for paper in keyword_papers:
        if paper['arxiv_id'] not in seen_arxiv_ids:
            all_papers.append(paper)
            seen_arxiv_ids.add(paper['arxiv_id'])
        else:
            print(f"    Skipping duplicate keyword result: {paper['arxiv_id']}")
    print(f"Found {len(all_papers)} unique papers from the last {days_back} days")
    
    # Search for papers by specific authors if provided
    if target_authors:
        print(f"Also searching for papers by specific authors: {', '.join(target_authors)}")
        for author in target_authors:
            author_query = f'au:"{author}"'
            print(f"  - Searching for papers by: {author}")
            print(f"    -> Author query: {author_query}")
            author_papers = fetch_papers_from_query(author_query, start_date)
            print(f"    -> Author query returned {len(author_papers)} papers before filtering")
            
            # Include if not duplicate
            for paper in author_papers:
                if paper['arxiv_id'] not in seen_arxiv_ids:
                    all_papers.append(paper)
                    seen_arxiv_ids.add(paper['arxiv_id'])
                else:
                    print(f"      Skipping duplicate author result: {paper['arxiv_id']}")
    
    # Sort all papers by publication date (newest first)
    all_papers.sort(key=lambda p: p['published'], reverse=True)
    
    print(f"Found {len(all_papers)} unique papers from the last {days_back} days")
    return all_papers

def fetch_papers_from_query(query: str, start_date: datetime) -> list:
    """
    Fetch papers from arXiv API for a given query.
    
    Args:
        query: Search query string
        start_date: Earliest date to include papers from
    
    Returns:
        List of Paper dictionaries with keys
    """
    print(f"    -> Requesting arXiv API with query: {query}")

    # arXiv API URL
    base_url = "http://export.arxiv.org/api/query"
    params = {
        'search_query': query,
        'start': 0,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    try:
        response = requests.get(base_url, params=params, timeout=30)
        print(f"       HTTP {response.status_code} | {len(response.content)} bytes")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from arXiv: {e}")
        return []
    
    # Parse XML response to string
    try:
        root = ET.fromstring(response.content)
        print("       XML parsed successfully")
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        return []
    
    # Extract papers
    papers = []
    namespace = {'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'}
    
    entries = root.findall('atom:entry', namespace)
    print(f"       Found {len(entries)} <entry> elements in feed")
    
    for entry in entries:
        try:
            paper = {}

            # Extract basic info
            paper['title'] = entry.find('atom:title', namespace).text
            paper['title'] = re.sub(r'\s+', ' ', paper['title'])  # Clean whitespace
            
            # Extract authors
            paper['authors'] = []
            for author in entry.findall('atom:author', namespace):
                name = author.find('atom:name', namespace).text
                paper['authors'].append(name)
            
            # Extract abstract
            paper['abstract'] = entry.find('atom:summary', namespace).text
            paper['abstract'] = re.sub(r'\s+', ' ', paper['abstract'])  # Clean whitespace
            
            # Extract arXiv ID
            paper['arxiv_id'] = entry.find('atom:id', namespace).text.split('/')[-1]
            
            # Extract dates
            paper['published'] = entry.find('atom:published', namespace).text
            updated_elem = entry.find('atom:updated', namespace)
            paper['updated'] = updated_elem.text if updated_elem is not None else paper['published']
            
            # Extract categories
            paper['categories'] = []
            for category in entry.findall('atom:category', namespace):
                paper['categories'].append(category.get('term'))
            
            # Check if paper is within date range
            published_date = datetime.fromisoformat(
                paper['published'].replace('Z', '+00:00')).replace(tzinfo=None)
            if published_date >= start_date:
                papers.append(paper)
            else:
                print(f"       Skipping {paper['arxiv_id']} published {published_date} (older than cutoff {start_date})")
            
        except Exception as e:
            print(f"Error processing entry: {e}")
            continue
    
    print(f"       Returning {len(papers)} papers after date filtering")
    return papers

def load_papers_database() -> list:
    """
    Load papers from the JSON database file.
        
    Returns:
        List of dictionary objects
    """
    if not os.path.exists(DATABASE):
        print(f"Database file {DATABASE} not found, starting fresh")
        return []
    
    try:
        with open(DATABASE, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"Loaded {len(papers)} papers from database")
        return papers
    except Exception as e:
        print(f"Error loading database: {e}")
        return []

def merge_papers(existing_papers: list, new_papers: list) -> list:
    """
    Merge new papers into existing papers, avoiding duplicates.
    
    Args:
        existing_papers: Existing papers from database
        new_papers: Newly fetched papers
        
    Returns:
        Merged list of papers
    """

    papers_dict = {paper['arxiv_id']: paper for paper in existing_papers}
    seen_arxiv_ids = set(papers_dict.keys())

    nbr_new = 0
    nbr_updated = 0
    for paper in new_papers:
        arXiv_id = paper['arxiv_id']

        if arXiv_id not in seen_arxiv_ids:
            # Include new paper if it's not already in the database
            papers_dict[arXiv_id] = paper
            seen_arxiv_ids.add(arXiv_id)
            nbr_new += 1
        
        elif paper['updated'] > papers_dict[arXiv_id]['updated']:
            # Update if the new paper has a more recent update date
            papers_dict[arXiv_id] = paper
            nbr_updated += 1

    print(f"Added {nbr_new} new papers, updated {nbr_updated} existing papers")
    
    # Convert back to list and sort by publication date
    merged_papers = list(papers_dict.values())
    merged_papers.sort(key=lambda p: p['published'], reverse=True)
    
    return merged_papers

def prune_old_papers(papers: list, max_age_days: int = 90) -> list:
    """
    Remove papers older than max_age_days.
    
    Args:
        papers: List of dictionary objects
        max_age_days: Maximum age in days to keep papers
        
    Returns:
        List of papers within the age limit
    """
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    pruned_papers = []
    removed_count = 0
    
    for paper in papers:
        published_date = datetime.fromisoformat(
            paper['published'].replace('Z', '+00:00')).replace(tzinfo=None)
        if published_date >= cutoff_date:
            pruned_papers.append(paper)
        else:
            removed_count += 1
    
    if removed_count > 0:
        print(f"Pruned {removed_count} papers older than {max_age_days} days")
    
    return pruned_papers

def save_papers_database(papers: list):
    """
    Save papers to the JSON database file.
    
    Args:
        papers: List of dictionary objects
    """
    try:
        data = papers  # papers are now dictionaries
        with open(DATABASE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(papers)} papers to database")
    except Exception as e:
        print(f"Error saving database: {e}")

def generate_html(papers: list):
    """
    Generate HTML page with the papers.
    
    Args:
        papers: List of dictionary objects
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
        :root {{
            --primary-color: #c16742;
            --text-color: #533a1c;
            --background-color: #ede9d0;
            --card-background: #ede9d0;
            --border-color: #ede9d0;
            --muted-text: #533a1c;
            --secondary-text: #533a1c;
            --light-background: #ede9d0;
            --highlight-background: #ede9d0;
            --button-text: #533a1c;
            --footer-border: #ede9d0;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: var(--background-color);
        }}
        
        .container {{
            background: var(--card-background);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        .header {{
            margin-bottom: 30px;
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 15px;
        }}
        
        .header h1 {{
            color: var(--primary-color);
            margin: 0 0 5px 0;
            font-size: 2.2em;
        }}
        
        .last-updated {{
            color: var(--muted-text);
            font-size: 0.9em;
        }}
        
        .paper {{
            margin: 3px 0;
            padding: 6px 0;
            border-bottom: 1px solid var(--border-color);
            transition: transform 0.2s ease;
            display: grid;
            grid-template-columns: auto 1fr;
            gap: 15px 15px;
            row-gap: 0px;
        }}
        
        .paper:hover {{
            transform: translateY(-1px);
        }}
        
        .paper:last-child {{
            border-bottom: none;
        }}
        
        .paper-date {{
            font-size: 0.85em;
            color: var(--muted-text);
            font-weight: bold;
            padding-top: 4px;
            padding-bottom: 4px;
            grid-column: 1;
            grid-row: 1;
        }}
        
        .paper-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: var(--secondary-text);
            line-height: 1.3;
            margin-bottom: 0;
            grid-column: 2;
            grid-row: 1;
        }}
        
        .paper-title a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        
        .paper-title a:hover {{
            text-decoration: underline;
        }}
        
        .abstract-section {{
            grid-column: 1;
            grid-row: 2;
        }}
        
        .paper-authors {{
            color: var(--muted-text);
            font-style: italic;
            font-size: 0.9em;
            line-height: 1.4;
            padding-top: 4px;
            padding-bottom: 4px;
            grid-column: 2;
            grid-row: 2;
        }}
        
        .abstract-toggle {{
            background: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 4px;
            cursor: pointer;
            user-select: none;
            font-size: 0.8em;
            color: var(--button-text);
            transition: background-color 0.2s ease;
            display: flex;
            align-items: center;
            gap: 4px;
            flex-shrink: 0;
            font-style: normal;
            line-height: 1.4;
        }}
        
        .abstract-toggle:hover {{
            background: var(--highlight-background);
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
            margin: 10px 0 10px 0;
            line-height: 1.6;
            padding: 12px;
            background: var(--highlight-background);
            border-radius: 4px;
            border-left: 3px solid var(--primary-color);
            font-size: 0.9em;
            grid-column: 1 / -1;
            grid-row: 3;
        }}
        
        .paper-abstract.show {{
            display: block;
        }}
        
        .paper-abstract code {{
            background-color: var(--light-background);
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }}
        
        .paper-abstract a {{
            color: var(--primary-color);
            text-decoration: none;
            border-bottom: 1px dotted var(--primary-color);
        }}
        
        .paper-abstract a:hover {{
            text-decoration: underline;
            border-bottom: 1px solid var(--primary-color);
        }}
        
        .paper-abstract [style*="small-caps"], .paper-title [style*="small-caps"] {{
            font-variant: small-caps;
            letter-spacing: 0.05em;
        }}
        
        .no-papers {{
            text-align: center;
            color: var(--muted-text);
            font-style: italic;
            margin: 40px 0;
            font-size: 1.1em;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--footer-border);
            color: var(--muted-text);
            font-size: 0.9em;
        }}
        
        .github-link {{
            color: var(--primary-color);
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
                grid-template-columns: 1fr;
                gap: 5px;
            }}
            
            .paper-date {{
                grid-column: 1;
                grid-row: 1;
                font-size: 0.8em;
            }}
            
            .paper-title {{
                grid-column: 1;
                grid-row: 2;
            }}
            
            .abstract-section {{
                grid-column: 1;
                grid-row: 3;
            }}
            
            .paper-authors {{
                grid-column: 1;
                grid-row: 4;
            }}
            
            .paper-abstract {{
                grid-column: 1;
                grid-row: 5;
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
            pub_date = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
            formatted_date = pub_date.strftime("%d %B %Y")
            
            # Format authors (limit to first 5 for display)
            if len(paper['authors']) > 8:
                authors_display = (", ".join(
                    paper['authors'][:NBR_AUTHORS_TO_DISPLAY]) 
                + f" and {len(paper['authors']) - NBR_AUTHORS_TO_DISPLAY} others")
            else:
                authors_display = ", ".join(paper['authors'])
            
            # Use full abstract without truncation
            abstract = process_latex_text(paper['abstract'])
            title_processed = process_latex_text(paper['title'])
            
            html_content += f"""
            <article class="paper">
                <div class="paper-date">{formatted_date}</div>
                <div class="paper-title">
                    <a href="https://arxiv.org/abs/{paper['arxiv_id']}" target="_blank" rel="noopener">{title_processed}</a>
                </div>
                <div class="abstract-section">
                    <div class="abstract-toggle">
                        <span class="arrow">▶</span>
                        <span>Abstract</span>
                    </div>
                </div>
                <div class="paper-authors">{authors_display}</div>
                <div class="paper-abstract">{abstract}</div>
            </article>
"""

    html_content += f"""
        </main>
        
        <footer class="footer">
            <p>
                Generated automatically from arXiv.org • 
                <a href="https://github.com/UKNumericalRelativity/UKNR_papers" class="github-link" target="_blank" rel="noopener">
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
                    // Find the abstract element - it's in the same paper container
                    const paper = this.closest('.paper');
                    const abstract = paper.querySelector('.paper-abstract');
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
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file generated: {HTML_OUTPUT}")

def process_latex_text(text: str) -> str:
    """
    Convert LaTeX text commands to HTML.
    
    Args:
        text: Text possibly containing LaTeX commands
        
    Returns:
        Text with LaTeX commands converted to HTML
    """
    
    # Greek letters - handle these FIRST before accent commands that might interfere
    # Common ones in physics papers (single backslash in the input)
    greek_map = {
        r'\\alpha\b': 'α', r'\\beta\b': 'β', r'\\gamma\b': 'γ', r'\\delta\b': 'δ',
        r'\\epsilon\b': 'ε', r'\\zeta\b': 'ζ', r'\\eta\b': 'η', r'\\theta\b': 'θ',
        r'\\iota\b': 'ι', r'\\kappa\b': 'κ', r'\\lambda\b': 'λ', r'\\mu\b': 'μ',
        r'\\nu\b': 'ν', r'\\xi\b': 'ξ', r'\\omicron\b': 'ο', r'\\pi\b': 'π',
        r'\\rho\b': 'ρ', r'\\sigma\b': 'σ', r'\\tau\b': 'τ', r'\\upsilon\b': 'υ',
        r'\\phi\b': 'φ', r'\\chi\b': 'χ', r'\\psi\b': 'ψ', r'\\omega\b': 'ω',
        r'\\Gamma\b': 'Γ', r'\\Delta\b': 'Δ', r'\\Theta\b': 'Θ', r'\\Lambda\b': 'Λ',
        r'\\Xi\b': 'Ξ', r'\\Pi\b': 'Π', r'\\Sigma\b': 'Σ', r'\\Upsilon\b': 'Υ',
        r'\\Phi\b': 'Φ', r'\\Chi\b': 'Χ', r'\\Psi\b': 'Ψ', r'\\Omega\b': 'Ω'
    }
    
    # Apply Greek letter transformations FIRST
    for latex_cmd, unicode_char in greek_map.items():
        text = re.sub(latex_cmd, unicode_char, text)
    
    # LaTeX accent commands - handle these AFTER Greek letters
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
    
    # Handle \texttt{} inside math mode first (before general \texttt processing)
    # \texttt{} in math mode should become \text{} or \mathrm{} for MathJax
    def replace_texttt_in_math(match):
        full_math = match.group(0)
        # Replace \texttt{content} with \text{content} inside this math expression
        fixed_math = re.sub(r'\\texttt\{([^}]+)\}', r'\\text{\1}', full_math)
        return fixed_math
    
    # Find all math expressions and fix \texttt inside them
    text = re.sub(r'\$[^$]*\\texttt\{[^}]*\}[^$]*\$', replace_texttt_in_math, text)
    
    # Handle escaped underscore
    text = re.sub(r'\\_', '_', text)
    text = re.sub(r'\\%', '%', text)
    
    # Apply all LaTeX text formatting transformations
    # \emph{text} -> <em>text</em>
    text = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', text)
    
    # \textbf{text} -> <strong>text</strong>
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    
    # \textit{text} -> <em>text</em>
    text = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', text)
    
    # \textsc{text} -> <span style="font-variant: small-caps;">text</span>
    text = re.sub(r'\\textsc\{([^}]+)\}', r'<span style="font-variant: small-caps;">\1</span>', text)
    
    # \texttt{text} -> <code>text</code> (only for text outside math mode now)
    text = re.sub(r'\\texttt\{([^}]+)\}', r'<code>\1</code>', text)
    
    # \textrm{text} -> <span style="font-style: normal;">text</span>
    text = re.sub(r'\\textrm\{([^}]+)\}', r'<span style="font-style: normal;">\1</span>', text)
    
    # Fix corrupted characters that appear in arXiv data
    # Handle cases where character encoding went wrong
    text = re.sub(r'ḩi', 'χ', text)  # Corrupted chi character (U+1E29 + i -> χ)
    text = re.sub(r'ḩ', 'χ', text)   # General fix for this corruption (U+1E29 -> χ)
    
    # Make URLs clickable - detect http/https URLs and convert to links
    # This pattern matches URLs but avoids matching those already inside HTML tags
    url_pattern = r'(?<!href=")(?<!href=\')(?<!src=")(?<!src=\')(https?://[^\s<>"\'()]+)'
    text = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)
    
    # Fix math delimiters around HTML tags (this causes MathJax rendering issues)
    # Pattern: $<tag>content</tag>$ -> <tag>content</tag>
    text = re.sub(r'\$(<[^>]+>[^<]*</[^>]+>)\$', r'\1', text)
    
    # Also handle cases where \texttt{} was used inside math mode
    # This pattern catches $\texttt{text}$ which becomes $<code>text</code>$ after \texttt processing
    # We convert it to just <code>text</code> (remove the math delimiters)
    text = re.sub(r'\$<code>([^<]*)</code>\$', r'<code>\1</code>', text)
    
    return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scrape arXiv for papers with keywords and generate an HTML page')
    parser.add_argument('--query', default='numerical relativity', 
                       help='Search query (default: "numerical relativity")')
    parser.add_argument('--days-back', type=int, default=60,
                       help='How many days back to search (default: 60)')
    parser.add_argument('--target-authors', nargs='*', default=TARGET_AUTHORS,
        help='List of author names to always include (default: a couple UKNR authors)')
    args = parser.parse_args()

    # Search arXiv for new papers
    print("\n" + "=" * 60)
    print("Fetching new papers from arXiv...")
    new_papers = search_arxiv(args.query, args.days_back, args.target_authors)

    # Load existing papers from database
    print("=" * 60)
    print("Loading papers database...")
    existing_papers = load_papers_database()

    # Merge new papers with existing ones
    print("\n" + "=" * 60)
    print("Merging papers...")
    merged_papers = merge_papers(existing_papers, new_papers)

    # Prune old papers
    print("\n" + "=" * 60)
    print(f"Pruning papers older than {args.days_back} days...")
    final_papers = prune_old_papers(merged_papers, args.days_back)

    # Save updated database
    print("\n" + "=" * 60)
    print("Saving database...")
    save_papers_database(final_papers)

    # Generate HTML
    print("\n" + "=" * 60)
    print("Generating HTML...")
    generate_html(final_papers)

    print("\n" + "=" * 60)
    print(f"Done! Database contains {len(final_papers)} papers (generated {HTML_OUTPUT})")
    print("=" * 60)
