from playwright.sync_api import sync_playwright
import json
import os

URL = "https://www.naukri.com/data-engineer-jobs-in-india?k=data%20engineer&l=india&jobAge=1"

OUTPUT_DIR = "output"
OUTPUT_FILE = f"{OUTPUT_DIR}/naukri_jobs.jsonl"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clear previous output file (optional)
with open(OUTPUT_FILE, "w", encoding="utf-8"):
    pass

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    # Open Indeed
    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=30000
    )

    for i in range(3):

        # Wait for job cards
        page.wait_for_selector(
            "div.srp-jobtuple-wrapper",
            timeout=30000
        )

        jobs = page.locator("div.cust-job-tuple")

        total_jobs = jobs.count()

        print(f"Total jobs found: {total_jobs}")

        for i in range(total_jobs):

            try:

                # Re-locate jobs because page DOM can change
                jobs = page.locator("div.cust-job-tuple")

                job = jobs.nth(i)

                # Skip hidden job cards
                if not job.is_visible():
                    continue

                # -------------------------
                # TITLE
                # -------------------------
                title = job.locator(
                    "a.title"
                ).get_attribute("title")

                company = job.locator(
                    "a.comp-name"
                ).get_attribute("title")

                try:
                    location = job.locator(
                        "span.locWdth[title]"
                    ).get_attribute("title")
                except:
                    location = ""

                job_link = job.locator(
                    "a.title"
                ).get_attribute("href")
                job_page = browser.new_page()
                description = ''
                try:
                    job_page.goto(
                        job_link,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )
                    job_page.wait_for_selector("section.styles_job-desc-container__txpYf")
                    description = job_page.locator("section.styles_job-desc-container__txpYf").inner_text()
                    job_page.close()
                except Exception as e:
                    print(e)
                data = {
                        "source": "naukri",
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": job_link,
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
                print(e)
        page.get_by_role("link", name="Next ").click()

    browser.close()


print(f"\nCompleted!")
print(f"Output saved to: {OUTPUT_FILE}")