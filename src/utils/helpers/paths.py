from pathlib import Path


class PathHelper:
    @staticmethod
    def get_root():
        return Path(__file__).parent.parent.parent.parent
