import os
import asyncio
from loguru import logger
from typing import List, Dict, Any
from datetime import datetime
from entity_analysis import analyze_content, scrape_content, compare_pages, select_entities_for_integration, generate_entity_recommendations
from utils import create_excel_report, get_competitor_name, validate_urls
from collections import defaultdict
import aiohttp
from data_models import EntitySelections

urls = {
    "client_url": "https://turbotax.intuit.com/tax-tips/jobs-and-career/how-bonuses-are-taxed/L7UjtAZbh",
    "competitor_urls": [
        "https://www.fidelity.com/learning-center/smart-money/bonus-tax-rate",
        "https://www.oysterhr.com/library/how-are-bonuses-taxed",
        "https://www.bankrate.com/taxes/how-bonuses-are-taxed/"
    ]
}

async def run_analysis(client_url: str, competitor_urls: List[str], credentials_path: str) -> Dict[str, Any]:
    """Run the complete content analysis."""
    # Initialize domain counter
    used_domains = defaultdict(int)

    # Create mapping of URLs to competitor names
    competitor_names = {url: get_competitor_name(url, used_domains) for url in competitor_urls}

    async with aiohttp.ClientSession() as session:
        # Scrape content concurrently
        logger.info("Scraping content from a URL...")
        scrape_tasks = [scrape_content(client_url, session)] + [scrape_content(url, session) for url in competitor_urls]
        scrape_results = await asyncio.gather(*scrape_tasks)

        client_content = scrape_results[0]
        if not client_content:
            raise Exception("Failed to scrape client page")

        competitive_contents = scrape_results[1:]
        valid_competitor_urls = [url for url, content in zip(competitor_urls, competitive_contents) if content]
        competitive_contents = [content for content in competitive_contents if content]

        all_documents = [client_content] + competitive_contents

        # Run analysis concurrently
        logger.info("Analyzing content using Google Cloud Natural Language API...")
        analysis_tasks = [analyze_content(client_content, credentials_path, all_documents)] + [
            analyze_content(content, credentials_path, all_documents) for content in competitive_contents
        ]
        analysis_results = await asyncio.gather(*analysis_tasks)

        client_analysis = analysis_results[0]
        competitive_analyses = analysis_results[1:]

        # Compare results
        logger.info("Comparing the client page analysis to the competitive pages...")
        comparison_results = compare_pages(client_analysis, competitive_analyses, valid_competitor_urls)

        # Update competitor names in the results
        for analysis_type in ["missing_entities", "missing_keywords"]:
            for item_name, item_data in comparison_results[analysis_type].items():
                updated_competitors = {}
                for url, metrics in item_data["competitors"].items():
                    updated_competitors[competitor_names[url]] = metrics
                item_data["competitors"] = updated_competitors

        # Select entities for integration
        logger.info("AI Job: Selecting entities for integration...")
        selected_entities_response = await select_entities_for_integration(comparison_results.get("missing_entities", {}))
        selected_entities = selected_entities_response.selected_entities

        # Generate recommendations for selected entities concurrently
        logger.info("AI Job: Generating recommendations for selected entities...")
        recommendation_tasks = [generate_entity_recommendations(entity_selection, client_content) for entity_selection in selected_entities]
        recommendations = await asyncio.gather(*recommendation_tasks)

        entity_recommendations = {entity_selection.entity_name: recommendation for entity_selection, recommendation in zip(selected_entities, recommendations)}

        recommendation_overview = EntitySelections(selected_entities=selected_entities)

        return {
            "client_analysis": client_analysis,
            "competitive_analyses": competitive_analyses,
            "comparison_results": comparison_results,
            "competitor_names": competitor_names,
            "entity_recommendations": entity_recommendations,
            "client_url": client_url,
            "recommendation_overview": recommendation_overview
        }


async def main(urls: dict, output_folder: str = "output"):
    client_url = urls["client_url"]
    competitor_urls = urls["competitor_urls"]

    if not client_url:
        logger.error("Please enter a client URL")
        return

    if len(competitor_urls) < 2:
        logger.error("Please enter at least 2 competitor URLs")
        return

    try:
        # Initialize progress bar
        logger.info("Operation in progress. Please wait.")

        # Step 1: URL Validation (10%)
        if not validate_urls([client_url] + competitor_urls):
            logger.error("Invalid URL format. Please enter valid URLs.")
            return

        analysis_results = await run_analysis(
            client_url,
            competitor_urls,
            credentials_path="./service_account.json"
        )

        
        # export
        logger.info("Creating analysis report...")
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_data = create_excel_report(analysis_results)
        excel_filename = f"analysis_report_{current_time}.xlsx"

        # write to output folder (create if not exists)
        logger.info(f"Saving report to: {output_folder}")
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, excel_filename)
        with open(output_path, "wb") as file:
            file.write(excel_data)

        logger.info(f"Analysis completed successfully. Report saved to: {output_path}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return


if __name__ == "__main__":
    asyncio.run(main(urls))