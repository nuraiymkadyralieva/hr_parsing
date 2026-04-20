"""Entry point for the finance director lookup pipeline."""

from __future__ import annotations

import argparse
import time
from typing import Iterable

from config import Settings, load_settings
from deepseek_client import DeepSeekAPIError, DeepSeekClient
from fetcher import PageFetcher
from html_cleaner import clean_html_to_text, truncate_text
from input_reader import InputReader
from keyword_filter import extract_relevant_chunk, has_finance_keywords
from logger_setup import setup_logger
from models import InputCompanyRow, OutputRow, ProcessingStats
from output_writer import OutputWriter
from prompt_builder import build_extraction_prompt
from result_parser import extract_json_block, parse_director_result
from search_client import SearchAPIError, SerperSearchClient, build_search_queries


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Bulk finance director parser")
    parser.add_argument("--input", required=True, help="Path to input .xlsx file")
    parser.add_argument("--output", required=True, help="Path to output .xlsx file")
    parser.add_argument("--limit", type=int, default=None, help="Optional row processing limit")
    return parser.parse_args()


def run_pipeline(
    settings: Settings,
    input_path: str,
    output_path: str,
    limit: int | None = None,
) -> None:
    """Run the main finance director extraction pipeline."""
    logger = setup_logger()

    reader = InputReader(input_path)
    writer = OutputWriter(output_path)
    search_client = SerperSearchClient(
        api_key=settings.serper_api_key,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )
    fetcher = PageFetcher(
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )
    deepseek_client = DeepSeekClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )

    input_rows = reader.read_rows()
    if limit is not None:
        input_rows = input_rows[:limit]

    stats = ProcessingStats(total_rows=len(input_rows))

    for company_row in input_rows:
        process_company(
            company_row=company_row,
            settings=settings,
            writer=writer,
            search_client=search_client,
            fetcher=fetcher,
            deepseek_client=deepseek_client,
            stats=stats,
        )
        time.sleep(settings.sleep_between_requests)

    writer.save()
    log_stats(stats)
    logger.info("Output saved to: %s", output_path)


def process_company(
    company_row: InputCompanyRow,
    settings: Settings,
    writer: OutputWriter,
    search_client: SerperSearchClient,
    fetcher: PageFetcher,
    deepseek_client: DeepSeekClient,
    stats: ProcessingStats,
) -> None:
    """Process one company and always write exactly one output row."""
    logger = setup_logger()
    logger.info(
        "Processing row %s: %s",
        company_row.row_index,
        company_row.company or company_row.registration_number,
    )

    finance_position = ""
    finance_full_name = ""

    try:
        search_queries = build_search_queries(company_row.company)
        collected_urls: list[str] = []

        for query in search_queries:
            try:
                search_results = search_client.search(
                    query=query,
                    num_results=settings.top_search_results,
                )
                collected_urls.extend(search_results)
            except SearchAPIError as error:
                stats.search_errors += 1
                logger.error(
                    "Search error for company '%s' with query '%s': %s",
                    company_row.company,
                    query,
                    error,
                )

        unique_urls = deduplicate_urls(collected_urls)[: settings.max_pages_per_company]

        for url in unique_urls:
            html = fetcher.fetch(url)
            if not html:
                stats.fetch_errors += 1
                logger.error("Fetch error or empty response for URL: %s", url)
                continue

            cleaned_text = clean_html_to_text(html)
            if not cleaned_text:
                continue

            if not has_finance_keywords(cleaned_text):
                continue

            relevant_text = extract_relevant_chunk(cleaned_text)
            prompt_text = truncate_text(relevant_text, settings.max_text_length)
            prompt = build_extraction_prompt(company_row.company, prompt_text)

            try:
                raw_response = deepseek_client.ask(prompt)
            except DeepSeekAPIError as error:
                stats.api_errors += 1
                logger.error("DeepSeek error for company '%s': %s", company_row.company, error)
                continue

            if extract_json_block(raw_response) is None:
                stats.parse_errors += 1
                logger.error("Parsing error for company '%s': JSON block not found", company_row.company)
                continue

            position, person_fio = parse_director_result(raw_response)
            if position and person_fio:
                finance_position = position
                finance_full_name = person_fio
                break

            stats.parse_errors += 1
            logger.error("Parsing error for company '%s': invalid finance director result", company_row.company)

        if finance_position and finance_full_name:
            stats.found_director += 1
        else:
            stats.empty_result += 1
    except Exception as error:
        logger.error("Unexpected error for company '%s': %s", company_row.company, error)
    finally:
        writer.add_row(
            OutputRow(
                company=company_row.company,
                registration_number=company_row.registration_number,
                finance_position=finance_position,
                finance_full_name=finance_full_name,
            )
        )
        stats.processed_rows += 1


def deduplicate_urls(urls: Iterable[str]) -> list[str]:
    """Remove duplicate URLs while preserving original order."""
    seen: set[str] = set()
    unique_urls: list[str] = []

    for url in urls:
        normalized_url = url.strip()
        if not normalized_url or normalized_url in seen:
            continue
        seen.add(normalized_url)
        unique_urls.append(normalized_url)

    return unique_urls


def log_stats(stats: ProcessingStats) -> None:
    """Write final processing stats to the logger."""
    logger = setup_logger()
    logger.info("Processing finished")
    logger.info("total_rows=%s", stats.total_rows)
    logger.info("processed_rows=%s", stats.processed_rows)
    logger.info("found_director=%s", stats.found_director)
    logger.info("empty_result=%s", stats.empty_result)
    logger.info("search_errors=%s", stats.search_errors)
    logger.info("fetch_errors=%s", stats.fetch_errors)
    logger.info("api_errors=%s", stats.api_errors)
    logger.info("parse_errors=%s", stats.parse_errors)


def main() -> None:
    """Parse arguments and run the pipeline."""
    args = parse_args()
    settings = load_settings()
    run_pipeline(
        settings=settings,
        input_path=args.input,
        output_path=args.output,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
