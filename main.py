# -- coding: utf-8 --
import time
import re
import tomd
import json
import os
import requests
from msedge.selenium_tools import Edge, EdgeOptions


def get_elements(url, clazz):
    driver.get(url)
    time.sleep(2)
    elements = driver.find_elements_by_class_name(clazz)
    return elements


def get_element(url, element_id):
    driver.get(url)
    time.sleep(2)
    return driver.find_element_by_id(element_id)


def convert(regex: str, new: str, src: str):
    return re.sub(regex, new, src, 0, re.MULTILINE)


def format_md(s: str):
    regex = r"\[<"
    t = convert(regex, r"![<", s)
    regex = r"(<pre>)|(</pre>)"
    t = convert(regex, "\n```\n", t)
    regex = r"<li>"
    t = convert(regex, "1. ", t)
    regex = r"</li>"
    t = convert(regex, "", t)
    return t


def generate_md(articles: list):
    for article in articles:
        print(f"\033[32m[+] Getting: {article}\033[0m")
        driver.get(article)
        time.sleep(1)
        source = driver.page_source
        title = driver.title
        title = title[:title.rfind("-")]
        title = title.replace("|", "")
        title = title.replace("*", "")
        title = title.strip()
        pattern = "(?s)<div id=\"topic_content\" class=\"topic-content markdown-body\">(.*)<div class=\"post-user-action\" style=\"margin-top: 34px;\">"
        pattern = re.compile(pattern)
        match = pattern.findall(source)
        content = match[0]
        content = re.findall(r'(?s)(.*)</div>', content)[0]
        if isinstance(content, str):
            content = content.strip()
        file_name = output_dir + "/" + title + ".md"
        md = tomd.convert(content)
        md = format_md(md)
        md = replace_link(md, title)
        f = open(file_name, "w", encoding="utf-8")
        f.write(md)
        print("\n\033[32m[*] Done\033[0m")
        f.close()


def replace_link(src: str, title: str):
    regex = r"<img src=\"(.*)\">"
    img_links = re.findall(regex, src, re.MULTILINE)
    base_dir = title + ".assets"
    dir_name = output_dir + "/" + base_dir
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    count = 0
    total = len(img_links)
    headers = {
        "User-Agent": r'''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36''',
        "Referer": "https://xz.aliyun.com/"
    }
    for link in img_links:
        print(f"\r\t\033[33m[+] Downloading images ...{count + 1}/{total}\033[0m", end="")
        r = requests.get(url=link, headers=headers)
        time.sleep(0.5)
        basename = f"image-{count}.png"
        f = open(f"{dir_name}/{basename}", "wb")
        f.write(r.content)
        f.close()
        re_link = convert(r"\.", "\\.", link)
        ref = r'<img src=\"' + re_link + r'\">'
        src = convert(ref, f"image-{count}", src)
        src = convert(re_link, f"{base_dir}/{basename}", src)
        count += 1
    return src


if __name__ == '__main__':
    config = json.loads(open("config.json", "r").read())
    options = EdgeOptions()
    options.use_chromium = True
    options.add_argument("blink-settings=imagesEnabled=false")
    options.add_argument("--lang=zh-CN")
    options.binary_location = config["location"]

    driver = Edge(options=options, executable_path="msedgedriver.exe")

    start = config['start']
    end = config['end']
    base_url = 'https://xz.aliyun.com/?page={}'
    output_dir = "output" if config['output'] == "" else config['output']

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    while start <= end:
        u = base_url.format(start)
        links = get_elements(u, "topic-title")
        pages = []
        for i in links:
            pages.append(i.get_attribute("href"))

        generate_md(pages)
        start += 1

    driver.close()
