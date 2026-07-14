import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GRID_API_KEY")
series_id = 2589176

if not api_key:
    raise RuntimeError("GRID_API_KEY was not loaded from .env")

base_url = (
    f"https://api.grid.gg/"
    f"file-download/end-state/grid/series/{series_id}"
)

print("Testing x-api-key header...")

header_response = requests.get(
    base_url,
    headers={"x-api-key": api_key},
    timeout=30,
)

print("Header status:", header_response.status_code)
print("Header response:", header_response.text[:500])

print("\nTesting URL key parameter...")

parameter_response = requests.get(
    base_url,
    params={"key": api_key},
    timeout=30,
)

print("Parameter status:", parameter_response.status_code)
print("Parameter response:", parameter_response.text[:500])