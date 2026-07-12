import urllib.request
import urllib.error
from html.parser import HTMLParser
from core.ports.input_adapter import IInputAdapter, RawPayload
from typing import Any, Union, List

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._in_script_or_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'noscript'):
            self._in_script_or_style = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'header', 'footer', 'noscript'):
            self._in_script_or_style = False
        elif tag in ('p', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if not self._in_script_or_style:
            text = data.strip()
            if text:
                self.text_parts.append(text + ' ')

    def get_text(self):
        return "".join(self.text_parts).strip()


class UrlAdapter(IInputAdapter):
    """
    Ingests raw text from direct job posting URLs to feed the unified AI Extraction pipeline.
    """
    def collect(self, **kwargs) -> List[RawPayload]:
        raw_data = kwargs.get("url") or kwargs.get("raw_data")
        url = str(raw_data).strip()
        if not url.startswith("http"):
            url = "https://" + url
            
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            extractor = _TextExtractor()
            extractor.feed(html)
            text = extractor.get_text()
            
            # Simple cleanup of excessive newlines
            lines = [line.strip() for line in text.split('\n')]
            cleaned_text = '\n'.join([line for line in lines if line])
            return [{
                "source": "url",
                "metadata": {"url": url},
                "content": cleaned_text
            }]
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to fetch URL {url}: {e}")
