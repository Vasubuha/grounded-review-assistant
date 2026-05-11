from ddgs import DDGS
from urllib.parse import urlparse, parse_qs
import re
import time


def normalize_flipkart_review_url(url: str) -> str:
    """
    Converts Flipkart product URL into dedicated review URL.
    """

    try:
        if "product-reviews" in url:
            return url

        parsed = urlparse(url)

        path = parsed.path

        # Extract product slug
        match = re.search(r"(/p/|/itm)(.*)", path)

        if "/p/" not in path:
            return url

        review_path = path.replace("/p/", "/product-reviews/")

        query = parse_qs(parsed.query)

        pid = query.get("pid", [""])[0]

        if pid:
            return (
                f"https://www.flipkart.com"
                f"{review_path}?pid={pid}&marketplace=FLIPKART"
            )

        return f"https://www.flipkart.com{review_path}"

    except Exception:
        return url


def normalize_amazon_review_url(url: str) -> str:
    """
    Converts Amazon product URL into review-focused URL.
    """

    try:
        match = re.search(r"/dp/([A-Z0-9]+)/", url)

        if not match:
            return url

        asin = match.group(1)

        return (
            f"https://www.amazon.in/product-reviews/{asin}"
            f"?reviewerType=all_reviews"
        )

    except Exception:
        return url


def expand_sources(canonical_name: str, model_number: str = "") -> dict:
    """
    Discover authoritative ecommerce, review, YouTube,
    and specification URLs for a product.
    """

    print(f"[Expander] Expanding sources for: {canonical_name}")

    sources = {
        "amazon": None,
        "amazon_reviews": None,
        "flipkart": None,
        "flipkart_reviews": None,
        "youtube": None,
        "spec": None
    }
    
    def is_valid_match(href: str, title: str) -> bool:
        if not model_number: return True
        model_words = model_number.lower().split()
        text = (href + " " + title).lower()
        for word in model_words:
            if any(char.isdigit() for char in word) and word not in text:
                return False
        return True

    with DDGS() as ddgs:

        # AMAZON
        try:
            amazon_results = list(
                ddgs.text(
                    f"site:amazon.in {canonical_name}",
                    max_results=5
                )
            )

            for res in amazon_results:

                href = res.get("href", "")
                title = res.get("title", "")
                
                if not is_valid_match(href, title):
                    continue

                if "amazon.in" in href and "/dp/" in href:

                    sources["amazon"] = href

                    sources["amazon_reviews"] = (
                        normalize_amazon_review_url(href)
                    )

                    break

        except Exception as e:
            print(f"[Expander] Amazon search error: {e}")

        time.sleep(1)

        # FLIPKART
        try:
            flipkart_results = list(
                ddgs.text(
                    f"site:flipkart.com {canonical_name}",
                    max_results=5
                )
            )

            for res in flipkart_results:

                href = res.get("href", "")
                title = res.get("title", "")
                
                if not is_valid_match(href, title):
                    continue

                if (
                    "flipkart.com" in href
                    and "/p/" in href
                ):

                    sources["flipkart"] = href

                    sources["flipkart_reviews"] = (
                        normalize_flipkart_review_url(href)
                    )

                    break

        except Exception as e:
            print(f"[Expander] Flipkart search error: {e}")

        time.sleep(1)

        # YOUTUBE
        try:
            yt_results = list(
                ddgs.text(
                    f"site:youtube.com {canonical_name} review",
                    max_results=5
                )
            )

            for res in yt_results:

                href = res.get("href", "")
                title = res.get("title", "")
                
                if not is_valid_match(href, title):
                    continue

                if "youtube.com/watch" in href:

                    sources["youtube"] = href
                    break

        except Exception as e:
            print(f"[Expander] YouTube search error: {e}")

        time.sleep(1)

        # SPECS
        try:
            spec_results = list(
                ddgs.text(
                    (
                        f"(site:gsmarena.com "
                        f"OR site:gadgets360.com) "
                        f"{canonical_name} specifications"
                    ),
                    max_results=5
                )
            )

            for res in spec_results:

                href = res.get("href", "")
                title = res.get("title", "")
                
                if not is_valid_match(href, title):
                    continue

                if (
                    "gsmarena.com" in href
                    or "gadgets360.com" in href
                ):

                    sources["spec"] = href
                    break

        except Exception as e:
            print(f"[Expander] Spec search error: {e}")

    print("[Expander] Final discovered sources:")

    for key, value in sources.items():
        print(f"  {key}: {value}")

    return sources