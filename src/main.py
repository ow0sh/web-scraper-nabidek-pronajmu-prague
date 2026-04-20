#!/usr/bin/env python3
import logging
import re
from datetime import datetime
from time import sleep

from config import config
from offers_storage import OffersStorage
from scrapers.rental_offer import RentalOffer
from scrapers_manager import create_scrapers, fetch_latest_offers
from telegram_logger import TelegramLogHandler
from telegram_notifier import TelegramNotifier


def get_current_daytime() -> bool:
    return datetime.now().hour in range(6, 22)


def get_refresh_interval_minutes() -> int:
    if get_current_daytime():
        return config.refresh_interval_daytime_minutes

    return config.refresh_interval_nighttime_minutes


def extract_offer_price(price: int | str) -> int | None:
    if isinstance(price, int):
        return price

    match = re.search(r"\d[\d\s\xa0]*", str(price))
    if match is None:
        return None

    digits = re.sub(r"\D", "", match.group())
    return int(digits) if digits else None


def offer_matches_price_filter(offer: RentalOffer) -> bool:
    if config.min_price is None and config.max_price is None:
        return True

    offer_price = extract_offer_price(offer.price)
    if offer_price is None:
        return False

    if config.min_price is not None and offer_price < config.min_price:
        return False

    if config.max_price is not None and offer_price > config.max_price:
        return False

    return True


def process_latest_offers(storage: OffersStorage, scrapers, notifier: TelegramNotifier) -> None:
    logging.info("Fetching offers")

    new_offers: list[RentalOffer] = []
    filtered_out_offers = 0
    for offer in fetch_latest_offers(scrapers):
        if not offer_matches_price_filter(offer):
            filtered_out_offers += 1
            continue

        if not storage.contains(offer):
            new_offers.append(offer)

    first_time = storage.first_time
    storage.save_offers(new_offers)

    logging.info("Offers fetched (new: %s, filtered by price: %s)", len(new_offers), filtered_out_offers)

    if not first_time and new_offers:
        notifier.send_offers(new_offers)
    elif first_time:
        logging.info("No previous offers, first fetch is running silently")

    notifier.update_status(datetime.now().strftime("Last update: %Y-%m-%d %H:%M:%S"))


def run() -> None:
    scrapers = create_scrapers(config.dispositions)
    storage = OffersStorage(config.found_offers_file)
    notifier = TelegramNotifier(config.telegram.bot_token, config.telegram.chat_id)
    interval_minutes = get_refresh_interval_minutes()

    if not config.debug:
        logging.getLogger().addHandler(TelegramLogHandler(notifier, logging.ERROR))
    else:
        logging.info("Telegram logger is inactive in debug mode")

    logging.info("Available scrapers: %s", ", ".join(scraper.name for scraper in scrapers))
    logging.info("Fetching latest offers every %s minutes", interval_minutes)

    if config.min_price is not None or config.max_price is not None:
        logging.info("Price filter active (min: %s, max: %s)", config.min_price, config.max_price)

    while True:
        process_latest_offers(storage, scrapers, notifier)

        next_interval_minutes = get_refresh_interval_minutes()
        if next_interval_minutes != interval_minutes:
            interval_minutes = next_interval_minutes
            logging.info("Fetching latest offers every %s minutes", interval_minutes)

        sleep(interval_minutes * 60)

if __name__ == "__main__":
    logging.basicConfig(
        level=(logging.DEBUG if config.debug else logging.INFO),
        format='%(asctime)s - [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug("Running in debug mode")

    run()
