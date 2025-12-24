from pathlib import Path
from collections import deque
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
import threading, asyncio, json, os, aiohttp, random, logging

from playwright.async_api import async_playwright

from config import settings
from request import fetch_soup


class SearchThread(threading.Thread):
    def __init__(self, data_search: dict, uid: int):
        super().__init__()
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.data_search = dict(data_search)
        self.data_attempts = {key: 0 for key in data_search}
        self.seen_ids = {key: set() for key in data_search}

        self.queue = asyncio.Queue()
        self.rate_limit = 2.0 


    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        worker_task = loop.create_task(self._worker()) 
        loop.run_until_complete(self.loop())           
        loop.run_until_complete(worker_task)      


    def add_filter(self, new_filter: dict):
        with self.lock:
            for key, value in new_filter.items():
                if key not in self.data_search:
                    self.data_search[key] = value
                    self.data_attempts[key] = 0
                    self.seen_ids[key] = set()
                    print(f"Фильтр добавлен напрямую: {key}")

    
    def update_filter(self, new_filter: dict):
        with self.lock:
            for key, value in new_filter.items():
                if key in self.data_search:
                    existing = self.data_search[key]
                    if isinstance(existing, dict) and isinstance(value, dict):
                        for field, field_value in value.items():
                            if field not in existing or existing[field] != field_value:
                                existing[field] = field_value
                                print(f"Поле '{field}' обновлено для фильтра {key}")
                    else:
                        self.data_search[key] = value
                        print(f"Фильтр {key} обновлён целиком")

                    self.data_attempts[key] = 0
                    self.seen_ids[key] = set()
                    print(f"Сброс состояния для фильтра {key}")


    def has_filter(self, key: str) -> bool:
        with self.lock:
            return key in self.data_search


    def remove_filter(self, key: str):
        with self.lock:
            if key in self.data_search:
                self.data_search.pop(key, None)
                self.data_attempts.pop(key, None)
                self.seen_ids.pop(key, None)
                print(f"Фильтр удалён напрямую: {key}")


    async def loop(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                while not self.stop_event.is_set():
                    with self.lock:
                        keys = list(self.data_search.keys())

                    new_ads_data = []

                    for key in keys:
                        info = self.data_search[key]

                        context = await browser.new_context()

                        page_obj = await self._open_page(context, key, info)
                        page = page_obj["page"]

                        new_ads = await self._process_page(page, info, key)
                        if new_ads:
                            for new_ad in new_ads:
                                new_ads_data.append((new_ad, info))

                        await page.close()
                        await context.close()

                    if new_ads_data:
                        for data, info in new_ads_data:
                            await self.queue.put((info, data))
                            await asyncio.sleep(random.randint(5, 12))

                    await asyncio.sleep(15)

            finally:
                await browser.close()


    async def _open_page(self, context, key, info):
        page = await context.new_page()
        await page.goto(info["url"] + "search/")
        await page.wait_for_load_state("networkidle")
        return {"page": page, "info": info, "key": key}


    async def _process_page(self, page, info, key):
        await asyncio.sleep(1)

        options = {
            "select[name='cid[]']": info.get('models'),
            "select[name='topt[18][min]']": info.get("min_year"),
            "select[name='topt[18][max]']": info.get("max_year"),
            "input[name='topt[15][min]']": info.get("min_displacement"),
            "input[name='topt[15][max]']": info.get("max_displacement"),
            "select[name='opt[34][]']": info.get("typengines"),
            "select[name='opt[35][]']": info.get("gearbox"),
            "select[name='opt[32][]']": info.get("bodytypes"),
            "select[name='opt[223][]']": info.get("inspection"),
            "input[name='topt[8][min]']": info.get("min_price"),
            "input[name='topt[8][max]']": info.get("max_price"),
            "select[name='sid']": "Sell"
        }

        for selector, value in options.items():
            if value is None:
                continue
            try:
                if selector.startswith("select"):
                    options_elements = await page.query_selector_all(selector + " option")
                    available_labels = [await opt.inner_text() for opt in options_elements]

                    if isinstance(value, list):
                        valid_values = [str(v) for v in value if str(v) in available_labels]
                        if valid_values:
                            await page.select_option(selector, label=valid_values, timeout=3000)
                    else:
                        if str(value) in available_labels:
                            await page.select_option(selector, label=str(value), timeout=3000)

                elif selector.startswith("input"):
                    await page.fill(selector, str(value))
            except Exception as e:
                print(e)
                print('error')

        await page.click("#sbtn")
        await page.wait_for_load_state("networkidle")

        ads = await page.query_selector_all("a.am")
        if not ads:
            return None

        with self.lock:
            attempt = self.data_attempts.get(key, 0)

        logging.info(f"key={key} | {info.get('name_car')} | attempt={attempt}")

        new_ads = []
        for ad in ads[:10]:
            title = await ad.inner_text()
            href = await ad.get_attribute("href")
            listing = f"{title}: {href}"

            with self.lock:
                if key not in self.seen_ids or key not in self.data_attempts:
                    return None

                if attempt == 0:
                    self.seen_ids[key].add(listing)
                else:
                    if listing not in self.seen_ids[key]:
                        self.seen_ids[key].add(listing)
                        logging.info(f"Новое объявление [{key}] | https://www.ss.com{href} |")

                        if href:
                            data = await generate_message(url=f'https://www.ss.com{href}')
                            if data.get("success", False):
                                new_ads.append(data)
                            else:
                                logger.warning(data.get("error"))

        with self.lock:
            if ads:
                self.data_attempts[key] = attempt + 1

        return new_ads if new_ads else None


    async def _worker(self):
        async with aiohttp.ClientSession() as client:
            while not self.stop_event.is_set():
                info, data = await self.queue.get()
                img_src = data.get('image')
                message = data.get('message')

                try:
                    resp = await client.post(
                        f"https://api.telegram.org/bot{settings.TOKEN}/sendPhoto",
                        data={
                            "chat_id": info.get('uid'),
                            "photo": img_src,
                            "caption": message,
                            "parse_mode": "HTML"
                        },
                    )
                    result = await resp.json()
                    if not result.get("ok"):
                        if result.get("error_code") == 429:
                            retry_after = result["parameters"]["retry_after"]
                            print(f"Flood control, sleeping {retry_after} sec")
                            await asyncio.sleep(retry_after)
                        else:
                            print("Telegram error:", result)
                except Exception as e:
                    print("Send error:", e)

                await asyncio.sleep(self.rate_limit)


    def stop(self):
        self.stop_event.set()


class ThreadManager:
    def __init__(self):
        self.file_path = Path('data_tasks/active_threads.json')
        self.active_threads: dict[int, SearchThread] = {}

    
    def _load_db(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}


    def start_threads(self, data_search: dict, uid: int) -> bool:
        db = self._load_db()
        active_filters = db.setdefault(str(uid), [])
        existing_keys = {list(item.keys())[0] for item in active_filters}

        if not self.active_threads.get(uid, None):
            thread = SearchThread(data_search=data_search, uid=uid)
            self.active_threads[uid] = thread
            thread.start()
        else:
            thread = self.active_threads.get(uid)
            if thread:
                for key, value in data_search.items():
                    if not thread.has_filter(key=key):
                        thread.add_filter({key: value})
                        

        for key, value in data_search.items():
            if key not in existing_keys:
                active_filters.append({key: value})

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)


    def stop_threads(self, uid: int):
        thread = self.active_threads.get(uid)
        if thread:
            thread.stop()
            del self.active_threads[uid]
        
        print(self.active_threads)

    
    def restart_threads(self) -> None:
        db = self._load_db()
        for uid, filters in db.items():
            uid_int = int(uid)

            for filter_entry in filters:
                for key in filter_entry.keys():
                    self.start_threads(data_search=filter_entry, uid=uid_int)

                    print(f"Thread [{key}] for uid={uid_int} restarted")

    
    def remove_filter(self, uid: int, key: str) -> None:
        thread = self.active_threads.get(uid)
        if thread:
            thread.remove_filter(key=key)
            print(f"Thread [{key}] for uid={uid} removed!")

            if not thread.data_search:
                thread.stop()
                del self.active_threads[uid]

                print(f"Thread [{key}] for uid={uid} stopped!")
    

    def get_active_filters(self, uid: int) -> list:
        thread = self.active_threads.get(uid)
        if thread:
            return thread.data_attempts
        
        return []

    
    def update_filter(self, uid: int, new_filter: dict) -> None:
        thread = self.active_threads.get(uid)
        if thread:
            thread.update_filter(new_filter=new_filter)


def fetch_address_from_page(soup):
    row = soup.find('td', class_='ads_contacts_name', string="Address:")
    cell = row.find_next_sibling('td') if row else None
    tag = cell.find('a', class_='a9a') if cell else None
    return (tag or cell).get_text(strip=True) if (tag or cell) else None


def fetch_place(soup):
    row = soup.find('td', string=lambda t: t and "Place:" in t)
    cell = row.find_next('td', class_='ads_contacts') if row else None
    return cell.get_text(strip=True) if cell else None


async def generate_message(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            if not html:
                return {"success": False, "message": "empty html"}

    soup = bs(html, "lxml")
    if not soup:
        return {"success": False, "message": "parse error"}

    location, place = (fetch_address_from_page(soup), fetch_place(soup))
    big_photo_src = (soup.select_one("div.pic_dv_thumbnail a") or {}).get("href")
    
    selectors = {
        "model": ("tdo_31", "🚙 <b>{}</b>"),
        "price": ("tdo_8", "<b>Price:</b> {}"),
        "year": ("tdo_18", "<b>Year:</b> {}"),
        "engine_type": ("tdo_15", "<b>Engine type:</b> {}"),
        "gearbox": ("tdo_35", "<b>Gearbox:</b> {}"),
        "mileage": ("tdo_16", "<b>Mileage:</b> {}"),
        "checkup": ("tdo_223", "<b>Checkup:</b> {}"),
    }

    parts = []
    find = soup.find

    for key, (id_, template) in selectors.items():
        el = find(id=id_)
        if el:
            txt = el.get_text(strip=True)
            parts.append(template.format(txt))

    if not big_photo_src or not parts:
        return {"success": False, "error": "big_photo_src or data missing"}

    if location:
        parts.append(f"<b>Address:</b> {location}")
    if place:
        parts.append(f"<b>Place:</b> {place}")

    parts.append(f"<a href='{url}'>Go to webpage</a>")

    return {
        "success": True,
        "image": big_photo_src,
        "message": "\n".join(parts)
    }


thread_manager = ThreadManager()


# async def test():
#     print(await generate_message(url="https://www.ss.com/msg/en/transport/cars/bmw/118/ccocjg.html"))


# asyncio.run(test())


# def main():
#     search_thread = SearchThread()
#     search_thread.start()

#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         search_thread.stop()
#         search_thread.join()


# if __name__ == "__main__":
#     main()