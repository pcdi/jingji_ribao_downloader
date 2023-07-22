import asyncio
from aiohttp import ClientSession
from datetime import date
from bs4 import BeautifulSoup
import re


class JingjiRibaoEdition:
    edition_date = date.today()
    edition_url = (
        "http://paper.ce.cn/pc/layout/"
        + edition_date.strftime("%Y%m/%d/")
        + "node_01.html"
    )
    edition_frontpage_html = BeautifulSoup
    edition_pdfs = []

    def __init__(self):
        print(self.edition_url)

    async def get_edition_html(self):
        async with ClientSession() as session:
            async with session.get(self.edition_url) as response:
                try:
                    response = await response.read()
                    self.edition_frontpage_html = BeautifulSoup(response, "html.parser")
                    # print(self.edition_frontpage_html.prettify())
                except response.status != 200:
                    raise

    def get_edition_pdf_links(self):
        page_pdf_links = self.edition_frontpage_html.find_all(
            "li", class_="posRelative"
        )
        for page_pdf_link in page_pdf_links:
            edition_page_link = {
                "page_number": int(
                    page_pdf_link.get_text()
                    .strip()
                    .split("：")[0]
                    .removeprefix("第")
                    .removesuffix("版")
                ),
                "page_link": page_pdf_link.find("input")["value"],
            }
            self.edition_pdfs.append(edition_page_link)


async def get_edition():
    edition = JingjiRibaoEdition()
    print(f"Getting 经济日报 for {edition.edition_date}")
    await edition.get_edition_html()
    edition.get_edition_pdf_links()


if __name__ == "__main__":
    with asyncio.Runner(debug=True) as runner:
        runner.run(get_edition())
