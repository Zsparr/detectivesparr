import asyncio
import argparse
import sys
from colorama import init, Fore, Style
from searcher import SiteChecker

# Initialize colorama
init()

async def main():
    parser = argparse.ArgumentParser(description="Search for a username across multiple social media sites.")
    parser.add_argument("username", help="The username to search for")
    args = parser.parse_args()

    username = args.username
    print(f"{Fore.CYAN}Searching for username: {Style.BRIGHT}{username}{Style.RESET_ALL}\n")

    checker = SiteChecker()
    if not checker.sites:
        print(f"{Fore.RED}No sites loaded. Check sites.json.{Style.RESET_ALL}")
        return

    results = await checker.search_all(username)

    found_count = 0
    for res in results:
        if res["found"]:
            print(f"{Fore.GREEN}[+] Found {res['name']}: {res['url']}{Style.RESET_ALL}")
            found_count += 1
        elif res["error"]:
             print(f"{Fore.YELLOW}[!] Error accessing {res['name']}: {res['error']}{Style.RESET_ALL}")
        else:
            # Optional: Print not found sites? Usually too noisy.
            # print(f"{Fore.RED}[-] Not Found {res['name']}{Style.RESET_ALL}")
            pass

    print(f"\n{Fore.CYAN}Search complete. Found {found_count} profiles.{Style.RESET_ALL}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
