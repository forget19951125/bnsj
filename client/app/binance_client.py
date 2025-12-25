"""
币安客户端（复用原项目代码）
"""
import os
import re
import json
import qrcode
import shutil
from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime
# 延迟导入playwright，只在get_token函数中导入
# from playwright.sync_api import sync_playwright

WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"


def launch_persistent_ctx(pw, reset=False, headless=True, user_id=None, log_callback=None):
    """启动持久化浏览器上下文
    
    Args:
        pw: Playwright实例
        reset: 是否重置浏览器缓存（每次登录都清理）
        headless: 是否无头模式
        user_id: 用户ID，用于多账号支持（不同账号使用不同目录）
    """
    # 获取程序运行目录（client目录）
    current_file = os.path.abspath(__file__)
    # app/binance_client.py -> app -> client
    app_dir = os.path.dirname(current_file)
    client_dir = os.path.dirname(app_dir)
    
    # 根据user_id创建不同的目录，支持多开
    if user_id:
        user_data_dir = os.path.join(client_dir, f"playwright-binance-{user_id}")
    else:
        user_data_dir = os.path.join(client_dir, "playwright-binance")
    
    # 每次登录都清理缓存（reset=True）
    if reset:
        if os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir)
            log_msg = log_callback if log_callback else print
            log_msg(f"已清理浏览器缓存: {user_data_dir}")

    args = [
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,960",
    ]

    if headless:
        args += ["--headless=new", "--disable-gpu"]

    common_kwargs = dict(
        user_data_dir=user_data_dir,
        headless=headless,
        args=args,
        viewport={"width": 1280, "height": 960},
        locale="zh-CN",
        user_agent=WIN_UA,
        extra_http_headers={
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua-mobile": "?0",
            "accept-language": "zh-CN,zh;q=0.9"
        },
    )

    return pw.chromium.launch_persistent_context(**common_kwargs)


def apply_windows_ua(ctx, page):
    """应用Windows User-Agent"""
    page.add_init_script(f"""
        Object.defineProperty(navigator, 'userAgent', {{get: () => '{WIN_UA}' }});
        Object.defineProperty(navigator, 'platform', {{get: () => 'Win32' }});
        Object.defineProperty(navigator, 'vendor', {{get: () => 'Google Inc.' }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => 0 }});
    """)

    try:
        s = ctx.new_cdp_session(page)
        s.send("Emulation.setUserAgentOverride", {
            "userAgent": WIN_UA,
            "platform": "Windows",
            "acceptLanguage": "zh-CN,zh;q=0.9"
        })
    except:
        pass

    ctx.set_extra_http_headers({
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-mobile": "?0",
        "accept-language": "zh-CN,zh;q=0.9"
    })


def print_qr(data, log_callback=None):
    """打印二维码到终端"""
    qr = qrcode.QRCode(border=0)
    qr.add_data(data)
    qr.make(fit=True)
    m = qr.get_matrix()

    black = "  "
    white = "██"
    scale = 1
    margin = 1
    w = len(m[0])
    
    log_msg = log_callback if log_callback else print

    for _ in range(margin * scale):
        log_msg(white * (w + margin * 2))

    for row in m:
        line = white * margin
        for v in row:
            line += (black if v else white) * scale
        line += white * margin
        for _ in range(scale):
            log_msg(line)

    for _ in range(margin * scale):
        log_msg(white * (w + margin * 2))


def get_token(reset=False, headless=True, qr_callback=None, user_id=None, log_callback=None):
    """
    获取币安Token
    
    Args:
        reset: 是否重置浏览器缓存（每次登录都清理，默认True）
        headless: 是否无头模式
        qr_callback: 二维码回调函数，接收二维码数据作为参数
        user_id: 用户ID，用于多账号支持（不同账号使用不同目录）
    
    Returns:
        dict: 包含csrftoken, p20t, expirationTimestamp的字典
    """
    # 每次登录都清理缓存
    if reset is None:
        reset = True
    
    # 只在需要时才导入playwright
    from playwright.sync_api import sync_playwright
    
    csrftoken = ""
    p20t = ""
    expirationTimestamp = -1
    
    with sync_playwright() as pw:
        ctx = launch_persistent_ctx(pw, reset=reset, headless=headless, user_id=user_id, log_callback=log_callback)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        apply_windows_ua(ctx, page)

        qr_results = []

        def update_p20t_from_context():
            try:
                cookies = ctx.cookies("https://www.binance.com")
                c = next((c for c in cookies if c.get("name") == "p20t"), None)
                token = c.get("value", "")
                if not token:
                    return
                nonlocal p20t
                p20t = token
            except:
                pass

        def on_request(req):
            try:
                url = req.url
                if "https://www.binance.com/fapi/v1/ticker/24hr" in url:
                    token = req.headers.get("csrftoken", "")
                    if not token:
                        return
                    nonlocal csrftoken
                    csrftoken = token
            except:
                pass

        def on_request_finished(req):
            try:
                url = req.url
                if "https://accounts.binance.com/bapi/accounts/v2/public/qrcode/login/get" in url:
                    resp = req.response()
                    if not resp:
                        return
                    data = resp.json()
                    if not data.get("success"):
                        return
                    code = data["data"]["qrCode"]
                    if code not in qr_results:
                        qr_results.append(code)
                        log_msg = log_callback if log_callback else print
                        log_msg("请使用 Binance App 扫描以下二维码登录")
                        print_qr(code, log_callback=log_callback)
                        img = qrcode.make(code).convert("RGB")
                        img.save("qrcode.jpg", format="JPEG", quality=100)
                        # 调用回调函数
                        if qr_callback:
                            qr_callback(code)
                elif "https://accounts.binance.com/bapi/accounts/v2/private/authcenter/setTrustDevice" in url:
                    resp = req.response()
                    if not resp:
                        return
                    hdrs_arr = resp.headers_array()
                    date_hdr = resp.headers.get("date") or resp.header_value("date")
                    if not hdrs_arr or not date_hdr:
                        return
                    sc_values = [h.get("value", "") for h in hdrs_arr if h.get("name", "").lower() == "set-cookie"]
                    m = next((m for sc in sc_values for m in SimpleCookie(sc).values() if m.key == "p20t"), None)
                    if not m:
                        return
                    nonlocal p20t, expirationTimestamp
                    p20t = m.value
                    expirationTimestamp = int(m["max-age"]) + int(parsedate_to_datetime(date_hdr).timestamp())
            except:
                pass

        page.on("request", on_request)
        page.on("requestfinished", on_request_finished)
        ctx.on("request", on_request)
        ctx.on("requestfinished", on_request_finished)

        page.goto("https://accounts.binance.com/zh-CN/login?loginChannel=&return_to=", wait_until="domcontentloaded")

        while True:
            page.wait_for_timeout(1500)

            if csrftoken and p20t:
                token_dict = {"csrftoken": csrftoken, "p20t": p20t, "expirationTimestamp": expirationTimestamp}
                log_msg = log_callback if log_callback else print
                log_msg("✓ 币安登录成功，获取到Token:")
                log_msg(f"  csrftoken: {csrftoken[:20]}...")
                log_msg(f"  p20t: {p20t[:20]}...")
                log_msg(f"  expirationTimestamp: {expirationTimestamp}")
                ctx.close()
                log_msg("✓ 浏览器已关闭")
                return token_dict

            try:
                if "accounts.binance.com" in page.url:
                    if page.get_by_text(re.compile("Understand")).count() > 0:
                        page.get_by_role("button", name=re.compile("Understand")).first.click(timeout=1200, force=True)

                    if page.get_by_text(re.compile("知道了")).count() > 0:
                        page.get_by_role("button", name=re.compile("知道了")).first.click(timeout=1200, force=True)

                    if page.get_by_text(re.compile("好的")).count() > 0:
                        page.get_by_role("button", name=re.compile("好的")).first.click(timeout=1200, force=True)

                    if page.get_by_text(re.compile("登录")).count() > 0 and page.get_by_text(re.compile("邮箱/手机号码")).count() > 0 and page.get_by_text(re.compile("用手机相机扫描")).count() == 0:
                        page.get_by_role("button", name=re.compile("登录")).first.click(timeout=1200, force=True)

                    if page.get_by_text(re.compile("刷新二维码")).count() > 0:
                        page.get_by_role("button", name=re.compile("刷新二维码")).first.click(timeout=1200, force=True)

                    if page.get_by_text(re.compile("保持登录状态")).count() > 0:
                        page.get_by_role("button", name=re.compile("是")).first.click(timeout=1200, force=True)
                else:
                    update_p20t_from_context()
            except:
                pass


def place_order_web(csrftoken, p20t, orderAmount, timeIncrements, symbolName, payoutRatio, direction):
    """
    下单函数（复用原项目代码）
    """
    import requests
    url = "https://www.binance.com/bapi/futures/v1/private/future/event-contract/place-order"
    headers = {
        "content-type": "application/json",
        "clienttype": "web",
        "csrftoken": csrftoken,
        "cookie": f"p20t={p20t}"
    }
    data = {
        "orderAmount": orderAmount,
        "timeIncrements": timeIncrements,
        "symbolName": symbolName,
        "payoutRatio": payoutRatio,
        "direction": direction
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

