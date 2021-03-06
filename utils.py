# coding:utf-8
import asyncio
import aiohttp
import aiosocks
import async_timeout
import urllib
import time
from tqdm import tqdm
from parsel import Selector


class VisitException(Exception):
    """website is unavailable"""
    pass


class ExtractException(Exception):
    """can't extract html label"""
    pass


def gen_encode_url(ytb_url='', domain=''):
    param_dict = {
        'url': ytb_url
    }
    param = urllib.parse.urlencode(param_dict)
    url = f'{domain}?{param}'
    return url


def gen_decode_url(name=''):
    name = urllib.parse.unquote(name)
    return name


async def save(length, res, ytb_title, postfix, file_path):
    if postfix == 'srt':
        notice = 'Subtitle'
    elif postfix == 'mp4':
        notice = 'Video'
    else:
        raise Exception('Unsupported file type')
    with open(f'{file_path}/{ytb_title}.{postfix}', 'wb') as srt:
        # time.sleep(0.2)
        asyncio.sleep(0.2)
        print(f'Downloading {notice}: {ytb_title}...')
        with tqdm(
                total=length,
                ncols=100,
                # desc='Subtitle',
                unit_scale=True,
                bar_format='  {l_bar}{bar}| {n_fmt}/{total_fmt} '
                           '[Remaining: {remaining}, {rate_fmt}]'
        ) as bar:
            # while True:
            #     chunk = await res.content.read(4096)
            #     if not chunk:
            #         break
            #     srt.write(chunk)
            #     # asyncio.sleep(0.2)
            #     bar.update(len(chunk))
            async for chunk in res.content.iter_chunked(4096):
                srt.write(chunk)
                bar.update(len(chunk))


async def get_post_args(session):
    """prepare data for http://www.downvids.net
to get video urls in playlist"""
    try:
        # res = session.get(
        #     'http://www.downvids.net/download-youtube-playlist-videos',
        #     timeout=30,
        # )
        with async_timeout.timeout(30):
            async with session.get(
                    'http://www.downvids.net/download-youtube-playlist-videos',
                    proxy='socks5://127.0.0.1:1080'
            ) as res:
                text = await res.text()
    except asyncio.TimeoutError:
        raise VisitException('website is unavailable or unreached(timeout)')

    selector = Selector(text=text)
    payload = {}
    try:
        payload['autoken'] = selector.xpath(
            "//form/input[@name='autoken']/@value"
        ).extract()[0]
        payload['authenticity_token'] = selector.xpath(
            "//form/input[@name='authenticity_token']/@value"
        ).extract()[0]
        payload['playlistok'] = selector.xpath(
            "//form/input[@name='playlistok']/@value"
        ).extract()[0]
        payload['hd'] = '2'  # ignore this. 1:default, 2:480p, 3:720p, 4:1080p
    except:
        raise ExtractException("can't extract html label")

    return payload


async def get_urls_in_playlist(session, playlist_url=''):
    """get each url of videos in playlist"""
    try:
        payload = await get_post_args(session)
        payload['playlist'] = playlist_url
    except:
        raise ExtractException('failed: extract playlist')

    async with session.post(
            "http://www.downvids.net/videoflv.php",
            proxy='socks5://127.0.0.1:1080',
            data=payload,  # todo: 有可能用data=json.dumps(payload)
    ) as res:
        text = await res.text()
        selector = Selector(text=text)
        video_urls = selector.xpath(
            "//span[@class='thumb vcard author']/a/@href"
        ).extract()
        for url in video_urls:
            yield url


async def ytb_download(session, file_path, ytb_url):
    domain = 'http://keepvid.com/'
    v_url = gen_encode_url(ytb_url, domain)
    print(f'Ready to extract, relying on your network, be patient. {v_url}')
    # res = session.get(v_url, timeout=60)
    try:
        with async_timeout.timeout(60):
            async with session.get(
                    v_url, proxy='socks5://127.0.0.1:1080') as res:
                text = await res.text()
    except asyncio.TimeoutError:
        raise VisitException('website is unavailable or unreached(timeout)')

    selector = Selector(text=text)
    pre_dl_list = selector.xpath(
        "//table[@class='result-table']/tbody/tr"
    )
    ytb_title = selector.xpath(
        "//div[@class='row']/div[@class='item-3']/p[1]/text()"
    ).extract()[0]
    for pre in pre_dl_list:
        formats = pre.xpath(
            "td[2]/text()"
        ).extract()[0].lower()
        qualities = pre.xpath(
            "td[@class='al']/text()"
        ).extract()[0].lower()
        if 'mp4' in formats and 'pro' not in qualities and '480' in qualities:
            download_url = pre.xpath(
                "td/a/@href"
            ).extract()[0]
            print(formats, qualities, download_url)

            # get video size for sending to save()

            # res = session.head(download_url, timeout=30)
            try:
                with async_timeout.timeout(10):
                    async with session.head(
                            download_url,
                            proxy='socks5://127.0.0.1:1080') as res:
                        # handle http status code 302
                        r = res.headers.get('location', None)
            except asyncio.TimeoutError:
                raise VisitException(
                    'website is unavailable or unreached(timeout)')
            else:
                if not r:
                    length = int(res.headers.get('content-length', 0))
                    await save(length, res, ytb_title, 'mp4', file_path)
                else:
                    # r = res.headers.get('location')
                    try:
                        with async_timeout.timeout(30):
                            async with session.get(
                                r, proxy='socks5://127.0.0.1:1080'
                            )as res:
                                length = int(
                                    res.headers.get('content-length', 0))

                    # res = session.head(r, timeout=30)
                    # length = int(res.headers.get('content-length', 0))
                    # res = session.get(r, stream=True, timeout=30)
                                await save(length, res, ytb_title,
                                           'mp4', file_path)
                    except asyncio.TimeoutError:
                        raise VisitException(
                            'website is unavailable or unreached(timeout)')

        # you can uncomment below code for
        # downloading subtitle from same website.

        # elif 'srt' in formats:
        #     download_url = pre.xpath(
        #         "td/a/@href"
        #     ).extract()[0]
        #     print(formats, qualities, download_url)
        #     res = session.get(download_url, stream=True, timeout=3)
        #     save(len(res.content), res, ytb_title, 'srt')
        else:
            continue

    # get subtitle from different website
    domain = 'http://downsub.com/'
    s_url = gen_encode_url(ytb_url, domain)
    try:
        with async_timeout.timeout(30):
            async with session.get(
                s_url, proxy='socks5://127.0.0.1:1080'
            ) as res:
                text = res.text()
    except asyncio.TimeoutError:
        raise VisitException(
            'website is unavailable or unreached(timeout)')

    # res = session.get(s_url, timeout=30)
    selector = Selector(text=text)
    abs_url = selector.xpath(
        "//div[@id='show']/b[1]/a/@href"
    ).extract()[0]
    download_url = domain + abs_url[2:]
    print()
    print('srt', 'subtitles', download_url)
    # res = session.get(download_url, stream=True, timeout=30)
    try:
        with async_timeout.timeout(30):
            async with session.get(
                download_url, proxy='socks5://127.0.0.1:1080'
            ) as res:
                await save(len(res.content), res, ytb_title, 'srt', file_path)
    except asyncio.TimeoutError:
        raise VisitException(
            'website is unavailable or unreached(timeout)')

