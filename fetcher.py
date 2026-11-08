import re
from curl_cffi.requests import AsyncSession
from logger_config import logger_init
from config import DEFAULT_HEADERS, DETAILS_URL, DETAILS_HEADERS, REVIEWS_API, REVIEWS_HEADERS
from urllib.parse import urlsplit

logger = logger_init()

class FetcherActions:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSession(impersonate="chrome124")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
      if self.session:
            await self.session.close()

    async def get_html_page(self, category_url: str) -> str | None:
        try:
            response = await self.session.get(
                url=category_url,
                headers=DEFAULT_HEADERS,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"[curl_cffi] Response recieved! Status: {response.status_code}. get_html_page")
                return response.text

            logger.warning(
                "[curl_cffi] PDP API response:\n"
                f"Status: {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Headers: {response.headers}\n"
                f"Body: {response.text[:3000]}"
            )
            return None

        except Exception as e:
            logger.error(f"[curl_cffi] Error: {e}. get_html_page")
            return None
    
    async def get_pdp_details(self, pdp_url: str):
        try:
            clean_url = urlsplit(pdp_url)._replace(fragment="").geturl()
            last = clean_url.rstrip("/").split("/")[-1]
            code = re.sub(r"\D", "", last)

            req_params = {
                "country": "UA",
                "lang": "ua",
                "ids": code,
                "platform": "desktop"
            }
            response = await self.session.get(
                url=DETAILS_URL,
                headers=DETAILS_HEADERS,
                params=req_params,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"[curl_cffi] Response recieved! Status: {response.status_code}. get_pdp_details")

                pdp_response = response.json()
                reviews_response = await self.get_reviews(code)
                if reviews_response:
                    pdp_response["reviews"] = reviews_response
                    
                return pdp_response

            logger.warning(
                "[curl_cffi] PDP API response:\n"
                f"Status: {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Headers: {response.headers}\n"
                f"Body: {response.text[:3000]}"
            )
            return None

        except Exception as e:
            logger.error(f"[curl_cffi] Error: {e}. get_pdp_details")
            return None
    
    async def get_reviews(self, code: int):
        try:
            reviews_params = {
                "country": "UA",
                "lang": "ua",
                "goods": code,
                "limit": 36,
                "page": 1,
                "sort": "from_buyer",
                "topSellerId": 5,
                "type": "comment"
            }
            response = await self.session.get(
                url=REVIEWS_API,
                params=reviews_params,
                headers=REVIEWS_HEADERS,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"[curl_cffi] Response reviews recieved successfully. get_reviews")
                return response.json()

            logger.warning(
                "[curl_cffi] PDP API response:\n"
                f"Status: {response.status_code}\n"
                f"URL: {response.url}\n"
                f"Headers: {response.headers}\n"
                f"Body: {response.text[:3000]}"
            )
            return None

        except Exception as e:
            logger.error(f"[curl_cffi] Error: {e}. get_reviews")
            return None
