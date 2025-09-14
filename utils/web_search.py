from duckduckgo_search import DDGS
from typing import List, Dict, Optional
import time


def get_fallback_resources(topic: str) -> Dict[str, List[Dict[str, str]]]:
    """Provide fallback resources when web search fails"""
    topic_lower = topic.lower()
    
    # Fallback YouTube videos for common topics
    fallback_videos = {
        'machine learning': [
            {"title": "Machine Learning Course - 3Blue1Brown", "url": "https://www.youtube.com/watch?v=aircAruvnKk"},
            {"title": "Machine Learning Tutorial - freeCodeCamp", "url": "https://www.youtube.com/watch?v=KNAWp2s3c94"},
            {"title": "Machine Learning Explained - Simplilearn", "url": "https://www.youtube.com/watch?v=ukzFI9rgwfU"}
        ],
        'python': [
            {"title": "Python Tutorial for Beginners - freeCodeCamp", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw"},
            {"title": "Learn Python - Full Course - Programming with Mosh", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc"},
            {"title": "Python Crash Course - Traversy Media", "url": "https://www.youtube.com/watch?v=JJmcL1N2KQs"}
        ],
        'data structure': [
            {"title": "Data Structures and Algorithms - freeCodeCamp", "url": "https://www.youtube.com/watch?v=8hly31xKli0"},
            {"title": "Data Structures - CS50", "url": "https://www.youtube.com/watch?v=3uGchQbk7g8"},
            {"title": "Algorithms and Data Structures - MIT", "url": "https://www.youtube.com/watch?v=HtSuA80QTyo"}
        ]
    }
    
    # Fallback articles for common topics
    fallback_articles = {
        'machine learning': [
            {"title": "Machine Learning Tutorial - W3Schools", "url": "https://www.w3schools.com/python/python_ml_getting_started.asp"},
            {"title": "Introduction to Machine Learning - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/introduction-to-machine-learning/"},
            {"title": "Machine Learning Guide - Towards Data Science", "url": "https://towardsdatascience.com/machine-learning-basics-part-1-a36d38c8216c"}
        ],
        'python': [
            {"title": "Python Tutorial - W3Schools", "url": "https://www.w3schools.com/python/"},
            {"title": "Python Documentation - Official", "url": "https://docs.python.org/3/tutorial/"},
            {"title": "Learn Python - Real Python", "url": "https://realpython.com/start-here/"}
        ],
        'data structure': [
            {"title": "Data Structures - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/data-structures/"},
            {"title": "Data Structures and Algorithms - Tutorialspoint", "url": "https://www.tutorialspoint.com/data_structures_algorithms/index.htm"},
            {"title": "Introduction to Data Structures - Programiz", "url": "https://www.programiz.com/dsa"}
        ]
    }
    
    # Find matching topic
    videos = []
    articles = []
    
    for key, video_list in fallback_videos.items():
        if key in topic_lower:
            videos = video_list
            break
    
    for key, article_list in fallback_articles.items():
        if key in topic_lower:
            articles = article_list
            break
    
    # If no specific match, provide general resources
    if not videos:
        videos = [
            {"title": "Learn Programming - freeCodeCamp", "url": "https://www.youtube.com/c/Freecodecamp"},
            {"title": "Programming Tutorials - Programming with Mosh", "url": "https://www.youtube.com/c/programmingwithmosh"},
            {"title": "Tech Tutorials - Traversy Media", "url": "https://www.youtube.com/c/TraversyMedia"}
        ]
    
    if not articles:
        articles = [
            {"title": "Programming Tutorials - W3Schools", "url": "https://www.w3schools.com/"},
            {"title": "Learn Programming - GeeksforGeeks", "url": "https://www.geeksforgeeks.org/"},
            {"title": "Programming Resources - Tutorialspoint", "url": "https://www.tutorialspoint.com/"}
        ]
    
    return {"videos": videos, "articles": articles}


def recommend_articles_ddg(topic: str, limit: int = 3) -> List[Dict[str, str]]:
    """Fetch article links using DuckDuckGo search API.
    Returns a list of {title, url, body}.
    """
    try:
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        with DDGS(timeout=15) as ddgs:
            # Search for tutorial articles with better query
            query = f"{topic} tutorial guide documentation"
            results = [r for r in ddgs.text(query, max_results=limit*3, region='wt-wt', safesearch='off')]
            
            items = []
            for result in results:
                if result.get('title') and result.get('href'):
                    # Filter out unwanted domains
                    url = result['href']
                    if not any(skip in url.lower() for skip in ['duckduckgo.com', 'google.com', 'bing.com', 'youtube.com', 'facebook.com', 'twitter.com']):
                        items.append({
                            "title": result['title'],
                            "url": url,
                            "body": result.get('body', '')
                        })
                        if len(items) >= limit:
                            break
            
            # If no items found, use fallback
            if not items:
                print(f"No articles found for '{topic}', using fallback resources")
                fallback = get_fallback_resources(topic)
                return fallback["articles"][:limit]
            
            return items
            
    except Exception as e:
        print(f"Error in recommend_articles_ddg: {e}")
        # Return fallback resources
        fallback = get_fallback_resources(topic)
        return fallback["articles"][:limit]


def recommend_youtube_ddg(topic: str, limit: int = 3) -> List[Dict[str, str]]:
    """Fetch YouTube video links using DuckDuckGo search API.
    Returns a list of {title, url, thumbnail}.
    """
    try:
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        with DDGS(timeout=15) as ddgs:
            # Search for YouTube videos with better query
            query = f"{topic} tutorial course"
            results = [r for r in ddgs.videos(query, max_results=limit*2, region='wt-wt', safesearch='off', timelimit='y')]
            
            items = []
            for result in results:
                if result.get('title') and result.get('content'):
                    items.append({
                        "title": result['title'],
                        "url": result['content'],
                        "thumbnail": result.get('thumbnail', '')
                    })
                    if len(items) >= limit:
                        break
            
            # If no items found, use fallback
            if not items:
                print(f"No videos found for '{topic}', using fallback resources")
                fallback = get_fallback_resources(topic)
                return fallback["videos"][:limit]
            
            return items
            
    except Exception as e:
        print(f"Error in recommend_youtube_ddg: {e}")
        # Return fallback resources
        fallback = get_fallback_resources(topic)
        return fallback["videos"][:limit]
