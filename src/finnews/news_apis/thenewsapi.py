import http.client, urllib.parse

conn = http.client.HTTPSConnection('api.thenewsapi.com')

params = urllib.parse.urlencode({
    'api_token': 'YOUR_API_TOKEN',
    'categories': 'business,tech',
    'limit': 50,
    })

# All News
conn.request('GET', '/v1/news/all?{}'.format(params))
# # News by UUID. 
# conn.request('GET', '/v1/news/uuid/{uuid}?{}'.format(params))
# # Sources
# conn.request('GET', '/v1/news/sources?{}'.format(params))

res = conn.getresponse()
data = res.read()

print(data.decode('utf-8'))