import aiohttp
import asyncio
import async_timeout
from parsel import Selector
from tqdm import tqdm
from utils import gen_encode_url


async def subtitle(ytb_url='', file_path=''):
    domain = 'http://downsub.com/'
    s_url = gen_encode_url(ytb_url, domain)
    async with aiohttp.ClientSession() as session:
        try:
            with async_timeout.timeout(5):
                async with session.get(s_url) as res:
                    text = await res.text()
        except asyncio.TimeoutError:
            print('timeout.....')
            # exit(1)
        else:
            selector = Selector(text=text)
            abs_url = selector.xpath(
                "//div[@id='show']/b[1]/a/@href"
            ).extract()[0]
            download_url = domain + abs_url[2:]
            title = selector.xpath(
                "//span[@class='media-heading']/text()"
            ).extract()[0]
            print(f'Real download url: {download_url}')

            try:
                with async_timeout.timeout(5):
                    async with session.get(download_url) as res:
                        length = res.content_length
                        with open(
                                '{}/{}.srt'.format(file_path, title),
                                'wb') as srt:
                            with tqdm(
                                    total=length,
                                    ncols=100,
                                    # desc='Subtitle',
                                    unit_scale=True,
                                    bar_format='  {l_bar}{bar}| {n_fmt}/{total_fmt} '
                                               '[Remaining: {remaining}, {rate_fmt}]'
                            ) as bar:
                                while True:
                                    chunk = await res.content.read(4096)
                                    if not chunk:
                                        break
                                    srt.write(chunk)
                                    bar.update(len(chunk))
            except asyncio.TimeoutError:
                print('Download file timeout...')


if __name__ == '__main__':
    # 待下载ytb的url
    url = 'https://www.youtube.com/watch?v=Ttw816mwnQY'
    filepath = '/Users/zhangyue/Downloads'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(subtitle(url, filepath))
    loop.close()

