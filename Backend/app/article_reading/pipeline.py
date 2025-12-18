import os
import re
from dotenv import load_dotenv
from newspaper import Article
import requests
import pyttsx3
from langchain_community.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import datetime
import json

# Download NLTK data on startup
from ..utils.nltk_init import download_nltk_data
download_nltk_data()

load_dotenv()


class ArticleExample:
    def __init__(self, title, text, summary, url):
        self.title = title
        self.text = text
        self.summary = summary
        self.url = url

# ---- LLM SWITCHER ----
def get_llm(provider: str):
    if provider == "openai":
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    elif provider == "groq":
        return ChatGroq(model="llama3-8b-8192", groq_api_key=os.getenv("GROQ_API_KEY"))
    else:
        raise ValueError("Unsupported provider")


def refine_query(llm, original_query: str):
    prompt = f"""You are an expert search query refiner. Your task is to take a user's initial search query related to recent updates in a field and rewrite it into one more specific query that is highly likely to return links to an individual, informative article from a reputable source, rather than just index pages or general overviews.

Your refined query should incorporate strategies such as:

- Specifying the content type (e.g., "article," "news report").
- Emphasizing recency (e.g., "since April 2024," "in early 2025").
- Including keywords that suggest specific information and depth (e.g., "developments," "breakthroughs," "analysis").

You will receive the user's initial query, and you will output one refined search query.

Example:
User Query: Recent updates about AI
Refined Query: Recent news report on significant AI developments in early 2025.

Original query: "{original_query}"
"""
    result = llm.invoke(prompt)
    return result.content.strip()


# ---- LLM-BASED SEARCH ----
from ddgs import DDGS

def llm_search(query: str, llm, num_results=3):
    """
    1. Dùng LLM để tối ưu hóa từ khóa tìm kiếm (tùy chọn).
    2. Dùng DuckDuckGo để tìm link THẬT.
    """
    print(f"\n🔍 Searching for: {query}")

    # Bước 1: (Tùy chọn) Dùng LLM để tạo từ khóa tìm kiếm tốt hơn
    # Ví dụ: User hỏi "AI mới nhất", LLM đổi thành "latest artificial intelligence news 2024"
    search_query = query 
    try:
        refine_prompt = f"Convert this user question into a generic search engine keyword (e.g. Google) to find news articles. Return ONLY the keyword.\nQuestion: {query}"
        response = llm.invoke(refine_prompt) # Bỏ comment nếu muốn dùng LLM
        search_query = response.content.strip()
    except:
        pass

    # Bước 2: Tìm kiếm thật bằng DuckDuckGo
    real_urls = []
    try:
        with DDGS() as ddgs:
            # Tìm kiếm tin tức (news) hoặc web thông thường
            results = ddgs.news(search_query, max_results=num_results + 2) # Lấy dư ra chút
            
            for r in results:
                # r là dict: {'title': ..., 'url': ..., 'body': ..., 'date': ...}
                link = r.get('url')
                if link:
                    real_urls.append(link)
                    print(f"✅ Found: {link}")
                
                if len(real_urls) >= num_results:
                    break
                    
    except Exception as e:
        print(f"❌ Search Error: {e}")
        # Fallback nếu lỗi mạng
        return [
            "https://www.bbc.com/news/technology",
            "https://techcrunch.com/",
            "https://www.theverge.com/"
        ][:num_results]

    if not real_urls:
         print("⚠️ No results found via search engine.")
         return []

    return real_urls


# ---- ARTICLE EXTRACTION ----
def extract_articles(urls):
    articles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    for url in urls:
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Try to use NLP, but if NLTK data is missing, skip it
            try:
                article.nlp()
            except LookupError as nltk_error:
                print(f"⚠️ NLTK data missing, skipping NLP: {nltk_error}")
                # Continue without NLP - we still have the parsed article
            except Exception as nlp_error:
                print(f"⚠️ NLP processing failed: {nlp_error}")
                # Continue without NLP

            if article.text.strip():
                articles.append(ArticleExample(article.title, article.text[:2000], article.summary, url))
        except Exception as e:
            print(f"❌ Error extracting from {url}: {e}")
    return articles


# ---- SUMMARIZATION ----
def summarize_articles(llm, articles):
    if not articles:
        return "No valid articles to summarize."

    summaries = []
    for title, content, _ in articles:
        summary_prompt = f"📰 Title: {title}\n\n📖 Article:\n{content}\n\n✏️ Please provide a short summary."
        response = llm.invoke(summary_prompt)
        summaries.append(response.content.strip())

    return "\n\n".join(summaries)


# ---- TEXT TO SPEECH (optional) ----
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# ---- PIPELINE ----
def execute_pipeline(user_query: str, provider="openai"):  # Changed default from "gemini" to "openai"
    # 1. Get LLM
    llm = get_llm(provider)

    print(f"🔍 Original Query:\n{user_query}\n")

    # Step 1: Refine Query
    #refined_query = refine_query(llm, user_query)
    #print(f"🎯 Refined Query:\n{refined_query}\n")

    refined_query = user_query

    # Step 2: Search with LLM
    urls = llm_search(refined_query, llm)
    print(f"🔗 Extracted URLs:\n{urls}\n")


    # Step 3: Article Extraction
    articles = extract_articles(urls)
    print(f"📚 Retrieved {len(articles)} articles for summarization...\n")


    # # Step 5: TTS (optional)
    # # speak_text(summary)

    max_articles = 3

    return articles[:max_articles]


# ---- MAIN ----
if __name__ == "__main__":
    query = input("Enter your query: ")
    execute_pipeline(query, provider="openai")  # Options: "openai", "gemini", "groq"
