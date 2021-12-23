import time
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Type

import schedule

from backupGD import (
    __version__,
    app,
    credentials,
    log
)


logger = logging.getLogger(__name__)

class RootNamespace(Namespace):
    log_level: str = 'info'
    version: bool = False
    name: str = 'backupGD'
    path: Path = Path('./data').resolve()
    every: int = 1
    day: str = 'days'
    at: str = '00:00'
    keep: int = 16
    client_secret: Path = Path('./client_secret.json').resolve()
    token: Path = Path('./token.json').resolve()


def create_parser() -> ArgumentParser:
    """ Create Argument Parser """
    parser = ArgumentParser(
        'backupGD',
        usage='%(prog)s [optional arguments]'
    )

    parser.add_argument(
        '--log-level',
        default=RootNamespace.log_level,
        type=type(RootNamespace.log_level),
        choices=['critical', 'error', 'warning', 'info', 'debug'],
        dest='log_level',
        help='logging level [default: %(default)s]'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        dest='version',
        help='show version'
    )
    parser.add_argument(
        '--name',
        default=RootNamespace.name,
        type=type(RootNamespace.name),
        dest='name',
        metavar='TEXT',
        help='folder name on GoogleDrive [default: %(default)s]'
    )
    parser.add_argument(
        '--path',
        default=RootNamespace.path,
        type=type(RootNamespace.path),
        dest='path',
        metavar='PATH',
        help='path to file or directory to back up [default: %(default)s]'
    )
    parser.add_argument(
        '--every',
        default=RootNamespace.every,
        type=type(RootNamespace.every),
        dest='every',
        metavar='INTEGER',
        help='interval [default: %(default)s]'
    )
    parser.add_argument(
        '--day',
        default=RootNamespace.day,
        type=type(RootNamespace.day),
        choices=[
            'days', 
            'sunday', 
            'monday', 
            'tuesday', 
            'wednesday', 
            'thursday', 
            'friday', 
            'saturday',
            'weeks'
        ],
        dest='day',
        help='days to keep in drive [default: %(default)s]'
    )
    parser.add_argument(
        '--at',
        default=RootNamespace.at,
        type=type(RootNamespace.at),
        dest='at',
        metavar='TEXT',
        help='time to run [default: %(default)s]'
    )
    parser.add_argument(
        '--keep',
        default=RootNamespace.keep,
        type=type(RootNamespace.keep),
        dest='keep',
        metavar='INTEGER',
        help='max number of backup files on GoogleDrive [default: %(default)s]'
    )
    parser.add_argument(
        '--client-secret',
        default=RootNamespace.client_secret,
        type=type(RootNamespace.client_secret),
        dest='client_secret',
        metavar='PATH',
        help='path to client_secret.json [default: %(default)s]'
    )
    parser.add_argument(
        '--token',
        default=RootNamespace.token,
        type=type(RootNamespace.token),
        dest='token',
        metavar='PATH',
        help='path to OAuth2.0 token [default: %(default)s]'
    )
    
    return parser


def get_credentials(args: Type[RootNamespace]) -> credentials.Credentials:
    if args.token.exists():
        creds: credentials.Credentials = credentials.Credentials.from_authorized_user_file(args.token.as_posix())
    elif args.client_secret.exists():
        creds = credentials.get_credentials(args.client_secret)
    else:
        creds = credentials.get_credentials()
    return creds
    

def main() -> None:
    parser: ArgumentParser = create_parser()
    args: Type[RootNamespace] = parser.parse_args(namespace=RootNamespace)
    if args.version:
        print(__version__)
        exit(0)
    if not args.path.exists():
        print(FileNotFoundError(f'"--path" argument {args.path.as_posix()} not found.'))
        exit(1)
    
    log.setup(args.log_level.upper())
    creds: credentials.Credentials = get_credentials(args)
    _app: app.App = app.App(keep=args.keep, credentials=creds)
    _app.run(args.path, args.name)
    job = lambda: _app.run(args.path, args.name)
    getattr(schedule.every(args.every), args.day).at(args.at).do(job)
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    main()