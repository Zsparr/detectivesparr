import aiohttp
import asyncio

async def fetch(url):
    print(f"Fetching {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=False) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Title check: {'<title>' in text}")
            if '<title>' in text:
                start = text.find('<title>')
                end = text.find('</title>')
                print(f"Title: {text[start:end+8]}")
            
            print(f"Body snippet: {text[:500]}")
            print("-" * 20)

async def main():
    await fetch("https://www.pinterest.com/thisuserdefinitelydoesnotexist12345/")
    await fetch("https://www.twitch.tv/thisuserdefinitelydoesnotexist12345")
    await fetch("https://www.instagram.com/thisuserdefinitelydoesnotexist12345/")

asyncio.run(main())
