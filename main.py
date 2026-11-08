import json
import asyncio
from fetcher import FetcherActions
from parser import ProductDetails, ModelURL, get_total_pages, pagination_urls, parse_pdp_urls, parse_json_details
from logger_config import logger_init
import argparse

logger = logger_init()

async def collect_pdps(fetcher: FetcherActions, pagination_url: str) -> list[ModelURL]:
    page_html = await fetcher.get_html_page(pagination_url)

    if not page_html:
        return []

    pdp_urls = parse_pdp_urls(page_html)
    logger.info(f"[collect_pdps] Extracted {len(pdp_urls)} items from {pagination_url}")
    return pdp_urls

async def category_worker(queue: asyncio.Queue[str], fetcher: FetcherActions, results: list[ModelURL]) -> None:
    while True:
        pagination_url = await queue.get()
        try:
            pdp_urls = await collect_pdps(fetcher, pagination_url)
            results.extend(pdp_urls)
        except Exception:
            logger.exception(f"[category_worker] Error processing {pagination_url}")
        finally:
            queue.task_done()

async def pdp_details(fetcher: FetcherActions, pdp_url: str):
    response_json = await fetcher.get_pdp_details(pdp_url)

    if not response_json:
        return None

    pdp_details = parse_json_details(response_json)
    logger.info(f"[pdp_details] Parsed details from {pdp_url}")
    return pdp_details

async def pdp_worker(queue: asyncio.Queue[str], fetcher: FetcherActions, results) -> None:
    while True:
        pdp_url = await queue.get()
        try:
            details_data = await pdp_details(fetcher, pdp_url)
            if details_data is not None:
                results.append(details_data)
        except Exception as e:
            logger.error(f"[pdp_worker] Error processing {pdp_url}: {e}")
        finally:
            queue.task_done()

async def main():
    parser = argparse.ArgumentParser(description="Collect pdp from categories")
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        required=True,
        help="URL to process",
    )
    args = parser.parse_args()

    async with FetcherActions() as fetcher:
        page_html = await fetcher.get_html_page(args.url)
        if not page_html:
            return
        total_pages = get_total_pages(page_html)

        categories_queue = asyncio.Queue()
        category_results: list[ModelURL] = []

        for url in pagination_urls(args.url, total_pages):
            await categories_queue.put(url)

        category_workers = [
            asyncio.create_task(category_worker(categories_queue, fetcher, category_results))
            for _ in range(10)
        ]
        await categories_queue.join()
        for task in category_workers:
            task.cancel()
        await asyncio.gather(*category_workers, return_exceptions=True)
        
        pdp_urls = list(set([str(item.url) for item in category_results]))
        logger.info(f"Total URLs: {len(pdp_urls)}")
        logger.info(f"Unique URLs: {len(set(pdp_urls))}")
        logger.info(f"Duplicates: {len(pdp_urls) - len(set(pdp_urls))}")
        logger.info(f"Total collected: {len(pdp_urls)}")
        
        pdp_queue = asyncio.Queue()
        pdp_results: list[ProductDetails] = []

        for url in pdp_urls:
            await pdp_queue.put(url)

        pdp_workers = [
            asyncio.create_task(pdp_worker(pdp_queue, fetcher, pdp_results))
            for _ in range(15)
        ]

        await pdp_queue.join()
        for task in pdp_workers:
            task.cancel()
        await asyncio.gather(*pdp_workers, return_exceptions=True)
        
        products_data = [product.model_dump(mode="json") for product in pdp_results]

        logger.info(f"Total collected: {len(products_data)}")
        with open("products.json", "w", encoding="utf-8") as file:
            json.dump(products_data, file, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
