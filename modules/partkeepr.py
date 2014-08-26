from ._module import _module

import http.client
import urllib.parse
import json

class partkeepr(_module):
    def cmd_locate(self, args, source, target, admin):
        parts = self.findpart(' '.join(args))
        if parts:
            partstr = ', '.join(['{{name: "{name}", location: "{location}", stock: {stock}}}'.format(**part) for part in parts])
            return ['Part found: ' + partstr]
        else:
            return ['Part not found']
    def findpart(self, query):
        try:
            conn = http.client.HTTPConnection('parts.tkkrlab.nl')
            body = json.dumps({'username': self.get_config('username'), 'password': self.get_config('password')})
            conn.request('POST', '/rest.php/Auth/login', body)

            resp = conn.getresponse()
            body = json.loads(resp.read().decode('utf-8'))

            sessionid = body['response']['sessionid']

            conn.request('GET', '/rest.php/Part?query={}'.format(urllib.parse.quote_plus(query)), None, {'session': sessionid})

            body = json.loads(conn.getresponse().read().decode('utf-8'))
            response = body['response']

            if int(response['totalCount']) > 0:
                return [{'name': data['name'], 'location': data['storageLocationName'], 'stock': int(data['stockLevel'])} for data in response['data']]
            else:
                return None
        except Exception as e:
            return None

