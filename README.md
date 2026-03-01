# Job Notification System

## Overview
This job notification system is designed to scrape job listings from popular job platforms, specifically LinkedIn and Naukri. It aims to provide users with timely notifications when new job listings match their preferences.

## Workflow
1. **User Registration**: Users register on the system, providing their job preferences.
2. **Job Scraping**: The system regularly scrapes job listings from LinkedIn and Naukri based on user preferences.
3. **Data Storage**: Scraped job data is stored in a database for further processing.
4. **Notification System**: Users are notified about new job listings via telegram bot notifications.

## Data Flow
1. **Data Input**: Job listings from LinkedIn and Naukri are collected.
2. **Database Storage**: The data is stored in a structured format in the database.
3. **Notification Trigger**: The system checks for new listings and triggers notifications based on user preferences.

## Job Scraping Process
- **LinkedIn Scraper**: 
  - Accesses LinkedIn pages to collect job data using specific queries.
  - Parses HTML data to extract job titles, companies, locations, and descriptions.

- **Naukri Scraper**: 
  - Similar to the LinkedIn scraper, it accesses Naukri job listings and extracts relevant information.
  - Handles pagination to ensure all job listings are captured.

- **Indeed Scraper**: 
  - Similar to the LinkedIn scraper, it accesses Indeed job listings and extracts relevant information.
  - Handles pagination to ensure all job listings are captured.

