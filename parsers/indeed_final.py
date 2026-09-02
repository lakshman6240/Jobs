from playwright.sync_api import sync_playwright
import json
import os

URL = "https://in.indeed.com/jobs?q=data+engineer&l=India&fromage=1"

OUTPUT_DIR = "output"
OUTPUT_FILE = f"{OUTPUT_DIR}/indeed_jobs.jsonl"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clear previous output file (optional)
with open(OUTPUT_FILE, "w", encoding="utf-8"):
    pass

for i in ["", "&start=10", "&start=20", "&start=30"]:
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        # Open Indeed
        page.goto(
            URL+i,
            wait_until="domcontentloaded",
            timeout=30000
        )

        # Wait for job cards
        page.wait_for_selector(
            "div.job_seen_beacon",
            timeout=30000
        )

        # Close cookie popup safely
        try:
            page.locator(
                "#onetrust-reject-all-handler"
            ).click(timeout=3000)
        except:
            pass

        jobs = page.locator("div.job_seen_beacon")

        total_jobs = jobs.count()

        print(f"Total jobs found: {total_jobs}")

        for i in range(total_jobs):

            try:

                # Re-locate jobs because page DOM can change
                jobs = page.locator("div.job_seen_beacon")

                job = jobs.nth(i)

                # Skip hidden job cards
                if not job.is_visible():
                    continue

                # -------------------------
                # TITLE
                # -------------------------
                title = job.locator(
                    "h3.jobTitle"
                ).inner_text()

                # -------------------------
                # COMPANY
                # -------------------------
                company_locator = job.locator(
                    '[data-testid="company-name"]'
                )

                company = (
                    company_locator.first.inner_text()
                    if company_locator.count() > 0
                    else None
                )

                # -------------------------
                # LOCATION
                # -------------------------
                location_locator = job.locator(
                    '[data-testid="text-location"]'
                )

                location = (
                    location_locator.first.inner_text()
                    if location_locator.count() > 0
                    else None
                )

                # -------------------------
                # JOB LINK + JOB ID
                # -------------------------
                job_link = job.locator(
                    "a[data-jk]"
                ).first

                job_key = job_link.get_attribute(
                    "data-jk"
                )

                job_url = (
                    f"https://in.indeed.com/viewjob?jk={job_key}"
                    if job_key
                    else None
                )

                # -------------------------
                # CLICK JOB
                # -------------------------
                job_link.scroll_into_view_if_needed()

                job_link.click(timeout=10000)

                # -------------------------
                # DESCRIPTION
                # -------------------------
                description_locator = page.locator(
                    "#jobDescriptionText"
                )

                try:

                    description_locator.wait_for(
                        state="visible",
                        timeout=10000
                    )

                    description = (
                        description_locator
                        .inner_text()
                    )

                except:
                    description = None

                # -------------------------
                # JOB DATA
                # -------------------------
                data = {
                    "source": "indeed",
                    "job_id": job_key,
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": job_url,
                    "description": description
                }

                # -------------------------
                # WRITE TO JSONL
                # -------------------------
                with open(
                    OUTPUT_FILE,
                    "a",
                    encoding="utf-8"
                ) as f:

                    f.write(
                        json.dumps(
                            data,
                            ensure_ascii=False
                        ) + "\n"
                    )

                print(
                    f"[{i + 1}/{total_jobs}] "
                    f"Saved: {title}"
                )

            except Exception as e:

                print(
                    f"[ERROR] Job {i + 1}: {e}"
                )

        browser.close()


print(f"\nCompleted!")
print(f"Output saved to: {OUTPUT_FILE}")