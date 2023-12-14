from bs4 import BeautifulSoup
import pandas as pd
import requests
from typing import List
import json
from json_to_pd import normalize_data, create_dataframe


class RealEstateScrapper:
    def __init__(self, base_url: str):
        """
        Initialize the scrapper with the base url

        Parameters
        ----------
        base_url : str

        Returns
        -------
        None
        """
        self.base_url = base_url

    def paginate_urls(self, num_pages: int) -> List[str]:
        """
        Returns a list of urls to scrape based on the base_url and the number of pages to scrape

        Parameters
        ----------
        base_url : str
            The base url to scrape

        num_pages : int
            The number of pages to scrape

        Returns
        -------
        urls : List[str]
            A list of urls to scrape
        """

        urls = []
        urls.append(self.base_url)
        for i in range(2, num_pages + 1):
            urls.append(self.base_url + f"&pag={i}")

        return urls

    def get_individual_ad_main_info(self, url: str, soup: BeautifulSoup) -> dict:
        """
        Returns a dictionary containing the main info of the real estate ad

        Parameters
        ----------
        url : str
            The url to scrape

        soup : BeautifulSoup
            The BeautifulSoup object containing the html of the page to scrape

        Returns
        -------
        ad_main_info : dict
            A dictionary containing the main info of the real estate ad
        """
        try:
            ad_main_info = dict()

            ad_main_info["title"] = (
                soup.find("div", "in-titleBlock__content")
                .find("h1", "in-titleBlock__title")
                .text.strip()
            )
            ad_main_info["url"] = url

            raw_ad_main_info = soup.find(
                "ul",
                attrs="nd-list nd-list--pipe in-feat in-feat--full in-feat__mainProperty in-landingDetail__mainFeatures",
            ).find_all("li")

            for li in raw_ad_main_info:
                if "€" in li.text:
                    ad_main_info["price"] = li.text.strip()
                elif "locali" in li["aria-label"] or "locale" in li["aria-label"]:
                    ad_main_info["rooms"] = li.text.strip()
                elif "m²" in li.text:
                    ad_main_info["area"] = li.text.strip().replace("da", "")
                elif "piano" in li.text:
                    ad_main_info["floor"] = li.text.strip()
                elif "bagni" in li.text:
                    ad_main_info["bathrooms"] = li.text.strip()
                elif "classe" in li.text:
                    ad_main_info["energy_class"] = li.text.strip()
                elif "anno" in li.text:
                    ad_main_info["year"] = li.text.strip()
                elif "stato" in li.text:
                    ad_main_info["state"] = li.text.strip()
                elif "tipologie" in li["aria-label"]:
                    ad_main_info["type"] = li.text.strip()
                else:
                    ad_main_info["other_info"] = (
                        li.text.strip() + " " + li["aria-label"]
                    )

            return ad_main_info

        except:
            raise Exception("The page main info scrapping failed")

    def get_individual_ad_description(self, soup: BeautifulSoup) -> dict:
        """
        Returns a dictionary containing the description of the real estate ad

        Parameters
        ----------
        soup : BeautifulSoup
            The BeautifulSoup object containing the html of the page to scrape

        Returns
        -------
        description_info : dict
            A dictionary containing the description section information of the real estate ad
        """
        try:
            description_info = dict()
            description_info["title"] = soup.find(
                "p", "in-description__title"
            ).text.strip()
            description_info["content"] = soup.find("div", "in-readAll").text.strip()

            return description_info

        except:
            raise Exception("The page description scrapping failed")

    def get_individual_ad_table_info(self, soup: BeautifulSoup) -> dict:
        """
        Returns a dictionary containing the table information of the real estate ad

        Parameters
        ----------
        soup : BeautifulSoup
            The BeautifulSoup object containing the html of the page to scrape

        Returns
        -------
        additional_info : dict
            A dictionary containing the table information of the real estate ad
        """
        try:
            additional_info = dict()

            table_titles = soup.find_all("div", "in-sectionTitle__container")
            raw_tables = soup.find_all("dl", "in-realEstateFeatures__list")

            for table_title, raw_table in zip(table_titles, raw_tables):
                table_info = dict()

                left_column_content = raw_table.find_all("dt")
                right_column_content = raw_table.find_all("dd")

                for dt, dd in zip(left_column_content, right_column_content):
                    if dt.text.strip() == "altre caratteristiche":
                        characteristics = dd.find_all("div")
                        table_info[dt.text.strip()] = [
                            characteristic.text.strip()
                            for characteristic in characteristics
                        ]
                    else:
                        table_info[dt.text.strip()] = dd.text.strip()

                additional_info[table_title.text.strip().lower()] = table_info

            return additional_info
        except Exception as e:
            raise Exception(f"The page table scrapping failed. " + str(e))

    def individual_ad_scrapper(self, urls: List[str]) -> List[dict]:
        """
        Returns a list of dictionaries containing the scraped data

        Parameters
        ----------
        urls : List[str]
            A list of urls to scrape

        Returns
        -------
        pages_content : List[dict]
            A list of dictionaries containing the scraped data
        """
        pages_content = []

        try:
            for url in urls:
                try:
                    page_request = requests.get(url)
                except:
                    print(f"Error on the request to {url}")
                    pass

                # Extract the response as html: html_doc
                html_doc = page_request.text

                # Initialize the scrapper
                soup = BeautifulSoup(html_doc, "lxml")

                try:
                    single_page_content = dict()

                    ad_main_info = self.get_individual_ad_main_info(url=url, soup=soup)
                    ad_description = self.get_individual_ad_description(soup=soup)
                    ad_table_info = self.get_individual_ad_table_info(soup=soup)

                    single_page_content["details"] = ad_main_info
                    single_page_content["description"] = ad_description
                    # single_page_content["additional_info"] = ad_table_info
                    for key, value in ad_table_info.items():
                        single_page_content[key] = value

                    pages_content.append(single_page_content)

                except:
                    raise Exception("The page main info scrapping failed")

            return pages_content

        except Exception as e:
            requests.exceptions.RequestException(
                f"The request to {url} failed." + str(e)
            )

    def main_scrapper(self):
        """
        Returns a dataframe containing the scraped data

        Parameters
        ----------
        None

        Returns
        -------
        entire_ad_info_dict : List[dict]
            A list of dictionaries containing the scraped data

        """
        urls_to_scrape = self.paginate_urls(num_pages=5)
        entire_ad_info_dict = []

        for i, url in enumerate(urls_to_scrape):
            print(f"Scraping page {i+1}")
            try:
                page_request = requests.get(url)
                if page_request.status_code != 200:
                    raise Exception("The request failed")

                # Extract the response as html: html_doc
                html_doc = page_request.text

                # Initialize the scrapper
                soup = BeautifulSoup(html_doc, "lxml")
                individual_ad_urls: List[str] = []

                try:
                    info_divs = soup.find_all("div", attrs="nd-mediaObject__content")

                    for div in info_divs:
                        individual_ad_urls.append(div.find("a").get("href"))

                    if len(individual_ad_urls) == 0:
                        raise Exception("No urls found")

                    # Pass the url to the specific ad scrapper
                    individual_details = self.individual_ad_scrapper(individual_ad_urls)
                    if individual_details != None:
                        entire_ad_info_dict.append(individual_details)

                except Exception as e:
                    print(f"Exception: {e}")
                    raise Exception("The page urls scrapping failed")

            except:
                requests.exceptions.RequestException(f"The request to {url} failed")

        return entire_ad_info_dict


sell_scrapper = RealEstateScrapper(
    "https://www.immobiliare.it/vendita-case/bologna/?criterio=rilevanza"
)
sell_results = sell_scrapper.main_scrapper()

with open("selling-bologna.json", "w") as f:
    json.dump(sell_results, f)

with open("selling-bologna.csv") as f:
    df = create_dataframe(normalize_data(sell_results))
    df.to_csv(f)


rent_scrapper = RealEstateScrapper(
    "https://www.immobiliare.it/affitto-case/emilia-romagna/?criterio=rilevanza"
)
rent_results = rent_scrapper.main_scrapper()

with open("renting.json", "w") as f:
    json.dump(rent_results, f)

with open("renting.csv") as f:
    df = create_dataframe(normalize_data(rent_results))
    df.to_csv(f)


print("Done")
