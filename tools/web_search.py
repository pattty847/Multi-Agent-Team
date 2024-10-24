# src/tools/web_search.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
from datetime import datetime
import time
import re

class WebSearchTool:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search arXiv for papers matching the query.
        """
        base_url = 'http://export.arxiv.org/api/query'
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            results = []
            for entry in entries:
                results.append({
                    'title': entry.title.text.strip(),
                    'authors': [author.text.strip() for author in entry.find_all('author')],
                    'summary': entry.summary.text.strip(),
                    'published': entry.published.text.strip(),
                    'link': entry.id.text.strip()
                })
            
            return results
        except Exception as e:
            return [{"error": f"Error searching arXiv: {str(e)}"}]

    def search_scholar(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Scrape Google Scholar for recent papers (basic implementation).
        """
        base_url = 'https://scholar.google.com/scholar'
        params = {
            'q': query,
            'hl': 'en',
            'as_sdt': '0,5',  # Recent papers
            'num': max_results
        }
        
        try:
            response = requests.get(base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('div', class_='gs_r gs_or gs_scl')
            
            results = []
            for article in articles[:max_results]:
                title_tag = article.find('h3', class_='gs_rt')
                if title_tag:
                    title = title_tag.text.strip()
                    link = title_tag.find('a')['href'] if title_tag.find('a') else None
                    
                    result = {
                        'title': title,
                        'link': link
                    }
                    
                    # Try to extract authors and publication info
                    pub_info = article.find('div', class_='gs_a')
                    if pub_info:
                        result['publication_info'] = pub_info.text.strip()
                    
                    results.append(result)
            
            return results
        except Exception as e:
            return [{"error": f"Error searching Google Scholar: {str(e)}"}]

    def summarize_research(self, query: str) -> str:
        """
        Perform a comprehensive research search and return a summarized result.
        """
        arxiv_results = self.search_arxiv(query)
        scholar_results = self.search_scholar(query)
        
        summary = [
            f"Research Summary for: {query}\n",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        ]
        
        if arxiv_results and not isinstance(arxiv_results[0].get('error'), str):
            summary.append("Recent arXiv Papers:")
            for i, paper in enumerate(arxiv_results, 1):
                summary.extend([
                    f"\n{i}. {paper['title']}",
                    f"   Authors: {', '.join(paper['authors'])}",
                    f"   Published: {paper['published']}",
                    f"   Link: {paper['link']}",
                    f"   Summary: {paper['summary'][:200]}...\n"
                ])
        
        if scholar_results and not isinstance(scholar_results[0].get('error'), str):
            summary.append("\nGoogle Scholar Results:")
            for i, paper in enumerate(scholar_results, 1):
                summary.extend([
                    f"\n{i}. {paper['title']}",
                    f"   Details: {paper.get('publication_info', 'No details available')}",
                    f"   Link: {paper.get('link', 'No link available')}\n"
                ])
        
        return "\n".join(summary)