import logging

from telegram_notifier import TelegramNotifier


class TelegramLogHandler(logging.Handler):
    def __init__(self, notifier: TelegramNotifier, level: int) -> None:
        super().__init__(level)
        self.notifier = notifier

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = f"{record.levelname}\n{record.getMessage()}"
            self.notifier.send_error(message)
        except Exception:
            self.handleError(record)
