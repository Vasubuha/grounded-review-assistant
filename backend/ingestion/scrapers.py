import asyncio
import urllib.request
from bs4 import BeautifulSoup
import re
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_html_text(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size=500) -> list[str]:
    if not text:
        return []
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

async def scrape_amazon(url: str) -> list[str]:
    print(f"Scraping Amazon: {url}")
    await asyncio.sleep(1)
    text = await asyncio.to_thread(fetch_html_text, url)
    chunks = chunk_text(text)
    return chunks[:15] if chunks else []

async def scrape_flipkart(url: str) -> list[str]:
    print(f"Scraping Flipkart: {url}")
    await asyncio.sleep(1)
    text = await asyncio.to_thread(fetch_html_text, url)
    chunks = chunk_text(text)
    return chunks[:15] if chunks else []

# async def scrape_youtube(url: str) -> list[str]:
#     print(f"Scraping YouTube: {url}")

#     try:
#         video_id = ""

#         if "v=" in url:
#             video_id = url.split("v=")[1].split("&")[0]

#         elif "youtu.be/" in url:
#             video_id = url.split("youtu.be/")[1].split("?")[0]

#         if not video_id:
#             return []

#         try:
#             api = YouTubeTranscriptApi()
#             transcript = await asyncio.to_thread(
#                 api.fetch,
#                 video_id
#             )
#             full_text = " ".join([item.text for item in transcript])
#         except AttributeError:
#             transcript = await asyncio.to_thread(
#                 YouTubeTranscriptApi.get_transcript,
#                 video_id
#             )
#             full_text = " ".join([item["text"] for item in transcript])

#         full_text = re.sub(r"\s+", " ", full_text).strip()

#         chunks = chunk_text(full_text, 500)

#         return chunks[:10]

#     except Exception as e:
#         print(f"Error extracting YouTube transcript: {e}")
#         return []

async def scrape_youtube(url: str) -> list[str]:
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]

    if not video_id:
        return []

    # Try transcript with language fallbacks
    for lang in [["en"], ["en-US"], ["en-GB"], None]:
        try:
            kwargs = {"languages": lang} if lang else {}
            transcript = await asyncio.to_thread(
                YouTubeTranscriptApi.get_transcript, video_id, **kwargs
            )
            full_text = " ".join([item["text"] for item in transcript])
            full_text = re.sub(r"\s+", " ", full_text).strip()
            return chunk_text(full_text, 500)[:10]
        except Exception:
            continue

    print("All YouTube transcript attempts failed, skipping.")
    return []  # Never crash, just skip

async def scrape_spec(url: str) -> list[str]:
    print(f"Scraping Specs: {url}")
    await asyncio.sleep(1)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        html = await asyncio.to_thread(urllib.request.urlopen, req, timeout=10)
        html_content = html.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        elements = soup.find_all(['td', 'th', 'p', 'li'])
        texts = [el.text.strip() for el in elements if len(el.text.strip()) > 10]
        
        combined = " ".join(texts)
        combined = re.sub(r'\s+', ' ', combined).strip()
        chunks = chunk_text(combined, 500)
        return chunks[:15]
    except Exception as e:
        print(f"Spec Scrape Error: {e}")
        return []

async def scrape_url(url: str, source_type: str) -> list[str]:
    """Scrapes a URL with basic retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if source_type == "amazon":
                return await scrape_amazon(url)
            elif source_type == "flipkart":
                return await scrape_flipkart(url)
            elif source_type == "youtube":
                return await scrape_youtube(url)
            elif source_type == "spec":
                return await scrape_spec(url)
            else:
                return []
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {url}: {e}")
            if attempt == max_retries - 1:
                return []
            await asyncio.sleep(2)
