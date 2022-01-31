#!/usr/bin/env python3
import argparse
import configparser
import subprocess
import requests
import urllib.parse
import random
import json
import ssl
from wsgiref.simple_server import make_server

class HostHeaderSSLAdapter(requests.adapters.HTTPAdapter):
    def send(self, request, **kwargs):
        self.poolmanager.connection_pool_kw["assert_hostname"] = False
        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)

parser = argparse.ArgumentParser(description='Messyu - A tool to automatically configure Full Mesh Network with WireGuard.')
parser.add_argument('--config', default='/etc/messyu/config.ini', help='Path to config file.')
args = parser.parse_args()

config_ini = configparser.ConfigParser()
config_ini.optionxform = str
config_ini.read(args.config, encoding='utf-8')

secret = config_ini['Messyu']['Secret']
me_listenport = config_ini['Messyu']['ListenPort'] if config_ini.has_option('Messyu', 'ListenPort') else '55700'
me_endpoint = '{}:{}'.format(config_ini['Default']['ExternalIP'], config_ini['Messyu']['ExternalPort'] if config_ini.has_option('Messyu', 'ExternalPort') else me_listenport)
verify = config_ini['Messyu']['CertFile'] if config_ini.has_option('Messyu', 'CertFile') else False
interface = config_ini['WireGuard']['Interface'] if config_ini.has_option('WireGuard', 'Interface') else 'messyu0'
wg_listenport = config_ini['WireGuard']['ListenPort'] if config_ini.has_option('WireGuard', 'ListenPort') else '55701'
wg_endpoint = '{}:{}'.format(config_ini['Default']['ExternalIP'], config_ini['WireGuard']['ExternalPort'] if config_ini.has_option('WireGuard', 'ExternalPort') else wg_listenport)
privatekey = subprocess.check_output('wg genkey', shell=True).decode("utf-8").strip()
publickey = subprocess.check_output('echo {} | wg pubkey'.format(privatekey), shell=True).decode("utf-8").strip()

_dict1 = {}
_dict2 = {}

for s in config_ini['Messyu']['Servers'].split(',') if config_ini.has_option('Messyu', 'Servers') else []:
    session = requests.Session()
    session.mount('https://', HostHeaderSSLAdapter())
    try:
        response = session.post('{}://{}/get_nodes'.format('https' if verify else 'http', s.strip()), data={'secret': secret}, timeout=(3, None), verify=verify)
        cidrs = [(sum([int(e) << i for i, e in zip([24, 16, 8, 0], cidr.split('/')[0].split('.'))]), 2 ** int(cidr.split('/')[1]) - 1 << 32 - int(cidr.split('/')[1])) for cidr in response.json().values()]
        iprange = range(max([address & mask for address, mask in cidrs]), min([address | (~mask & 4294967295) for address, mask in cidrs]))
        if config_ini.has_option('WireGuard', 'Address'):
            address = sum([int(e) << i for i, e in zip([24, 16, 8, 0], config_ini['WireGuard']['Address'].split('/')[0].split('.'))]) if config_ini.has_option('WireGuard', 'Address') else 174941441
            mask = int(config_ini['WireGuard']['Address'].split('/')[1]) if config_ini.has_option('WireGuard', 'Address') else 24
            if address not in iprange or min(iprange) < (address & (2 ** mask - 1 << 32 - mask)) or (address | (~(2 ** mask - 1 << 32 - mask) & 4294967295)) < max(iprange): exit(1);
        else:
            address = random.choice(list(set(iprange) - set([cidr[0] for cidr in cidrs])))
            i, t = max(max(iprange) - address, address - min(iprange)), 0
            while i >= 2: i /= 2; t += 1;
            mask = 32 - (t + 1)
        _dict1[me_endpoint] = '.'.join([str((address << i & 4294967295) >> 24) for i in [0, 8, 16, 24]]) + '/{}'.format(mask)
        for key in response.json().keys():
            try:
                response = session.post('{}://{}/add_node'.format('https' if verify else 'http', key), data={'secret': secret, 'me_endpoint': me_endpoint, 'wg_endpoint': wg_endpoint, 'cidr': _dict1[me_endpoint], 'publickey': publickey}, timeout=(3, None), verify=verify)
                if response.status_code == 200:
                    _dict1[key] = response.json()['cidr']
                    _dict2[key] = {'wg_endpoint': response.json()['wg_endpoint'], 'publickey': response.json()['publickey']}
                    config_ini.set('Messyu', 'Servers', ', '.join(_dict2.keys()))
                    with open(args.config, 'w') as f:
                        config_ini.write(f)
            except requests.exceptions.RequestException:
                pass
        break
    except requests.exceptions.RequestException:
        pass
else:
    address = sum([int(e) << i for i, e in zip([24, 16, 8, 0], config_ini['WireGuard']['Address'].split('/')[0].split('.'))]) if config_ini.has_option('WireGuard', 'Address') else 174941441
    mask = config_ini['WireGuard']['Address'].split('/')[1] if config_ini.has_option('WireGuard', 'Address') else 24
    _dict1[me_endpoint] = '.'.join([str((address << i & 4294967295) >> 24) for i in [0, 8, 16, 24]]) + '/{}'.format(mask)

subprocess.run(['wg-quick down {}'.format(interface)], shell=True)
_str1 = '[Interface]\nAddress = {}\nListenPort = {}\nPrivateKey = {}\nPostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT;\nPostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT;'.format(_dict1[me_endpoint], wg_listenport, privatekey)
_str2 = ''
for key in _dict2.keys():
    _str2 += '\n\n[Peer]\nPublicKey = {}\nEndpoint = {}\nAllowedIPs = {}/32'.format(_dict2[key]['publickey'], _dict2[key]['wg_endpoint'], _dict1[key].split('/')[0])
with open('/etc/wireguard/{}.conf'.format(interface), mode='w') as f:
    f.write(_str1 + _str2)
subprocess.run(['chmod 600 /etc/wireguard/{}.conf'.format(interface)], shell=True)
subprocess.run(['wg-quick up {}'.format(interface)], shell=True)

def app(environ, start_response):
    path_info = environ['PATH_INFO']
    request_method = environ['REQUEST_METHOD']
    if request_method == 'POST':
        query = urllib.parse.parse_qs(environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', 0))).decode('utf-8'))
        if query['secret'][0] == secret:
            if path_info == '/get_nodes':
                start_response('200 OK', [('Content-type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')])
                return [json.dumps(_dict1).encode("utf-8")]
            elif path_info == '/add_node':
                for key in [key for key, value in _dict1.items() if value == query['cidr'][0]]:
                    if key == me_endpoint:
                        del _dict1[key];
                        start_response('409 Conflict', [('Content-type', 'text/plain; charset=utf-8'), ('Access-Control-Allow-Origin', '*')])
                        return [b'409 Conflict']
                    else:
                        del _dict1[key], _dict2[key];
                _dict1[query['me_endpoint'][0]] = query['cidr'][0]
                _dict2[query['me_endpoint'][0]] = {'wg_endpoint': query['wg_endpoint'][0], 'publickey': query['publickey'][0]}
                _str2 = ''
                for key in _dict2.keys():
                    _str2 += '\n\n[Peer]\nPublicKey = {}\nEndpoint = {}\nAllowedIPs = {}/32'.format(_dict2[key]['publickey'], _dict2[key]['wg_endpoint'], _dict1[key].split('/')[0])
                with open('/etc/wireguard/{}.conf'.format(interface), mode='w') as f:
                    f.write(_str1 + _str2)
                subprocess.run(['wg-quick strip {0} > /tmp/stripped && wg setconf {0} /tmp/stripped'.format(interface)], shell=True)
                config_ini.set('Messyu', 'Servers', ', '.join(_dict2.keys()))
                with open(args.config, 'w') as f:
                    config_ini.write(f)
                start_response('200 OK', [('Content-type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')])
                return [json.dumps({'wg_endpoint': wg_endpoint, 'publickey': publickey, 'cidr': _dict1[me_endpoint]}).encode("utf-8")]
        else:
            start_response('403 Forbidden', [('Content-type', 'text/plain; charset=utf-8'), ('Access-Control-Allow-Origin', '*')])
            return [b'403 Forbidden']
    start_response('404 Not Found', [('Content-type', 'text/plain; charset=utf-8'), ('Access-Control-Allow-Origin', '*')])
    return [b'404 Not Found']

if __name__ == '__main__':
    with make_server('', int(me_listenport), app) as httpd:
        if verify:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(verify)
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            httpd.socket = context.wrap_socket(httpd.socket)
        httpd.serve_forever()
