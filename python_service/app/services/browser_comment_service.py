"""Playwright-based browser fallback for Bilibili comments."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from app.config import settings
from app.utils.logger import logger

try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover - optional dependency at runtime
    async_playwright = None


class BrowserCommentService:
    """Use a real browser context to fetch comments with full cookies."""

    def __init__(self, cookie_dict: Optional[Dict[str, str]] = None):
        self.cookie_dict = cookie_dict or {}

    @staticmethod
    def is_available() -> bool:
        return settings.browser_fallback_enabled and async_playwright is not None

    def _build_cookies(self) -> List[Dict]:
        cookies: List[Dict] = []
        for name, value in self.cookie_dict.items():
            if not value:
                continue
            cookies.append({
                "name": str(name),
                "value": str(value),
                "domain": ".bilibili.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            })
        return cookies

    @staticmethod
    def _normalize_reply(reply: Dict) -> Dict:
        member = reply.get("member") or {}
        content = reply.get("content") or {}
        return {
            "author": member.get("uname", "未知用户"),
            "gender": member.get("sex", "未知"),
            "content": content.get("message", ""),
            "like": int(reply.get("like", 0) or 0),
            "reply_id": reply.get("rpid"),
            "create_time": reply.get("ctime", 0),
        }

    async def fetch_comments(self, bvid: str, aid: int, max_count: int = 200) -> List[Dict]:
        if not self.is_available():
            raise RuntimeError("Playwright 未安装或已禁用")

        all_comments: List[Dict] = []
        page_index = 1

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.browser_headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
                viewport={"width": 1440, "height": 900},
            )
            cookies = self._build_cookies()
            if cookies:
                await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://www.bilibili.com/video/{bvid}", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1200)

            while len(all_comments) < max_count:
                payload = await page.evaluate(
                    """
                    async ({ aid, pageIndex }) => {
                      const url = new URL("https://api.bilibili.com/x/v2/reply");
                      url.searchParams.set("oid", String(aid));
                      url.searchParams.set("type", "1");
                      url.searchParams.set("pn", String(pageIndex));
                      url.searchParams.set("sort", "0");
                      const resp = await fetch(url.toString(), { credentials: "include" });
                      return { status: resp.status, text: await resp.text() };
                    }
                    """,
                    {"aid": aid, "pageIndex": page_index}
                )

                status = int(payload.get("status") or 0)
                body_text = payload.get("text") or ""
                if status == 412:
                    raise RuntimeError("Playwright 浏览器态评论抓取仍触发 412 风控")
                if status >= 400:
                    raise RuntimeError(f"Playwright 评论抓取失败，HTTP {status}")

                data = json.loads(body_text)
                if data.get("code") not in (0, None):
                    raise RuntimeError(
                        f"Playwright 评论抓取失败: code={data.get('code')} message={data.get('message')}"
                    )

                replies = ((data.get("data") or {}).get("replies")) or []
                if not replies:
                    break

                for reply in replies:
                    normalized = self._normalize_reply(reply)
                    if normalized["content"]:
                        all_comments.append(normalized)
                    if len(all_comments) >= max_count:
                        break

                if len(replies) < 20:
                    break

                page_index += 1
                await page.wait_for_timeout(900)

            await context.close()
            await browser.close()

        logger.info("Playwright 浏览器态评论抓取完成 - 共获取 %s 条评论", len(all_comments))
        return all_comments

