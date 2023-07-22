import asyncio
from aiohttp import ClientSession
from datetime import date
from bs4 import BeautifulSoup


class JingjiRibaoEdition:
    edition_date = date.today()
    edition_url = "http://paper.ce.cn/pc/layout/" + edition_date.strftime("%Y%m/%d")
    edition_frontpage_html = BeautifulSoup
    edition_pdfs = dict

    def __init__(self):
        print(self.edition_url)

    async def get_edition_html(self):
        async with ClientSession() as session:
            async with session.get(self.edition_url) as response:
                try:
                    response = await response.read()
                    self.edition_frontpage_html = BeautifulSoup(response, "html.parser")
                    print(self.edition_frontpage_html.prettify())
                except response.status != 200:
                    raise


async def get_edition():
    edition = JingjiRibaoEdition()
    print(f'Getting 经济日报 for {edition.edition_date}')
    await edition.get_edition_html()


if __name__ == "__main__":
    with asyncio.Runner(debug=True) as runner:
        runner.run(get_edition())
