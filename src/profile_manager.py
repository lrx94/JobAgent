import json
from pathlib import Path


PROFILE_DIR = Path("profiles")


class ProfileManager:

    def list_profiles(self):

        profiles = []

        for folder in PROFILE_DIR.iterdir():

            if folder.is_dir():

                config = folder / "config.json"

                if config.exists():

                    with open(config, encoding="utf-8") as f:

                        data = json.load(f)

                    profiles.append(data)

        return profiles