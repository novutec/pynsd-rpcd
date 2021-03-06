# coding: utf-8
"""
Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@category Novutec
@package pynsd-rpcd
@copyright Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
@license http://www.apache.org/licenses/LICENSE-2.0
"""

import pynsd
import zerorpc
import ConfigParser
import os
import string
import argparse


class Config(object):

    def __init__(self):
        self.Server = {
            'bind': None
        }
        self.NSDMaster = {
            'clientcert': None,
            'clientkey': None,
            'controlhost': 'localhost',
            'controlport': 8952
        }
        self.Zones = {
            'dir': None,
            'pattern': None,
            'filepattern': None
        }

    def loadFile(self, filename):
        cp = ConfigParser.ConfigParser()
        cp.read(filename)

        for section in ('Server', 'NSDMaster', 'Zones'):
            try:
                options = cp.options(section)
                for option in options:
                    vl = cp.get(section, option)
                    self.__dict__[section][option.lower()] = vl
            except:
                pass


class Result(object):
    def __init__(self, code, msg, **data):
        self.__dict__ = data
        self.code = code
        self.msg = msg

    def dict(self):
        return self.__dict__


class ErrorResult(Exception, Result):
    def __init__(self, code, msg='Call failed.', **data):
        Result.__init__(self, code, msg, **data)


class Server(object):
    validZoneChars = "-_.%s%s" % (string.ascii_letters, string.digits)

    def __init__(self, cfg):
        self.cfg = cfg
        self.cc = pynsd.ControlClient(cfg.NSDMaster['clientcert'],
                                      cfg.NSDMaster['clientkey'],
                                      cfg.NSDMaster['controlhost'],
                                      int(cfg.NSDMaster['controlport']),
                                      strip=True)

    def addZone(self, name, zonedata, pattern=None):
        name = self._filterZoneName(name)
        spattern = pattern or self.cfg.Zones['pattern']
        res = self.cc.call('addzone', [name, spattern])
        if res != 'ok':
            return ErrorResult(2302, 'Object exists', nsdresult=res).dict()

        if zonedata is not None and zonedata != '':
            self._writeZoneFile(name, zonedata)
        return self.reloadZone(name)

    def _filterZoneName(self, name):
        return filter(lambda c: c if c in self.validZoneChars else '', name)

    def _parseZoneFilePattern(self, name):
        fp = self.cfg.Zones['filepattern']
        for x in range(1, 4):
            if '%' + str(x) in fp:
                rep = ''
                if len(name) > x:
                    rep = name[x - 1]
                fp = fp.replace('%' + str(x), rep)
        if not '%s' in fp:
            raise Exception('%s missing in filepattern definition.')
        parts = name.split('.')
        parts.reverse()
        parts.pop()
        for x, ky in enumerate(('z', 'y', 'x')):
            if '%' + ky in fp:
                rep = ''
                if len(parts) > x:
                    rep = parts[x]
                fp = fp.replace('%' + ky, rep)
        fp = fp.replace('%s', name)
        return fp.replace('//', '/')

    def updateZone(self, name, zonedata):
        name = self._filterZoneName(name)
        res = self.cc.call('zonestatus', [name])
        if 'error ' in res:
            return ErrorResult(2303, 'Object does not exists',
                               nsdresult=res).dict()

        self._writeZoneFile(name, zonedata)
        return self.reloadZone(name)

    def _writeZoneFile(self, name, zonedata):
        zfname = self._parseZoneFilePattern(name)
        zffull = self.cfg.Zones['dir'] + '/' + zfname
        directory = os.path.dirname(zffull)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(zffull, 'wb') as zf:
            zf.write(zonedata)

    def _delZoneFile(self, name):
        zfname = self._parseZoneFilePattern(name)
        zffull = self.cfg.Zones['dir'] + '/' + zfname
        directory = os.path.dirname(zffull)
        if not os.path.exists(directory):
            return
        os.remove(zffull)

    def _call(self, cmd, name, *args):
        if name is not None:
            name = self._filterZoneName(name)
            call_args = [name]
        call_args += args
        res = self.cc.call(cmd, call_args)
        if ('error ' in res):
            return ErrorResult(2400, 'Command failed',
                               nsdresult=res).dict()
        return Result(1000, 'Command completed successfully',
                      nsdresult=res).dict()

    def delZone(self, name):
        name = self._filterZoneName(name)
        res = self.cc.call('delzone', [name])
        if ('error ' in res):
            return ErrorResult(2400, 'Command failed',
                               nsdresult=res).dict()
        self._delZoneFile(name)
        return Result(1000, 'Command completed successfully',
                      nsdresult=res).dict()

    def zoneStatus(self, name):
        return self._call('zonestatus', name)

    def reloadZone(self, name):
        return self._call('reload', name)

    def notifyZone(self, name):
        return self._call('notify', name)

    def transferZone(self, name):
        return self._call('transfer', name)

    def reconfig(self):
        return self._call('reconfig', None)

    def stats(self, noreset=True):
        cmd = 'stats'
        if noreset:
            cmd = 'stats_noreset'
        res = self.cc.call(cmd)
        if ('error ' in res):
            return ErrorResult(2400, 'Command failed',
                               nsdresult=res).dict()
        stats = {}
        for line in res.split("\n"):
            (ky, vl) = line.split('=', 2)
            stats[ky] = vl

        return Result(1000, 'Command completed successfully',
                      stats=stats).dict()


class Daemon(zerorpc.Server):
    def __init__(self, configfile):
        self.cfg = Config()
        self.cfg.loadFile(configfile)
        self.srv = Server(self.cfg)
        zerorpc.Server.__init__(self, self.srv, name="pynsd-rpcd")
        self.bind(self.cfg.Server['bind'])

    @staticmethod
    def cliRun():
        parser = argparse.ArgumentParser(description='Starts NSD RPC daemon.')
        parser.add_argument('-c', '--config', dest='config', required=True,
                            help='config file to load')

        args = parser.parse_args()
        Daemon(args.config).run()
