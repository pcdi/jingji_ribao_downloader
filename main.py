import asyncio
from datetime import date
from io import BytesIO
from urllib.parse import urljoin

import PyPDF2 as PyPDF2
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm


class JingjiRibaoEdition:
    edition_date = date.today()
    # edition_date = date(2021, 5, 15)
    edition_url = (
        "http://paper.ce.cn/pc/layout/"
        + edition_date.strftime("%Y%m/%d/")
        + "node_01.html"
    )
    edition_frontpage_html = BeautifulSoup
    edition_pdfs = []
    session = ClientSession

    def __init__(self):
        print(self.edition_url)

    async def get_edition_html(self):
        self.session = ClientSession(raise_for_status=True)
        print(f"Getting 经济日报 for {edition.edition_date}")
        async with self.session as session:
            try:
                async with session.get(self.edition_url) as response:
                    assert response.status == 200
                    response = await response.read()
                    self.edition_frontpage_html = BeautifulSoup(response, "html.parser")
                await self.get_edition_pdf_links()
            except aiohttp.ClientResponseError:
                raise

    async def get_edition_pdf_links(self):
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
        await self.get_edition_pdfs()

    async def get_edition_pdfs(self):
        async for edition_page_link in tqdm(self.edition_pdfs):
            try:
                async with self.session.get(
                    urljoin(self.edition_url, edition_page_link["page_link"])
                ) as response:
                    assert response.status == 200
                    response = await response.read()
                    edition_page_link["pdf"] = response

            except aiohttp.ClientResponseError:
                print("PDF could not be found.")
                return
        await self.merge_page_pdfs()

    async def merge_page_pdfs(self):
        print(f"Merging PDFs.")
        merger = PyPDF2.PdfMerger()
        for page in self.edition_pdfs:
            pdf = BytesIO(page["pdf"])
            bookmark = page["page_title"]
            merger.append(fileobj=pdf, outline_item=bookmark)
        merger.write(f"{self.edition_date}.pdf")
        merger.close()
        print("Done.")


if __name__ == "__main__":
    edition = JingjiRibaoEdition()
    with asyncio.Runner(debug=True) as runner:
        runner.run(edition.get_edition_html())
