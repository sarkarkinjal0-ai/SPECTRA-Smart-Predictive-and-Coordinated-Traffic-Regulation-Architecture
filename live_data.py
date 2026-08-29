import json
import os


DATA_FILE = r"C:\SPECTRA\Simulation\dashboard_live.json"


def get_dashboard_data():

    if not os.path.exists(DATA_FILE):
        return None

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        data["_data_file"] = DATA_FILE

        return data

    except (
        json.JSONDecodeError,
        OSError
    ):
        return None
