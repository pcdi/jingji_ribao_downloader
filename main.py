import asyncio
from io import BytesIO

import PyPDF2 as PyPDF2
from aiohttp import ClientSession
from datetime import date
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from tqdm.asyncio import trange, tqdm


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

    async def get_edition_html(self, session):
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
                "page_title": page_pdf_link.get_text().strip().split("：")[1],
                "page_link": page_pdf_link.find("input")["value"],
            }
            self.edition_pdfs.append(edition_page_link)

    async def get_edition_pdfs(self, session):
        for edition_page_link in tqdm(self.edition_pdfs):
            async with session.get(
                urljoin(self.edition_url, edition_page_link["page_link"])
            ) as response:
                try:
                    response = await response.read()
                    edition_page_link["pdf"] = response
                except response.status != 200:
                    raise

    def merge_page_pdfs(self):
        print(f"Merging PDFs.")
        merger = PyPDF2.PdfMerger()
        for page in self.edition_pdfs:
            pdf = BytesIO(page["pdf"])
            bookmark = page["page_title"]
            merger.append(fileobj=pdf, outline_item=bookmark)
        merger.write(f"{self.edition_date}.pdf")
        merger.close()
        print("Done.")


async def get_edition():
    edition = JingjiRibaoEdition()
    print(f"Getting 经济日报 for {edition.edition_date}")
    async with ClientSession() as session:
        await edition.get_edition_html(session)
        edition.get_edition_pdf_links()
        await edition.get_edition_pdfs(session)
        edition.merge_page_pdfs()


if __name__ == "__main__":
    with asyncio.Runner(debug=True) as runner:
        runner.run(get_edition())
