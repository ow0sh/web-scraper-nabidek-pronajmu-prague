import html
import logging
from time import monotonic, sleep
from typing import Any
from urllib.parse import quote_plus

import requests

from scrapers.rental_offer import RentalOffer

MAX_TEXT_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
SEND_DELAY_SECONDS = 3.0


class TelegramApiError(RuntimeError):
    pass


class RetriableTelegramApiError(TelegramApiError):
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, request_timeout: float = 30.0) -> None:
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.chat_id = chat_id
        self.request_timeout = request_timeout
        self.send_delay_seconds = SEND_DELAY_SECONDS
        self.status_message_id: int | None = None
        self._last_request_at: float | None = None

    def send_offers(self, offers: list[RentalOffer]) -> None:
        for offer in offers:
            self._send_offer(offer)

    def send_error(self, message: str) -> None:
        self._send_text(self._format_error_text(message), disable_web_page_preview=True)

    def update_status(self, message: str) -> None:
        payload = {
            "chat_id": self.chat_id,
            "text": self._truncate(message),
            "disable_web_page_preview": True,
        }

        if self.status_message_id is None:
            response = self._request("sendMessage", payload)
            self.status_message_id = response["message_id"]
            logging.info("Status message created.")
            return

        try:
            self._request(
                "editMessageText",
                {
                    **payload,
                    "message_id": self.status_message_id,
                },
            )
            logging.info("Status message updated.")
        except TelegramApiError as exc:
            logging.warning("Status message update failed: %s. Creating a new one.", exc)
            response = self._request("sendMessage", payload)
            self.status_message_id = response["message_id"]
            logging.info("Status message recreated.")

    def _send_offer(self, offer: RentalOffer) -> None:
        text = self._format_offer_text(offer)

        if offer.image_url and len(text) <= MAX_CAPTION_LENGTH:
            try:
                self._request(
                    "sendPhoto",
                    {
                        "chat_id": self.chat_id,
                        "photo": offer.image_url,
                        "caption": text,
                        "parse_mode": "HTML",
                    },
                )
                logging.info("Offer sent with photo: %s", offer.link)
                return
            except TelegramApiError as exc:
                logging.warning(
                    "Photo send failed for %s: %s. Falling back to text message.",
                    offer.link,
                    exc,
                )

        self._send_text(text)
        logging.info("Offer sent as text: %s", offer.link)

    def _send_text(self, text: str, disable_web_page_preview: bool = False) -> dict[str, Any]:
        return self._request(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": self._truncate(text),
                "parse_mode": "HTML",
                "disable_web_page_preview": disable_web_page_preview,
            },
        )

    def _request(self, method: str, payload: dict[str, Any], delay_seconds: float = 5.0) -> dict[str, Any]:
        current_delay = delay_seconds
        while True:
            try:
                self._wait_for_send_slot()
                return self._request_once(method, payload)
            except RetriableTelegramApiError as exc:
                retry_delay = max(current_delay, exc.retry_after or 0.0)
                logging.warning(
                    "Telegram API retry for %s: %s. Retrying in %.1fs.",
                    method,
                    exc,
                    retry_delay,
                )
                sleep(retry_delay)
                current_delay = min(retry_delay * 2, 60.0)

    def _request_once(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.api_url}/{method}",
                data=payload,
                timeout=self.request_timeout,
            )
        except requests.RequestException as exc:
            self._last_request_at = monotonic()
            raise RetriableTelegramApiError(str(exc)) from exc

        self._last_request_at = monotonic()

        data = self._parse_response(response)
        description = self._describe_error(data, response)

        if description == "Bad Request: message is not modified":
            return {}

        if response.status_code == 429:
            retry_after = data.get("parameters", {}).get("retry_after")
            retry_after_seconds = None
            if retry_after is not None:
                try:
                    retry_after_seconds = float(retry_after)
                except (TypeError, ValueError):
                    retry_after_seconds = None
            retry_hint = f" Retry after {retry_after}s." if retry_after else ""
            raise RetriableTelegramApiError(
                f"Rate limited by Telegram.{retry_hint}",
                retry_after=retry_after_seconds,
            )

        if response.status_code >= 500:
            raise RetriableTelegramApiError(self._describe_error(data, response))

        if response.status_code >= 400:
            raise TelegramApiError(description)

        if not data.get("ok", False):
            error_code = data.get("error_code")
            if error_code == 429 or isinstance(error_code, int) and error_code >= 500:
                raise RetriableTelegramApiError(description)

            raise TelegramApiError(description)

        return data["result"]

    def _wait_for_send_slot(self) -> None:
        if self._last_request_at is None:
            return

        remaining_delay = self.send_delay_seconds - (monotonic() - self._last_request_at)
        if remaining_delay > 0:
            sleep(remaining_delay)

    @staticmethod
    def _parse_response(response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {"description": response.text[:500]}

    @staticmethod
    def _describe_error(data: dict[str, Any], response: requests.Response) -> str:
        return data.get("description") or response.text[:500] or f"HTTP {response.status_code}"

    @staticmethod
    def _format_offer_text(offer: RentalOffer) -> str:
        lines = [
            f"<b>{html.escape(offer.scraper.name)}</b>",
            f"<b>{html.escape(offer.title)}</b>",
        ]

        if offer.location:
            maps_url = TelegramNotifier._format_google_maps_url(offer.location)
            lines.append(
                f'Lokalita: <a href="{html.escape(maps_url, quote=True)}">{html.escape(offer.location)}</a>'
            )

        lines.append(f"Cena: {html.escape(TelegramNotifier._format_price(offer.price))}")
        lines.append(f'<a href="{html.escape(offer.link, quote=True)}">Otevrit nabidku</a>')
        return "\n".join(lines)

    @staticmethod
    def _format_google_maps_url(location: str) -> str:
        return f"https://maps.google.com/?q={quote_plus(location)}"

    @staticmethod
    def _format_error_text(message: str) -> str:
        escaped_message = html.escape(message)
        return f"<b>Chyba aplikace</b>\n<pre>{TelegramNotifier._truncate(escaped_message, 3500)}</pre>"

    @staticmethod
    def _format_price(price: int | str) -> str:
        price_text = str(price).strip()
        if not price_text:
            return "Neuvedena"

        if "Kč" in price_text:
            return price_text

        return f"{price_text} Kč"

    @staticmethod
    def _truncate(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
        if len(text) <= max_length:
            return text

        return text[: max_length - 1] + "…"
