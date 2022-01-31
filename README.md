> Sorry for my bad English.

# Messyu
A tool to automatically configure Full Mesh Network with WireGuard.

## Commandline argments
| Key | Required | Default Value | Description |
|:---:|:---:|:---:|:---:| 
| --config | No | /etc/messyu/config.ini | Path to a config file. |

## config.ini

### Default Section

| Key | Required | Default Value | Description |
|:---:|:---:|:---:|:---:| 
| ExternalIP | Yes | None | IP address that can be accessed from the outside to this server. |

### Messyu Section

| Key | Required | Default Value | Description |
|:---:|:---:|:---:|:---:| 
| Secret | Yes | None | Secret key to protect the network from third person. (Share with all nodes.) |
| CertFile | No | False | Path to a certificate file for HTTPS traffic. (If the value is False, HTTP traffic will be used. The file must be shared all nodes. Hostname will be ignored.) |
| ListenPort | No | 55700 | Port that Messyu listen. |
| ExternalPort | No | Same as ListenPort | Port that can be accessed from the outside to Messyu. |
| Servers | No | None | Endpoints of another Messyu that will be accessed to get infomation of exsisted network. (Comma Separated. Get infomation from one of the nodes, that listed here and working properly. When joining the network, the endpoints of all nodes will be appended. So, if you want to join the network, you only need to set one node.) |

### WireGuard Section

| Key | Required | Default Value | Description |
|:---:|:---:|:---:|:---:| 
| Interface | No | messyu0 | Interface name for WireGuard. |
| ListenPort | No | 55701 | Port that WireGuard listen. |
| ExternalPort | No | Same as ListenPort | Port that can be accessed from the outside to WireGuard. |
| Address | No | Dynamic | IP address of Interface for WireGuard. (By default, if no other nodes are listed in Servers, IP address is 10.109.101.1/24. otherwise a dynamic IP is assigned by other nodes. You can assign a static IP too.) |

### The smallest example of config.ini

```ini:config.ini
[Default]
ExternalIP = 172.0.0.1

[Messyu]
Secret = Changeme
```

## Installation

### 1. Check requirements are already installed
1. openssl
1. wireguard
1. requests (Python library)

Other than wireguard are likely to be already installed.

### 2. Run this command

```bash
curl -sfL https://github.com/m-dev672/messyu/releases/download/v0.0.0-alpha/install.sh | sh -
```

### 3. Generate or copy certfile. (Recommended)
```bash
openssl req -x509 -new -nodes -keyout /etc/messyu/cert.pem -out /etc/messyu/cert.pem -subj "/"
```

### 4. Write config.ini according to above
If you follow these steps, config file is /etc/messyu/config.ini

### 5. Service enable and start

```bash
systemctl enable messyu.service
systemctl start messyu.service
```

## LICENSE
MIT License

Copyright (c) 2022 Mori Koutarou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
