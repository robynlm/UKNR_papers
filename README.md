# Numerical Relativity Papers from arXiv

This repository automatically scrapes arXiv for recent papers containing "numerical relativity" keywords and generates a clean HTML page that can be embedded in websites.

## Features

- 🔄 **Automatic Updates**: Runs daily via GitHub Actions
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Clean Interface**: Modern, professional styling
- 🔗 **Direct Links**: Quick access to arXiv abstracts and PDFs
- 📊 **Paper Metadata**: Authors, categories, publication dates
- 🌐 **Embeddable**: Can be embedded in Google Sites or other platforms

## Live Demo

The generated page is automatically deployed to GitHub Pages: [https://robynlm.github.io/UKNR_papers/](https://robynlm.github.io/UKNR_papers/)

## Setup Instructions

### 1. Fork or Clone this Repository

```bash
git clone https://github.com/robynlm/UKNR_papers.git
cd UKNR_papers
```

### 2. Enable GitHub Pages

1. Go to your repository settings
2. Navigate to "Pages" in the left sidebar
3. Under "Source", select "GitHub Actions"
4. The workflow will automatically deploy your page

### 3. Enable GitHub Actions

1. Go to the "Actions" tab in your repository
2. If prompted, enable Actions for your repository
3. The workflow will run automatically daily at 6 AM UTC
4. You can also trigger it manually from the Actions tab

### 4. Customize (Optional)

You can modify the search parameters by editing the GitHub Actions workflow file (`.github/workflows/update-papers.yml`):

```yaml
- name: Run arXiv scraper
  run: |
    python arxiv_scraper.py --days-back 60 --max-results 100 --output index.html
```

Available parameters:
- `--query`: Search terms (default: "numerical relativity")
- `--days-back`: How many days back to search (default: 30)
- `--max-results`: Maximum papers to fetch (default: 50)
- `--authors`: List of author names to search for (optional)
- `--output`: Output HTML file name (default: index.html)

## Author-Based Search

You can include papers from specific authors even if they don't contain the main search keywords. This is useful for tracking papers from key researchers in the field.

### Method 1: Configuration File
Edit the `TARGET_AUTHORS` list in `arxiv_scraper.py`:

```python
TARGET_AUTHORS = [
    "Pretorius, Frans",
    "Campanelli, Manuela", 
    "Buonanno, Alessandra",
    # Add more authors as needed
]
```

### Method 2: Command Line
```bash
python arxiv_scraper.py --authors "Pretorius, Frans" "Campanelli, Manuela"
```

## Local Development

### Requirements

- Python 3.8+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
# Basic usage
python arxiv_scraper.py

# Custom search with keywords
python arxiv_scraper.py --query "gravitational waves" --days-back 14 --max-results 25

# Include specific authors
python arxiv_scraper.py --authors "Pretorius, Frans" "Campanelli, Manuela"

# Combine keyword and author search
python arxiv_scraper.py --query "black holes" --authors "Buonanno, Alessandra"

# View the generated HTML
open index.html
```

## Embedding in Google Sites

1. After your GitHub Pages site is live, copy the URL
2. In Google Sites, add an "Embed" element
3. Paste your GitHub Pages URL
4. Adjust the embed size as needed

The page is designed to be responsive and will adapt to the embed container size.

## File Structure

```
UKNR_papers/
├── arxiv_scraper.py          # Main Python scraper script
├── requirements.txt          # Python dependencies
├── index.html               # Generated HTML page (auto-created)
├── .github/
│   └── workflows/
│       └── update-papers.yml # GitHub Actions workflow
└── README.md               # This file
```

## Customization

### Styling

The HTML template in `arxiv_scraper.py` includes embedded CSS. You can modify the styles by editing the `<style>` section in the `generate_html()` function.

### Search Query

To search for different terms, modify the `--query` parameter in the GitHub Actions workflow or when running locally.

### Update Frequency

The default schedule runs daily at 6 AM UTC. To change this, modify the cron expression in `.github/workflows/update-papers.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
```

## API Rate Limits

The arXiv API has rate limits. The script includes:
- Reasonable delays between requests
- Error handling for network issues
- Timeout protection

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- Data provided by [arXiv.org](https://arxiv.org/)
- Built with GitHub Actions and GitHub Pages
- Inspired by the numerical relativity community's need for staying updated with recent research
- **Entirely written by Claude Sonnet 4 (Anthropic's AI assistant)**

## Troubleshooting

### Common Issues

1. **No papers showing**: Check if the search query is too restrictive or if arXiv is temporarily unavailable
2. **Styling issues**: Ensure the HTML is properly generated and CSS is not cached
3. **GitHub Actions failing**: Check the Actions tab for error logs and ensure all permissions are set correctly

### Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Try running the script locally
3. Open an issue in this repository
