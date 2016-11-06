#!/usr/bin/env python3
"""A basic CLI for the API. It allows to list, create and
delete services, exploits and targets."""
import sys
import logging
import argparse
import requests

LOGGER = logging.getLogger()
ARGS = argparse.ArgumentParser(description='CTF-PWN CLI')
SUBARGS = ARGS.add_subparsers(dest='cmd')

ARGS.add_argument(
    '--api', action='store', dest='api_server',
    default='127.0.0.1', help='The IP of the CTF-PWN API')
ARGS.add_argument(
    '--port', action='store', dest='api_port', type=int,
    default=8080, help='Port of the CTF-PWN API')

pservices = SUBARGS.add_parser('services', help='List and create services')
pservices.add_argument('--list', action='store_true', help='List all services')
pservices.add_argument('--delete', default=None, help='Delete a service')
pservices.add_argument('--name', help='Name of the service')
pservices.add_argument('--type', default='port',
                       help='Type of the service (port of url, default: port)')
pservices.add_argument('--port', help='Port of the service')
pservices.add_argument('--url', help='URL of the service (optional)')
pservices.add_argument('--meta', help='Any other information (optional)')

pexploits = SUBARGS.add_parser('exploits', help='List and create exploits')
pexploits.add_argument('--list', action='store_true', help='List all exploits')
pexploits.add_argument('--delete', default=None, help='Delete an exploits')
pexploits.add_argument('--service', help='The service which is exploited')
pexploits.add_argument('--exploit', help='The path of the exploit on the API host')
pexploits.add_argument('--port', help='The service port')
pexploits.add_argument('--enabled', action='store_true', dest='exploit_enabled',
                       default=True, help='Enable or disable the exploit (default: True)')

ptargets = SUBARGS.add_parser('targets', help='List targets')


class CtfpwnCli(object):
    def __init__(self, args):
        self.args = args
        self.api = 'http://' + self.args.api_server
        if str(self.args.api_port) != str(80):
            self.api += ':' + str(self.args.api_port)
        self.services = self.api + '/services'
        self.exploits = self.api + '/exploits'
        self.targets = self.api + '/targets'

    def create_service(self):
        if not self.args.name or not self.args.port:
            LOGGER.error('--name and --port are mandatory')
        data = dict(name=self.args.name,
                    type=self.args.type,
                    port=self.args.port,
                    url=self.args.url,
                    meta=self.args.meta)
        resp = requests.post(self.services, data=data)
        if resp.status_code == 201:
            print('Successfully created service')
        elif resp.status_code == 500:
            LOGGER.error('Creation of service failed')
        else:
            LOGGER.error('Unknown HTTP status: ' + str(resp.status_code))

    def delete_service(self):
        resp = requests.delete(self.services + '/' + self.args.delete)
        if resp.status_code == 200:
            print('Successfully deleted service')
        elif resp.status_code == 404:
            LOGGER.error('Service not found')
        elif resp.status_code == 500:
            LOGGER.error('Could not delete service')
        else:
            LOGGER.error('Unknown HTTP status: ' + str(resp.status_code))

    def list_services(self):
        resp = requests.get(self.services)
        print(resp.text)

    def create_exploit(self):
        if not self.args.service or not self.args.exploit \
                or not self.args.port:
            LOGGER.error('--service, --exploit and --port are mandatory')
        data = dict(service=self.args.service,
                    exploit=self.args.exploit,
                    port=self.args.port,
                    enabled=self.args.enabled)
        resp = requests.post(self.exploits, data=data)
        if resp.status_code == 201:
            print('Successfully created service')
        elif resp.status_code == 500:
            LOGGER.error('Creation of exploit failed')
        else:
            LOGGER.error('Unknown HTTP status: ' + str(resp.status_code))

    def delete_exploit(self):
        resp = requests.delete(self.exploits + '/' + self.args.delete)
        if resp.status_code == 200:
            print('Successfully deleted exploit')
        elif resp.status_code == 404:
            LOGGER.error('Exploit not found')
        elif resp.status_code == 500:
            LOGGER.error('Could not delete exploit')
        else:
            LOGGER.error('Unknown HTTP status: ' + str(resp.status_code))

    def list_exploits(self):
        resp = requests.get(self.exploits)
        print(resp.text)

    def list_targets(self):
        resp = requests.get(self.targets)
        print(resp.text)


def main():
    args = ARGS.parse_args()
    cli = CtfpwnCli(args)
    if args.cmd == 'services':
        if args.list:
            cli.list_services()
        elif args.delete:
            cli.delete_service()
        else:
            cli.create_service()
    elif args.cmd == 'exploits':
        if args.list:
            cli.list_exploits()
        elif args.delete:
            cli.delete_exploit()
        else:
            cli.create_exploit()
    elif args.cmd == 'targets':
        cli.list_targets()
    else:
        LOGGER.error('Invalid argument')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())