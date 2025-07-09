import asyncio
import aiohttp
import os
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote

MONGO_DETAILS = "mongodb+srv://Mamidipaka_Bhagavan_Vara_Prasad:bharath%400712@cluster0.v3qjbj6.mongodb.net/student_collab_hub?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["student_collab_hub"]
resources_collection = database.get_collection("resources")

resources_dir = os.path.join(os.path.dirname(__file__), "resources-files")
os.makedirs(resources_dir, exist_ok=True)

SEARCH_URL = "https://duckduckgo.com/html/?q={query}+filetype:pdf"

async def fetch_pdf_url(session, query):
    # Use DuckDuckGo HTML results to find a PDF link
    search_url = SEARCH_URL.format(query=quote(query))
    async with session.get(search_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
        text = await resp.text()
        # Find first .pdf link in results
        import re
        matches = re.findall(r'href="(https?://[^"]+\.pdf)"', text)
        for url in matches:
            if url.lower().endswith('.pdf'):
                return url
    return None

async def download_pdf(session, url, filename):
    try:
        async with session.get(url, timeout=30) as resp:
            if resp.status == 200 and resp.headers.get('content-type', '').startswith('application/pdf'):
                with open(filename, 'wb') as f:
                    f.write(await resp.read())
                return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
    return False

async def main():
    async with aiohttp.ClientSession() as session:
        async for resource in resources_collection.find({}):
            title = resource.get('name') or resource.get('title')
            if not title:
                continue
            print(f"Searching PDF for: {title}")
            pdf_url = await fetch_pdf_url(session, title)
            if not pdf_url:
                print(f"No PDF found for {title}")
                continue
            print(f"Found PDF: {pdf_url}")
            safe_name = title.replace(' ', '_').replace('/', '_') + '.pdf'
            file_path = os.path.join(resources_dir, safe_name)
            if await download_pdf(session, pdf_url, file_path):
                print(f"Downloaded {safe_name}")
                await resources_collection.update_one(
                    {"_id": resource["_id"]},
                    {"$set": {"url": f"/api/files/{safe_name}", "filename": safe_name}}
                )
            else:
                print(f"Failed to download PDF for {title}")

if __name__ == "__main__":
    asyncio.run(main()) 