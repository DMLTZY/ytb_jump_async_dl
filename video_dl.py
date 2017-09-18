import asyncio
import aiohttp
import re
import sys
from utils import gen_decode_url
from subtitle_dl import subtitle
from parsel import Selector
from tqdm import tqdm


async def run(url, file_path):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/60.0.3112.90 Safari/537.36',
        'connection': 'keep-alive',
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get('http://simpleconverter.com/') as res:
            text = await res.text()

        selector = Selector(text=text)
        post_name = selector.xpath(
            "//form/input/@name"
        ).extract()
        post_value = selector.xpath(
            "//form/input/@value"
        ).extract()
        post = dict(zip(post_name, post_value))
        post['video[video]'] = url
        async with session.post(
                'http://simpleconverter.com/find',
                data=post,
        ) as res:
            text = await res.text()

            pattern = re.compile(
                r"<option data-url=\\'(.*?)\\' data-ext=\\'mp4\\'(.*?)<\\/option>")
            matches = pattern.findall(text)
            download_url = ''
            for d_url, quality in matches:
                if '480' in quality and 'MB' in quality:
                    print(f'Real download url: {d_url}')
                    download_url = d_url
                    break
            print()
        if not download_url:
            print('There is no 480p')
            return
        async with session.get(
            download_url
        ) as res:
            pattern = re.compile(r"filename=(.*)")
            matches = pattern.findall(download_url)
            name = gen_decode_url(matches[0])
            name = name.replace('+', ' ')
            with open(f'{file_path}/{name}', 'wb') as srt:
                asyncio.sleep(0.2)
                length = int(res.headers.get('content-length', 0))
                print('Downloading ...')
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
                    # async for chunk in res.content.iter_chunked(4096):
                    #     srt.write(chunk)
                    #     bar.update(len(chunk))


if __name__ == '__main__':
    args_len = len(sys.argv)
    if args_len == 1 or args_len > 3 \
            or 'youtube' not in sys.argv[args_len-1]:
        print('Usage: video_dl path url')
        print('Args: path -> video and subtitle saved path, default: /tmp')
        print('Args: url  -> url of video')
        print('Ex: video_dl /Users/xxx/Downloads http://www.youtube.com...')
        exit(1)
    if args_len == 2:
        file_path = '/tmp'
        url = sys.argv[1]
    else:
        if sys.argv[1][-1] == '/':
            file_path = sys.argv[1][:-1]
        else:
            file_path = sys.argv[1]
        url = sys.argv[2]
    loop = asyncio.get_event_loop()
    task_pairs = asyncio.wait([run(url, file_path), subtitle(url, file_path)])
    loop.run_until_complete(task_pairs)
    loop.close()
    print('Done')



