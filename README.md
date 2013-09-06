pynsd-rpcd
==========

A [zerorpc](https://github.com/dotcloud/zerorpc-python) based RPC Daemon to create, update and delete zones on NSD master.
based on [pynsd](https://github.com/novutec/pynsd)

Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)

Licensed under the Apache License, Version 2.0 (the "License").

Basic Example of Usage
------------------------
To use the rpc daemon you have to change the sample config /etc/[pynsd-rpcd.cfg](https://raw.github.com/novutec/pynsd/master/src/etc/pynsd-rpcd.cfg) to your settings
and start daemon.
 
```bash
pynsd-rpcd -c /etc/pynsd-rpcd.cfg
```

Send requests to rpc daemon:

```bash
zerorpc tcp://127.0.0.1:5912 zoneStatus testzone.example.
```

Or in python

```python
with open ("demozone.txt", "r") as f:
    zonedata=f.read()

clt = zerorpc.Client()
clt.connect('tcp://127.0.0.1:5912')
print clt.updateZone('testzone.example.', zonedata)
```

#### Available Commands
* addZone(name, zonedata, pattern = None)
* updateZone(name, zonedata)
* delZone(name)
* zoneStatus(name)
* reloadZone(name)
* notifyZone(name)
* transferZone(name)
* reconfig
* stats(noreset = True)

Installation
------------

```
1. Download zip file
2. Extract it
3. Execute in the extracted directory: python setup.py install
```

#### Development version

```
pip install -e git+git@github.com:novutec/pynsd-rpcd.git
```

#### Requirements

* Python 2.7 / 3.2 / 3.3
* [zerorpc](https://github.com/dotcloud/zerorpc-python) (for rpc daemon)
* argparse (to set config file in rpc daemon)
* [pynsd](https://github.com/novutec/pynsd)