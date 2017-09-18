### ytb_jump_async_dl

Download youtube video with subtitle. You can refer the repository named **ytb_jump_dl** that is not work directly now but you can download the video in browser through the extracted download url by **ytb_jump_dl**.

#### My environments

* OS X EI Capitan 10.11.6
* python 3.6.1
* [aiohttp 2.2.5](http://aiohttp.readthedocs.io/en/stable/)
* [parsel 1.2.0](https://github.com/scrapy/parsel)
* [tqdm 4.15.0](https://github.com/tqdm/tqdm)

**notes:** test in non-locking area, it means I don't use proxy.

### Man page

```bash
Usage: video_dl path url
Args: path -> video and subtitle saved path, default: /tmp
Args: url  -> url of video
```

### Run

```bash
$ python video_dl.py /Users/xxx/Downloads https://www.youtube.com...
```

subtitle_dl.py can run alone.

There is some useless function in utils.py that copyed from **ytb_jump_dl** repository.