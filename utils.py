import requests


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.53'
}

COOKIES = {'SUB': '_2A25Pk2TfDeRhGeFI41MY9ivFyz6IHXVs6dEXrDV8PUNbmtAfLW3CkW9NfMwjopB5-A1wUaHGaw3Cz6N3uJOZZQuN'}


def get_api(api, wait=3):
    r = requests.get(api, headers=HEADERS, cookies=COOKIES)
    time.sleep(np.random.randint(wait, wait + 5))
    if r.status_code in [200, 304]:
        return r
    else:
        raise ValueError('API未能成功访问。')