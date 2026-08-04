from apify_client import ApifyClient
import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# Initialize Apify client
apify_client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Maps the app's location dropdown to the ISO country codes the LinkedIn
# actor's "splitCountry" field accepts. Locations with no single matching
# country (e.g. "Remote", "Global") simply omit the field.
_LOCATION_TO_COUNTRY = {
    "India": "IN",
    "United States": "US",
    "United Kingdom": "GB",
}


def fetch_linkedin_jobs(search_query=None, location='India', rows=70):
    # Prepare the Actor input. Keywords/location must be URL-encoded, otherwise
    # spaces and commas break LinkedIn's search URL and the actor silently
    # returns zero results.
    run_input = {
        "urls": [
            f"https://www.linkedin.com/jobs/search/?keywords={quote(search_query or '')}"
            f"&location={quote(location)}&start=0"
        ],
        "scrapeCompany": True,
        "count": rows,
        "splitByLocation": False,
    }
    country_code = _LOCATION_TO_COUNTRY.get(location)
    if country_code:
        run_input["splitCountry"] = country_code

    # Run the Actor and wait for it to finish
    run = apify_client.actor("hKByXkMQaC5Qt9UMN").call(run_input=run_input)

    # Fetch Actor results from the run's dataset (if there are any)
    if isinstance(run, dict):
        dataset_id = run.get("default_dataset_id") or run.get("defaultDatasetId")
    else:
        dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    if dataset_id is None:
        return []

    return list(apify_client.dataset(dataset_id).iterate_items())

def fetch_naukri_jobs(search_query, location="India", rows=70):
    # Prepare the Actor input. Omit optional fields entirely rather than
    # sending None, since the actor's schema rejects null for string fields.
    run_input = {
        "keyword": search_query,
        "fetchDetails": False,
        # The actor rejects maxJobs < 50.
        "maxJobs": max(rows, 50),
        "freshness": "all",
        "sortBy": "relevance",
        "experience": "all",
    }

    # Run the Actor and wait for it to finish
    run = apify_client.actor("alpcnRV9YI9lYVPWk").call(run_input=run_input)

    # Fetch Actor results from the run's dataset (if there are any)
    # Support both dict-like and object-like run results returned by the Apify client
    if isinstance(run, dict):
        dataset_id = run.get("default_dataset_id") or run.get("defaultDatasetId")
    else:
        dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    if dataset_id is None:
        return []

    return list(apify_client.dataset(dataset_id).iterate_items())

def fetch_indeed_jobs(search_query=None, location='India', rows=70):
    # Prepare the Actor input. Use provided search_query/location when available.
    run_input = {
        "country": "us",
        "query": search_query or "",
        "location": location or "",
        "maxRows": max(rows, 50),
        "radius": "50",
        "sort": "relevance",
        "fromDays": "14",
        "urls": [],
        "maxRowsPerUrl": 100,
        "enableUniqueJobs": False,
        "includeSimilarJobs": True,
    }

    # Run the Actor and wait for it to finish
    run = apify_client.actor("MXLpngmVpE8WTESQr").call(run_input=run_input)

    # Fetch Actor results from the run's dataset (if there are any)
    if isinstance(run, dict):
        dataset_id = run.get("default_dataset_id") or run.get("defaultDatasetId")
    else:
        dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    if dataset_id is None:
        return []

    return list(apify_client.dataset(dataset_id).iterate_items())
