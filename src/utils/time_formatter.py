from datetime import datetime


class TimeFormatter:
    @staticmethod
    def get_current_unix() -> int:
        return int(datetime.now().timestamp() * 1000)
