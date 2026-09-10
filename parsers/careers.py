from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json
import os
from urllib.parse import urljoin


DATA_FILE = "parsers/data.json"
OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "career_jobs.jsonl")

MAX_PAGES = 3
MAX_JOBS_PER_PAGE = 60
PAGE_TIMEOUT = 30000


# ---------------------------------------------------------
# Load portal configuration
# ---------------------------------------------------------
with open(DATA_FILE, "r", encoding="utf-8") as file:
    all_portals = json.load(file)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_text(locator):
    """Safely get inner text."""
    try:
        if locator.count() > 0:
            return locator.inner_text().strip()
    except Exception:
        pass

    return ""


def get_job_description(page, selector):
    try:
        return page.locator(selector).first.inner_text().strip()
    except Exception:
        return ""


def get_location(page, selector):
    """Extract all matching location elements."""
    try:
        elements = page.locator(selector).all_inner_texts()

        locations = [
            value.strip()
            for value in elements
            if value.strip()
        ]

        return ", ".join(locations)

    except Exception:
        return ""


def get_job_link(job, config):
    """Extract and normalize job URL."""

    try:
        if config["job_link"]:
            href = job.locator(config["job_link"]).get_attribute("href")
        else:
            href = job.get_attribute("href")

        if not href:
            return None

        base_url = config.get("job_base_url")

        if base_url:
            href = urljoin(base_url, href)

        return href

    except Exception:
        return None


def scrape_job(browser_context, config, job_link):
    """Open and scrape an individual job."""

    page = browser_context.new_page()

    try:
        page.goto(
            job_link,
            wait_until="domcontentloaded",
            timeout=PAGE_TIMEOUT
        )

        # Wait for job page
        if config.get("child_page"):
            page.wait_for_selector(
                config["child_page"],
                timeout=PAGE_TIMEOUT
            )

        title = get_text(
            page.locator(config["title"])
        )

        location = get_location(
            page,
            config["location"]
        )

        description = get_job_description(
            page,
            config["description"]
        )

        return {
            "title": title,
            "location": location,
            "description": description
        }

    except PlaywrightTimeoutError:
        print(f"Timeout: {job_link}")

    except Exception as e:
        print(f"Error scraping {job_link}: {e}")

    finally:
        page.close()

    return {
        "title": "",
        "location": "",
        "description": ""
    }


# =========================================================
# PLAYWRIGHT
# =========================================================

with sync_playwright() as p:

    # -----------------------------------------------------
    # Launch browser ONLY ONCE
    # -----------------------------------------------------
    browser = p.chromium.launch(
        headless=False
    )

    context = browser.new_context()

    listing_page = context.new_page()

    # Keep track of already processed URLs
    processed_urls = set()

    # Open output file ONCE
    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as output:

        # -------------------------------------------------
        # Process every portal
        # -------------------------------------------------
        for config in all_portals:

            company = config["company"]

            print("\n" + "=" * 70)
            print(f"Company: {company}")
            print("=" * 70)

            try:

                listing_page.goto(
                    config["url"],
                    wait_until="domcontentloaded",
                    timeout=PAGE_TIMEOUT
                )

                # -----------------------------------------
                # Pagination
                # -----------------------------------------
                for page_number in range(1, MAX_PAGES + 1):

                    print(
                        f"\n[{company}] "
                        f"Processing page {page_number}"
                    )

                    # -------------------------------------
                    # Wait for job list
                    # -------------------------------------
                    try:
                        listing_page.wait_for_selector(
                            config["main_page"],
                            timeout=PAGE_TIMEOUT
                        )
                    except PlaywrightTimeoutError:
                        print(
                            f"No job list found for {company}"
                        )
                        break

                    # -------------------------------------
                    # Get job cards
                    # -------------------------------------
                    jobs = listing_page.locator(
                        config["jobs_list"]
                    )

                    total_jobs = jobs.count()

                    print(
                        f"Jobs found: {total_jobs}"
                    )

                    jobs_to_process = min(
                        total_jobs,
                        MAX_JOBS_PER_PAGE
                    )

                    # -------------------------------------
                    # Process jobs
                    # -------------------------------------
                    for job_index in range(jobs_to_process):

                        try:

                            job = jobs.nth(job_index)

                            if not job.is_visible():
                                continue

                            job_link = get_job_link(
                                job,
                                config
                            )

                            if not job_link:
                                print(
                                    f"Skipping job "
                                    f"{job_index + 1}: "
                                    f"No URL"
                                )
                                continue

                            # ---------------------------------
                            # Remove query parameters if required
                            # ---------------------------------
                            output_url = job_link

                            if not config["is_link_query"]:
                                output_url = job_link.split("?")[0]

                            # ---------------------------------
                            # Duplicate protection
                            # ---------------------------------
                            if output_url in processed_urls:
                                print(
                                    f"Duplicate skipped: "
                                    f"{output_url}"
                                )
                                continue

                            processed_urls.add(output_url)

                            print(
                                f"[{job_index + 1}/"
                                f"{jobs_to_process}] "
                                f"Scraping: {job_link}"
                            )

                            # ---------------------------------
                            # Scrape job detail
                            # ---------------------------------
                            job_data = scrape_job(
                                context,
                                config,
                                job_link
                            )

                            result = {
                                "source": "careers",
                                "title": job_data["title"],
                                "company": company,
                                "location": job_data["location"],
                                "url": output_url,
                                "description": job_data["description"]
                            }

                            # ---------------------------------
                            # Write JSONL
                            # ---------------------------------
                            output.write(
                                json.dumps(
                                    result,
                                    ensure_ascii=False
                                ) + "\n"
                            )

                            # Flush so data isn't lost
                            output.flush()

                            print(
                                f"Saved: "
                                f"{job_data['title']}"
                            )

                        except Exception as e:

                            print(
                                f"Job error "
                                f"[{job_index}]: {e}"
                            )

                    # -------------------------------------
                    # Next page
                    # -------------------------------------
                    next_selector = config.get(
                        "next_page"
                    )

                    if not next_selector:
                        break

                    try:

                        next_button = listing_page.locator(
                            next_selector
                        )

                        if (
                            next_button.count() == 0
                            or not next_button.is_visible()
                        ):
                            print(
                                "No next page."
                            )
                            break

                        # ---------------------------------
                        # Click next page
                        # ---------------------------------
                        next_button.click()

                        # Wait for navigation/content update
                        listing_page.wait_for_load_state(
                            "domcontentloaded"
                        )

                    except Exception as e:

                        print(
                            f"Pagination error: {e}"
                        )
                        break

            except Exception as e:

                print(
                    f"Portal error "
                    f"{company}: {e}"
                )

    # -----------------------------------------------------
    # Close browser once
    # -----------------------------------------------------
    browser.close()


print("\nCompleted!")
print(f"Output saved to: {OUTPUT_FILE}")