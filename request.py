import aiohttp
from asyncio import run
from bs4 import BeautifulSoup as bs


BASE_URL = "https://www.ss.com/en/transport/cars/"


async def fetch_soup(url: str) -> bs | None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            return bs(html, "lxml") if html else None


def extract_options(soup, selector: str, *, 
                    exclude_text: list[str] = None, 
                    exclude_value: list[str] = None,
                    value_filter: callable = None,
                    sort: bool = True,
                    reverse: bool = False) -> list[str]:
    opts = soup.select(selector)
    if not opts:
        return []

    result = []
    for opt in opts:
        text = opt.text.strip()
        val = opt.get("value", "")
        if exclude_text and text in exclude_text:
            continue
        if exclude_value and val in exclude_value:
            continue
        if not text:
            continue
        if value_filter and not value_filter(val):
            continue
        result.append(text)

    return sorted(result, reverse=reverse) if sort else result


async def get_list_cars() -> list[dict]:
    excluded_brands = {
        "Electric cars", "Exclusive cars", "Retro cars", "Sport cars", "Tuned cars",
        "Car exchange","Auto evacuation", "Car rent", "Car repair and service",
        "Cars with defects or after crash", "Spare parts and accessories", "Trailers",
        "Transport for invalids", "Trunks, wheels","Tuning", "Others", "Tesla"
    }
    soup = await fetch_soup(BASE_URL)
    if not soup:
        return []

    brands = [{"car": a.text.strip(), "url": a.get("href")} for a in soup.select("a.a_category") if a.text.strip() not in excluded_brands]

    return sorted(brands, key=lambda x: x["car"])


async def get_models_cars(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='cid[]'] option", exclude_text=["All","Another","Car rent","Spare parts","Car exchange"])


async def get_years(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='topt[18][min]'] option", value_filter=lambda v: v.isdigit() and int(v) >= 1960, reverse=True)


async def get_displacement_motor(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='topt[15][max]'] option")


async def get_typengines(url: str) -> list[str]:
    soup = await fetch_soup(url)
    return extract_options(soup, "select[name='opt[34][]'] option", exclude_value=[''])


async def get_gearbox(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='opt[35][]'] option")


async def get_bodytype(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='opt[32][]'] option", exclude_text=["-"], exclude_value=[""])


async def get_inspection(url: str) -> list[str]:
    return extract_options(await fetch_soup(url), "select[name='opt[223][]'] option", value_filter=lambda v: not v.isdigit())


async def get_models(url: str) -> dict[str, list[str]]:
    soup = await fetch_soup(url)
    if not soup:
        return {}

    span = next((s for s in soup.select("span.filter_opt_dv") if "Model:" in s.get_text()), None)
    if not span:
        return {}

    select = span.select_one("select.filter_sel")
    if not select:
        return {}

    skip = {"All", "Another", "Car rent", "Spare parts", "Car exchange", "Citan", "Sprinter", "Vaneo", "Viano", "Vito"}
    result, current = {}, None

    for opt in select.select("option"):
        text = opt.text.strip()

        if "font-weight:bold" in opt.get("style", "").replace(" ", ""):
            current = text
            result[current] = []
            continue

        if text in skip or not current:
            continue

        result[current].append(text)

    return result


# async def main():
#     print('test')
#     resp = await get_list_cars()  #https://www.ss.com/en/transport/cars/suzuki/swift/search/
#     print(resp)


# run(main())
