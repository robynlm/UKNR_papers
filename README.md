# Numerical Relativity Papers from arXiv

This project creates a webpage containing recent numerical relativity papers from arXiv, to be displayed on the [UKNR website papers page](https://www.uknumericalrelativity.org/papers).


GitHub Actions activates the arxiv_scraper.py script Monday through Friday to:
- collect recent arXiv papers matching the query `numerical relativity` and a configurable list of target authors,
- update collected results in `papers.json` database (robust under arXiv downtime),
- generate the [HTML](https://robynlm.github.io/UKNR_papers) which is embedded in the UKNR website.

## Usage

```bash
python3 arxiv_scraper.py

options
  --query            String of search query (default: "numerical relativity")
  --days-back        How many days back to search (default: 60)
  --target-authors   List of author names to include
```