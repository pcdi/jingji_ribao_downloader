import asyncio
import datetime
from datetime import date
from io import BytesIO
from urllib.parse import urljoin

import PyPDF2 as PyPDF2
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup


class JingjiRibaoEdition:
    edition_date = datetime.date
    edition_url = str
    edition_frontpage_html = BeautifulSoup
    edition_pdfs = list

    def __init__(self, edition_date=date.today()):
        self.session = None
        self.edition_date = edition_date
        self.edition_url = (
            "http://paper.ce.cn/pc/layout/"
            + self.edition_date.strftime("%Y%m/%d/")
            + "node_01.html"
        )
        self.edition_pdfs = []
        self.output_dir = 'out/'

    async def get_edition_html(self):
        self.session = ClientSession(raise_for_status=True)
        print(f"Getting 经济日报 for {self.edition_date.isoformat()}")
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
        for edition_page_link in self.edition_pdfs:
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
        await self.merge_and_write_page_pdfs()

    async def merge_and_write_page_pdfs(self):
        print(f"Merging PDFs for {self.edition_date.isoformat()}.")
        with PyPDF2.PdfMerger() as merger:
            for page in self.edition_pdfs:
                pdf = BytesIO(page["pdf"])
                bookmark = page["page_title"]
                with PyPDF2.PdfWriter() as writer:
                    writer.append(fileobj=pdf, outline_item=bookmark)
                    writer.write(
                        f"{self.output_dir}{self.edition_date.isoformat()}_{str(page['page_number'])}.pdf"
                    )
                    merger.append(fileobj=pdf, outline_item=bookmark)
            merger.write(f"{self.output_dir}{self.edition_date.isoformat()}.pdf")
        print(f"Done with {self.edition_date.isoformat()}.")


async def main(start_date, end_date):
    assert start_date <= end_date
    async with asyncio.TaskGroup() as tg:
        for edition_date in [
            start_date + datetime.timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]:
            edition = JingjiRibaoEdition(edition_date=edition_date)
            tg.create_task(edition.get_edition_html())


if __name__ == "__main__":
    start_date = date(2023, 7, 20)
    end_date = date(2023, 7, 22)
    with asyncio.Runner(
        # debug=True
    ) as runner:
        runner.run(main(start_date, end_date))
