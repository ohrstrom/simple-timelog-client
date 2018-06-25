# -*- coding: utf-8 -*-
import logging
import sys
import click
import os
import configparser
import calendar
import dateutil.parser
from pathlib import Path

from datetime import datetime, timedelta, date

from .client import TimelogClient
from .exceptions import TimelogClientAPIException

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.timelog')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')

PRINT_LINE_WIDTH = 120

__version__ = '0.0.1'

logger = logging.getLogger(__name__)


def get_config():

    config = configparser.ConfigParser()

    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as config_file:
            config.write(config_file)

    config.read(CONFIG_FILE)

    return config


@click.group()
def cli():

    click.secho('using config: {}'.format(CONFIG_FILE), fg='white')

    pass

@cli.command()
def version():
    print(__version__)
    sys.exit()


@cli.command()
def login():

    click.echo('login')

    config = get_config()

    if not config.has_section('api'):
        config.add_section('api')

    if config.has_option('api', 'endpoint'):
        endpoint = config.get('api', 'endpoint')
    else:
        endpoint = click.prompt('API endpoint', type=str)
        config.set('api', 'endpoint', endpoint)


    email = click.prompt('API email', type=str)
    password = click.prompt('API password', type=str)

    c = TimelogClient(
        endpoint=endpoint
    )

    try:
        token = c.login(email=email, password=password)
    except TimelogClientAPIException as e:
        click.secho('unable to login: {}'.format(e), fg='white', bg='red')
        sys.exit()


    config.set('api', 'token', token)

    with open(CONFIG_FILE, 'w') as config_file:
        config.write(config_file)


@cli.command()
@click.argument('project_key')
@click.argument('str_time')
@click.option('--date', '-d', 'str_date', type=str, required=False)
@click.option('--note', '-n', 'notes', type=str, multiple=True, required=True)
@click.option('--component', '-c', 'component', type=str, required=False)
def log(project_key, str_time, str_date, notes, component):

    config = get_config()

    # handle time input
    if '.' in str_time:
        # convert e.g. 3.75 to '3:45'
        str_time = '%d:%02d' % (int(float(str_time)), (float(str_time) * 60) % 60)

    time_minutes = sum(i * j for i, j in zip(map(int, str_time.split(':')), [60, 1]))
    time_spent = str_time + ':00'

    # handle date input date
    # parse input in form of 'YYYY-MM-DD' - defaults to 'today'
    if str_date:
        #date = datetime.strptime(str_date, '%Y-%m-%d').date()
        date = str_date
    else:
        date = datetime.today().date().strftime("%Y-%m-%d")

    click.secho('logging time: {project_key} - {time_spent} - {date}'.format(
        project_key=project_key, time_spent=time_spent, date=date
    ), fg='green')


    c = TimelogClient(
        endpoint=config.get('api', 'endpoint'),
        token=config.get('api', 'token'),
    )

    entry = c.log(
        project_key=project_key,
        time_spent=time_spent,
        date=date,
        notes=notes,
        component=component,
    )

    click.secho(str(entry), fg='cyan')


@cli.command()
@click.option('--timestamp', '-t', 'str_timestamp', type=str, required=False)
def checkin(str_timestamp):

    config = get_config()

    if str_timestamp:
        timestamp = str_timestamp
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    click.secho('checkin: {timestamp}'.format(
        timestamp=timestamp
    ), fg='green')

    c = TimelogClient(
        endpoint=config.get('api', 'endpoint'),
        token=config.get('api', 'token'),
    )

    entry = c.attendance(
        status=1,
        timestamp=timestamp,
    )

    click.secho(str(entry), fg='cyan')


@cli.command()
@click.option('--timestamp', '-t', 'str_timestamp', type=str, required=False)
def checkout(str_timestamp):

    config = get_config()

    if str_timestamp:
        timestamp = str_timestamp
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    click.secho('checkout: {timestamp}'.format(
        timestamp=timestamp
    ), fg='green')

    c = TimelogClient(
        endpoint=config.get('api', 'endpoint'),
        token=config.get('api', 'token'),
    )

    entry = c.attendance(
        status=0,
        timestamp=timestamp,
    )

    click.secho(str(entry), fg='cyan')


@cli.command()
@click.option('--scope', '-s', 'scope', type=click.Choice(['day', 'week', 'month']), default='day', required=False)
def report(scope):

    config = get_config()

    c = TimelogClient(
        endpoint=config.get('api', 'endpoint'),
        token=config.get('api', 'token'),
    )

    date_start = None
    date_end = None

    if scope == 'day':
        date_start = datetime.now().strftime('%Y-%m-%d')
        date_end = datetime.now().strftime('%Y-%m-%d')

    if scope == 'week':
        now = datetime.now()
        _date_start = now - timedelta(days=now.weekday())
        _date_end = _date_start + timedelta(days=6)
        date_start = _date_start.strftime('%Y-%m-%d')
        date_end = _date_end.strftime('%Y-%m-%d')

    if scope == 'month':
        now = datetime.now()
        _, num_days = calendar.monthrange(now.year, now.month)
        date_start = date(now.year, now.month, 1).strftime('%Y-%m-%d')
        date_end = date(now.year, now.month, num_days).strftime('%Y-%m-%d')

    click.secho('-' * PRINT_LINE_WIDTH, fg='cyan')
    click.secho('report:\t\t{date_start} - {date_end}'.format(
        date_start=date_start,
        date_end=date_end
    ), fg='green')
    click.secho('app:\t\t{}/admin/'.format(config.get('api', 'endpoint')), fg='green')


    log, attendance = c.report(
        date_start=date_start,
        date_end=date_end,
    )

    ###################################################################
    # not so nice way to build time/log summary...
    ###################################################################
    tpl = '{date}\t{time_spent}\t{project}\t | {notes}'
    total_time_spent = 0
    lines = []

    for entry in log['results']:
        lines.append(
            tpl.format(
                **entry
            )
        )
        total_time_spent += sum(i * j for i, j in zip(map(int, entry['time_spent'].split(':')), [60, 1]))


    click.secho('-' * PRINT_LINE_WIDTH, fg='cyan')

    for line in lines:
        click.secho(line, fg='cyan')

    click.secho('-' * PRINT_LINE_WIDTH, fg='cyan')
    click.secho('TOTAL:\t\t{:02d}:{:02d}:00'.format(*divmod(total_time_spent, 60)), fg='cyan')
    click.secho('=' * PRINT_LINE_WIDTH, fg='cyan')


    ###################################################################
    # not so nice way to build attendance summary...
    ###################################################################
    if scope == 'day':

        if not attendance['count'] == 2:
            click.secho('unable to build attendance. need exactly 2 entries', bg='red')
            return
        else:
            _checkin = attendance['results'][1]['timestamp']
            _checkout = attendance['results'][0]['timestamp']

            checkin = dateutil.parser.parse(_checkin)
            checkout = dateutil.parser.parse(_checkout)

            total_attendance = checkout - checkin


        click.secho('\n' + '-' * PRINT_LINE_WIDTH, fg='cyan')

        click.secho('Check In:\t{checkin}'.format(checkin=checkin.strftime('%H:%M:%S')), fg='green')
        click.secho('Check Out:\t{checkout}'.format(checkout=checkout.strftime('%H:%M:%S')), fg='yellow')

        click.secho('TOTAL:\t\t {}'.format(total_attendance), fg='cyan')

        click.secho('-' * PRINT_LINE_WIDTH, fg='cyan')


@cli.command()
@click.option('--address', '-i', 'ip_address', type=str, required=True)
def watch(ip_address):

    import time
    import socket

    config = get_config()

    click.secho('watch: {ip_address}'.format(
        ip_address=ip_address
    ), fg='green')

    c = TimelogClient(
        endpoint=config.get('api', 'endpoint'),
        token=config.get('api', 'token'),
    )

    last_state = 'offline'

    while True:

        # my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)

        response = os.system('ping -c 1 {}'.format(ip_address))

        # 0 -> online
        if response == 0:
            state = 'online'
        else:
            state = 'offline'

        if last_state != state:
            click.secho('state changed: {} > {}'.format(last_state, state), fg='green')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

            if state == 'online':
                c.attendance(
                    status=1,
                    timestamp=timestamp,
                )

            if state == 'offline':
                c.attendance(
                    status=0,
                    timestamp=timestamp,
                )

        else:
            click.secho('state unchanged: {}'.format(state), fg='cyan')

        last_state = state

        time.sleep(5)




    # c = TimelogClient(
    #     endpoint=config.get('api', 'endpoint'),
    #     token=config.get('api', 'token'),
    # )
    #
    # entry = c.attendance(
    #     status=0,
    #     timestamp=timestamp,
    # )
    #
    # click.secho(str(entry), fg='cyan')
