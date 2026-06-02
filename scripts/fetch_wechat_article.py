import argparse
import html
import json
import re
import urllib.request
from pathlib import Path


DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def clean_text(fragment):
    text = re.sub(r"<script\b.*?</script>", "", fragment, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def first_match(pattern, raw, flags=0):
    match = re.search(pattern, raw, flags)
    return html.unescape(match.group(1)).strip() if match else ""


def fetch(url, timeout=25):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DESKTOP_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        status = getattr(resp, "status", None)
        raw = resp.read().decode("utf-8", "ignore")

    title = first_match(r'property="og:title"[^>]*content="([^"]*)"', raw)
    if not title:
        title = first_match(r'id="activity-name"[^>]*>(.*?)</h1>', raw, re.S)
        title = clean_text(title) if title else ""

    account = first_match(r'id="js_name"[^>]*>(.*?)</a>', raw, re.S)
    if account:
        account = clean_text(account)
    author = first_match(r'id="js_author_name"[^>]*>(.*?)</span>', raw, re.S)
    if author:
        author = clean_text(author)

    body = ""
    body_match = re.search(r'id="js_content"[^>]*>(.*?)<script', raw, re.S)
    if body_match:
        body = clean_text(body_match.group(1))

    blocked = (
        "wappoc_appmsgcaptcha" in final_url
        or "verify.qq.com" in raw
        or "完成验证" in raw
        or "环境异常" in raw
    )

    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "bytes": len(raw),
        "blocked_or_captcha": blocked,
        "has_js_content": "js_content" in raw,
        "title": title,
        "account": account,
        "author": author,
        "body_chars": len(body),
        "body": body,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch a public mp.weixin.qq.com article by known URL.")
    parser.add_argument("url")
    parser.add_argument("--out", help="Write JSON result to a file.")
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()

    result = fetch(args.url, timeout=args.timeout)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(args.out)
    else:
        print(payload)


if __name__ == "__main__":
    main()
