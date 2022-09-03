""" fetch.py
Downloads the bikeshare datasets from open data Toronto
If invoked from terminal, takes in year and output_path as parameters
"""

import argparse
import logging
import time
from pathlib import Path

import requests

# Toronto Open Data is stored in a CKAN instance. It's APIs are documented here:
# https://docs.ckan.org/en/latest/api/

# To hit our API, you'll be making requests to:
BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/"
# Datasets are called "packages". Each package can contain many "resources"
# To retrieve the metadata for this package and its resources, use the package name in this page's URL:

# example of link to download:
# https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/7e876c24-177c-4605-9cef-e50dd74c617f/resource/98b63ba7-24ba-41da-a788-1c28d21a39d1/download/bikeshare-ridership-2017.zip
# {BASE_CKAN_URL}/dataset/<package_id>/resource/<resource_id>/download/<file_name.type>


def get_package_metadata(
    api_url: str = "package_show", pkg_id: str = "bike-share-toronto-ridership-data"
):

    params = {"id": pkg_id}
    package = requests.get(BASE_URL + api_url, params=params, timeout=5).json()
    return package


# with open('pkg_list.json', 'w') as f_out:
#     json.dump(package, f_out)
def parse_years(years: str) -> set:
    years_list = years.split(",")
    # raise ValueError if non-year values are given
    years_list = [year for year in years_list if year.isnumeric()]

    return set(years_list)


def make_path(output_path: Path) -> bool:
    if not output_path.exists:
        Path.mkdir(output_path, exist_ok=True, parents=True)
        return True
    else:
        return False


def is_year_present(name: list, years) -> bool:
    """regex to match year: 20[0-9]{2}($|-)"""
    present = [part in years for part in name]
    return any(present)


def run(years, output_path):
    years = parse_years(years)
    made_path = make_path(output_path)
    package = get_package_metadata()
    # To get resource data:
    for idx, resource in enumerate(package["result"]["resources"]):

        # To download the first non datastore_active resource :
        name_split = resource["name"].split("-")
        if not resource["datastore_active"] and is_year_present(name_split, years):
            res_url = resource["url"]
            with requests.get(res_url, stream=True, timeout=5) as resource_dump_data:
                resource_dump_data.raise_for_status()
                # how to convert dump_data to .zip?
                fname = f"""{resource['name']}.{resource['format'].lower()}"""
                file_path = Path(output_path / fname)
                if not file_path.exists():
                    logging.info(f"Requesting from {res_url}")
                    with open(file_path, "wb") as file:
                        logging.info(f"Writing to {file_path}")
                        for chunk in resource_dump_data.iter_content(
                            chunk_size=512 * 1024
                        ):
                            file.write(chunk)
                else:
                    logging.warn(f"Already exists: {file_path}")
            # to not hammer the server with quests too quickly
            time.sleep(1)
            # resource_urls.append(res_url)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year",
        type=str,
        help="""Year for which the bikeshare data will be requested. 
        If multiple years are required, separate by comma.""",
    )
    parser.add_argument(
        "--output_path",
        type=Path,
        help="The location where the resulting file will be saved.",
    )
    args = parser.parse_args()

    run(args.year, args.output_path)
