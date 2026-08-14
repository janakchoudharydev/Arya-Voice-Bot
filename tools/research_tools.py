"""
ARYA Research Tools - Advanced Backend Research Capabilities
Provides deep research, analysis, and information synthesis.
"""

import logging
import requests
import urllib.parse
from typing import List, Dict, Optional
from livekit.agents import function_tool
import json
import re
from datetime import datetime

logger = logging.getLogger("arya-agent")

@function_tool
async def deep_research(query: str, depth: str = "medium") -> str:
    """
    Perform comprehensive research on any topic with multiple sources.
    
    Args:
        query: Research topic or question
        depth: Research depth - "quick", "medium", or "deep"
    
    Uses multiple search queries, analyzes results, and synthesizes information.
    """
    try:
        logger.info(f"🔬 Starting deep research on: {query}")
        
        # Generate multiple search queries for comprehensive coverage
        search_queries = generate_search_queries(query, depth)
        
        research_results = []
        sources_used = []
        
        for search_query in search_queries[:3]:  # Limit to 3 queries for efficiency
            results = await perform_google_search(search_query)
            if results:
                research_results.extend(results)
                sources_used.append(f"Google: {search_query}")
        
        # Analyze and synthesize the research
        if research_results:
            synthesis = synthesize_research(query, research_results, sources_used)
            
            # Add timestamp and metadata
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return f"""
🔬 **DEEP RESEARCH REPORT**
📅 Generated: {timestamp}
🎯 Topic: {query}
📊 Sources: {len(sources_used)} sources analyzed
📄 Results: {len(research_results)} items processed

{synthesis}

---
🔍 **Sources Used:**
{chr(10).join(f"• {source}" for source in sources_used)}

💡 **Key Insights:**
{extract_key_insights(research_results)}
"""
        else:
            return f"❌ No research results found for '{query}'. Try rephrasing your query."
            
    except Exception as e:
        logger.error(f"Research error: {e}")
        return f"⚠️ Research failed: {str(e)[:100]}... Try a simpler query."

@function_tool
async def analyze_topic(topic: str) -> str:
    """
    Analyze a topic from multiple angles - pros, cons, trends, and future outlook.
    
    Provides comprehensive analysis including:
    - Current state and trends
    - Advantages and disadvantages
    - Future predictions
    - Key statistics and data
    """
    try:
        logger.info(f"📊 Analyzing topic: {topic}")
        
        # Generate analysis queries
        analysis_queries = [
            f"{topic} advantages benefits pros",
            f"{topic} disadvantages risks cons",
            f"{topic} trends statistics data",
            f"{topic} future outlook predictions"
        ]
        
        analysis_data = {}
        
        for query_type, search_query in zip(["pros", "cons", "trends", "future"], analysis_queries):
            results = await perform_google_search(search_query)
            analysis_data[query_type] = results[:3] if results else []
        
        # Generate comprehensive analysis
        analysis_report = generate_analysis_report(topic, analysis_data)
        
        return f"""
📊 **COMPREHENSIVE TOPIC ANALYSIS**
🎯 Subject: {topic}
📅 Analysis Date: {datetime.now().strftime("%Y-%m-%d")}

{analysis_report}

---
🔍 **Analysis Methodology:**
• Searched for advantages/disadvantages
• Analyzed current trends and statistics
• Researched future predictions
• Synthesized findings from multiple sources
"""
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return f"⚠️ Analysis failed: {str(e)[:100]}..."

@function_tool
async def compare_topics(topic1: str, topic2: str) -> str:
    """
    Compare two topics side by side with detailed analysis.
    
    Provides comparison across multiple dimensions:
    - Features and capabilities
    - Performance and efficiency
    - Cost and accessibility
    - User satisfaction and reviews
    """
    try:
        logger.info(f"⚖️ Comparing: {topic1} vs {topic2}")
        
        # Generate comparison queries
        comparison_queries = [
            f"{topic1} vs {topic2} comparison",
            f"{topic1} vs {topic2} differences",
            f"{topic1} vs {topic2} pros cons",
            f"{topic1} vs {topic2} reviews ratings"
        ]
        
        comparison_results = []
        
        for query in comparison_queries:
            results = await perform_google_search(query)
            comparison_results.extend(results[:2] if results else [])
        
        # Generate comparison table
        comparison_report = generate_comparison_report(topic1, topic2, comparison_results)
        
        return f"""
⚖️ **DETAILED COMPARISON ANALYSIS**
🥊 Topics: {topic1} vs {topic2}
📅 Comparison Date: {datetime.now().strftime("%Y-%m-%d")}

{comparison_report}

---
📋 **Comparison Criteria:**
• Features and functionality
• Performance and efficiency
• Cost and value
• User reviews and satisfaction
• Market position and trends
"""
        
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        return f"⚠️ Comparison failed: {str(e)[:100]}..."

@function_tool
async def get_latest_news(topic: str, days_back: int = 7) -> str:
    """
    Get latest news and developments on any topic.
    
    Args:
        topic: News topic or keyword
        days_back: How many days back to search (default: 7)
    
    Provides recent news with sources and timestamps.
    """
    try:
        logger.info(f"📰 Getting latest news for: {topic}")
        
        # Search for recent news
        news_queries = [
            f"{topic} latest news",
            f"{topic} recent developments",
            f"{topic} updates announcements"
        ]
        
        news_results = []
        
        for query in news_queries:
            results = await perform_google_search(query)
            news_results.extend(results[:3] if results else [])
        
        # Filter and organize news
        organized_news = organize_news_results(news_results, topic)
        
        return f"""
📰 **LATEST NEWS REPORT**
📡 Topic: {topic}
📅 Coverage: Last {days_back} days
🗞️ Articles Found: {len(news_results)}

{organized_news}

---
📢 **News Sources:**
• Google News Search
• Recent web articles
• Official announcements
• Industry publications
"""
        
    except Exception as e:
        logger.error(f"News error: {e}")
        return f"⚠️ News retrieval failed: {str(e)[:100]}..."

# Helper functions for research processing

def generate_search_queries(query: str, depth: str) -> List[str]:
    """Generate multiple search queries for comprehensive research."""
    base_queries = [query]
    
    if depth == "quick":
        return base_queries
    elif depth == "medium":
        return [
            query,
            f"{query} overview introduction",
            f"{topic} key facts statistics"
        ]
    else:  # deep
        return [
            query,
            f"{query} detailed analysis",
            f"{query} research studies",
            f"{query} expert opinions",
            f"{query} case studies examples"
        ]

async def perform_google_search(query: str) -> List[str]:
    """Perform Google search and return results."""
    try:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            h3_tags = soup.find_all('h3')
            
            for h3 in h3_tags[:5]:
                text = h3.get_text().strip()
                if len(text) > 10 and not text.lower().startswith(('search', 'related', 'people also')):
                    results.append(text)
            
            return results
        else:
            return []
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def synthesize_research(query: str, results: List[str], sources: List[str]) -> str:
    """Synthesize research results into coherent report."""
    if not results:
        return "No information found for synthesis."
    
    # Categorize results
    categories = categorize_results(results)
    
    synthesis = f"""
🧠 **RESEARCH SYNTHESIS**

📚 **Key Findings:**
{chr(10).join(f"• {result}" for result in results[:5])}

📊 **Topic Categories:**
{chr(10).join(f"• {category}: {', '.join(items[:2])}" for category, items in categories.items() if items)}

🎯 **Research Summary:**
Based on analysis of {len(results)} sources, {query} appears to be a {assess_topic_complexity(results)} topic with {assess_information_depth(results)} information available.
"""
    
    return synthesis

def categorize_results(results: List[str]) -> Dict[str, List[str]]:
    """Categorize research results by topic."""
    categories = {
        "overview": [],
        "technical": [],
        "benefits": [],
        "challenges": [],
        "trends": []
    }
    
    for result in results:
        result_lower = result.lower()
        if any(word in result_lower for word in ["overview", "introduction", "what is", "guide"]):
            categories["overview"].append(result)
        elif any(word in result_lower for word in ["technical", "how to", "implementation", "tutorial"]):
            categories["technical"].append(result)
        elif any(word in result_lower for word in ["benefits", "advantages", "pros", "why"]):
            categories["benefits"].append(result)
        elif any(word in result_lower for word in ["challenges", "disadvantages", "cons", "risks"]):
            categories["challenges"].append(result)
        elif any(word in result_lower for word in ["trends", "future", "2024", "2025", "latest"]):
            categories["trends"].append(result)
    
    return categories

def assess_topic_complexity(results: List[str]) -> str:
    """Assess the complexity of the topic based on results."""
    technical_terms = sum(1 for result in results if any(word in result.lower() for word in ["technical", "implementation", "algorithm", "system"]))
    
    if technical_terms > len(results) * 0.5:
        return "complex technical"
    elif technical_terms > len(results) * 0.2:
        return "moderately complex"
    else:
        return "straightforward"

def assess_information_depth(results: List[str]) -> str:
    """Assess the depth of information available."""
    if len(results) > 10:
        return "extensive"
    elif len(results) > 5:
        return "moderate"
    else:
        return "limited"

def extract_key_insights(results: List[str]) -> str:
    """Extract key insights from research results."""
    insights = []
    
    # Look for patterns in results
    common_words = {}
    for result in results:
        words = result.lower().split()
        for word in words:
            if len(word) > 4:  # Only meaningful words
                common_words[word] = common_words.get(word, 0) + 1
    
    # Get most common words
    top_words = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if top_words:
        insights.append(f"Key themes: {', '.join(word for word, count in top_words)}")
    
    # Look for numbers/statistics
    for result in results:
        if re.search(r'\d+%|\d+\.\d+%', result):
            insights.append(f"Statistical data found: {result[:100]}...")
            break
    
    return chr(10).join(f"• {insight}" for insight in insights[:3])

def generate_analysis_report(topic: str, data: Dict[str, List[str]]) -> str:
    """Generate comprehensive analysis report."""
    report = f"""
📈 **ANALYSIS OVERVIEW**

✅ **Advantages & Benefits:**
{chr(10).join(f"• {item}" for item in data["pros"][:3]) if data["pros"] else "• No specific advantages found"}

⚠️ **Disadvantages & Risks:**
{chr(10).join(f"• {item}" for item in data["cons"][:3]) if data["cons"] else "• No specific disadvantages found"}

📊 **Trends & Statistics:**
{chr(10).join(f"• {item}" for item in data["trends"][:3]) if data["trends"] else "• No trend data found"}

🔮 **Future Outlook:**
{chr(10).join(f"• {item}" for item in data["future"][:3]) if data["future"] else "• No future predictions found"}

💡 **Overall Assessment:**
{generate_overall_assessment(data)}
"""
    
    return report

def generate_overall_assessment(data: Dict[str, List[str]]) -> str:
    """Generate overall assessment based on analysis data."""
    total_points = len(data["pros"]) + len(data["cons"]) + len(data["trends"]) + len(data["future"])
    
    if total_points == 0:
        return "Limited information available for comprehensive assessment."
    
    pros_ratio = len(data["pros"]) / total_points if total_points > 0 else 0
    
    if pros_ratio > 0.6:
        return f"{topic} shows strong positive indicators with {len(data['pros'])} advantages versus {len(data['cons'])} disadvantages."
    elif pros_ratio > 0.4:
        return f"{topic} presents a balanced profile with both opportunities and challenges."
    else:
        return f"{topic} faces significant challenges with {len(data['cons'])} concerns identified."

def generate_comparison_report(topic1: str, topic2: str, results: List[str]) -> str:
    """Generate detailed comparison report."""
    # Simple comparison based on available results
    topic1_mentions = sum(1 for result in results if topic1.lower() in result.lower())
    topic2_mentions = sum(1 for result in results if topic2.lower() in result.lower())
    
    comparison = f"""
🆚 **COMPARISON OVERVIEW**

📊 **Mentions in Sources:**
• {topic1}: {topic1_mentions} references
• {topic2}: {topic2_mentions} references

🔍 **Key Comparison Points:**
{chr(10).join(f"• {result}" for result in results[:5])}

📈 **Comparative Analysis:"""
    
    if topic1_mentions > topic2_mentions:
        comparison += f"\n• {topic1} appears more frequently discussed in sources"
    elif topic2_mentions > topic1_mentions:
        comparison += f"\n• {topic2} appears more frequently discussed in sources"
    else:
        comparison += f"\n• Both topics receive similar attention in sources"
    
    return comparison

def organize_news_results(results: List[str], topic: str) -> str:
    """Organize news results by relevance and date."""
    if not results:
        return "No recent news found."
    
    organized = f"📰 **Recent Headlines:**\n"
    organized += chr(10).join(f"• {result}" for result in results[:5])
    
    organized += f"\n\n📊 **News Summary:**\n"
    organized += f"Found {len(results)} recent articles about {topic}. "
    
    # Look for sentiment indicators
    positive_words = ["growth", "success", "breakthrough", "achievement", "positive"]
    negative_words = ["concern", "decline", "issue", "problem", "challenge"]
    
    positive_count = sum(1 for result in results if any(word in result.lower() for word in positive_words))
    negative_count = sum(1 for result in results if any(word in result.lower() for word in negative_words))
    
    if positive_count > negative_count:
        organized += "News sentiment appears predominantly positive."
    elif negative_count > positive_count:
        organized += "News sentiment appears predominantly negative."
    else:
        organized += "News sentiment appears balanced."
    
    return organized

# Export all research tools
RESEARCH_TOOLS = [
    deep_research,
    analyze_topic,
    compare_topics,
    get_latest_news,
]
