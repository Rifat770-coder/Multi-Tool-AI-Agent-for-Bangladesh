"""One search provider: Tavily."""
import json
import urllib.request
from langchain_core.tools import StructuredTool


def create_web_tool(api_key):
    def search(question: str) -> str:
        try:
            request = urllib.request.Request(
                'https://api.tavily.com/search',
                data=json.dumps({'query': question, 'max_results': 5, 'search_depth': 'basic'}).encode(),
                headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {api_key}'},
            )
            with urllib.request.urlopen(request, timeout=30) as handle:
                response = json.load(handle)
            results = [{'title': r['title'], 'url': r['url'], 'content': r['content']} for r in response['results']]
            return json.dumps(results, ensure_ascii=False) if results else 'No web search results found.'
        except Exception as error:
            return f'Web search failed ({type(error).__name__}). Check Tavily credentials and connectivity.'
    return StructuredTool.from_function(search, name='WebSearchTool', description='Search general knowledge, definitions, Bangladesh policies and cultural context. Never substitute for dataset statistics.')
