found = False
try:
	import requesocks as requests
	found = True
except Exception, e:
	found = False
session = requests.session()
if found:
	session.proxies = {'http': 'socks5://127.0.0.1:9050',
                   'https': 'socks5://127.0.0.1:9050'}