from lxml import html
from pydantic import BaseModel, TypeAdapter, HttpUrl, Field, ConfigDict

class ModelURL(BaseModel):
    url: HttpUrl
page_results = TypeAdapter(list[ModelURL])

class ProductDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    url: HttpUrl = Field(alias="href")
    title: str
    brand: str | None = None
    price: int
    old_price: int | None = None
    discount: int | None = None
    images: list[HttpUrl] = Field(default_factory=list)
    sell_status: str | None = None
    comments_amount: int | None = None
    comments_mark: float | None = None
    seller: dict | None = None
    product_description: list[dict] | str | None = Field(default=None, alias="docket")
    variant_parameters: dict | None = Field(default=None, alias="var_params")
    reviews: list[dict] | None = None

def get_total_pages(h: str) -> int:
    tree = html.fromstring(h)
    total = tree.xpath('(//nav[@data-testid="paginator"]//*[@data-testid="page-number"])[last()]')
    return int(total[0].text_content().strip()) if total else 1

def parse_pdp_urls(h: str) -> list[ModelURL]:
    results = []
    tree = html.fromstring(h)
    products_list = tree.xpath('//rz-catalog-goods/rz-catalog-tile-placeholder//article')
    for node in products_list:
        product_url = node.xpath('./a[1]/@href')
        if product_url:
            results.append({"url": product_url[0]})
    return page_results.validate_python(results)

def pagination_urls(category_url: str, total_pages: int) -> list[str]:
    category_url = category_url.rstrip("/") + "/"
    return [f"{category_url}page={i}/" for i in range(1, total_pages + 1)]

def parse_json_details(response_json: dict) -> ProductDetails:
    data = response_json["data"][0]
    reviews = response_json["reviews"]["data"]["comments"] or []

    data["images"] = data["images"]["all"]
    data["reviews"] = [
        {
            "rev_id": rev["id"],
            "title": rev["dignity"],
            "content": rev["text"],
            "min_rating": 1,
            "max_rating": 5,
            "rating": rev["mark"]
        }
        for rev in reviews
    ]
    return ProductDetails.model_validate(data)
