"""统一网络层。

两个坑：
1. 本机 Clash Verge 做 HTTPS 解密，它的自签根证书装在 Windows 系统证书库里；
   Python 默认不认系统库 → 报 CERTIFICATE_VERIFY_FAILED。
   解法：装 truststore 并注入 ssl，Python 就按系统库校验（不是关校验）。
2. 少数源（huggingface 等）直连不通，需要走 PROXY；所以每条请求都「直连→代理」两级降级。
"""
import os
import requests

try:  # 信任系统证书库（含本机代理的解密根证书）
    import truststore
    truststore.inject_into_ssl()
except Exception:  # pragma: no cover
    pass

PROXY = os.environ.get("PROXY", "")
TIMEOUT = int(os.environ.get("HTTP_TIMEOUT", "25"))

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _proxies():
    return {"http": PROXY, "https": PROXY} if PROXY else None


def request(method, url, *, headers=None, data=None, json=None, timeout=None, **kw):
    """直连优先，失败自动改走代理；返回 requests.Response。"""
    timeout = timeout or TIMEOUT
    s = requests.Session()
    s.trust_env = False  # 不吃系统/环境代理设置，避免不可控的中间层
    h = dict(_UA)
    h.update(headers or {})
    errors = []
    attempts = [("直连", None)]
    if PROXY:
        attempts.append(("代理", _proxies()))
    for label, prx in attempts:
        try:
            resp = s.request(method, url, headers=h, data=data, json=json,
                             timeout=timeout, proxies=prx, **kw)
            resp.raise_for_status()
            return resp
        except Exception as e:
            errors.append(f"{label}: {type(e).__name__} {e}")
    raise RuntimeError("请求失败 " + " / ".join(errors))


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)
