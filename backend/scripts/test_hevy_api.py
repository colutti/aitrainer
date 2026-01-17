import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv(".env.prod")

# PROVIDED KEY
API_KEY = "39ba5086-3224-49ac-a6ab-6e561c642c3c"

async def test_hevy_api():
    async with httpx.AsyncClient() as http_client:
        print("\n🔍 Fetching Exercise Templates...")
        page = 1
        all_templates = []
        while True:
            response = await http_client.get(
                "https://api.hevyapp.com/v1/exercise_templates",
                headers={"api-key": API_KEY},
                params={"page": page, "pageSize": 100}
            )
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                break
            
            data = response.json()
            templates = data.get("exercise_templates", [])
            all_templates.extend(templates)
            
            print(f"   Page {page}: Got {len(templates)} templates (Total: {len(all_templates)})")
            
            if page >= data.get("page_count", 0):
                break
            page += 1

        print("\n🧪 Testing Search Logic:")
        # Common terms user mentioned as failing
        search_terms = ["leg press", "hip thrust", "iso-lateral row", "shoulder press", "chest press", "row", "squat", "bench"]
        for term in search_terms:
            matches = [t for t in all_templates if term.lower() in t["title"].lower()]
            if matches:
                print(f"✅ '{term}': Found {len(matches)} matches. Top: '{matches[0]['title']}' - ID: {matches[0]['id']}")
            else:
                # Try a broader search (AND logic for each word)
                parts = term.split()
                if len(parts) > 1:
                    matches = [t for t in all_templates if all(p.lower() in t["title"].lower() for p in parts)]
                    if matches:
                        print(f"⚠️ '{term}': Multi-word match: '{matches[0]['title']}' - ID: {matches[0]['id']}")
                        continue
                print(f"❌ '{term}': NO MATCH FOUND")

        print("\n🤔 Analyzing why 'leg press' or others might fail...")
        # Search for anything containing 'leg'
        print("Searching for 'leg':", [t["title"] for t in all_templates if "leg" in t["title"].lower()][:5])
        # Search for anything containing 'press'
        print("Searching for 'press':", [t["title"] for t in all_templates if "press" in t["title"].lower()][:5])

if __name__ == "__main__":
    asyncio.run(test_hevy_api())
