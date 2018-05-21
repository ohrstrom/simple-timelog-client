# -*- coding: utf-8 -*-
import logging
import sys
import click
import os
import configparser
from pathlib import Path

from datetime import datetime

from .client import TimelogClient
from .exceptions import TimelogClientAPIException

CONFIG_DIR = os.path.join(Path.home(), '.timelog')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.ini')

print(CONFIG_DIR)
print(CONFIG_FILE)

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

    #
    # sys.exit()




@cli.command()
@click.argument('project_key')
@click.argument('str_time')
@click.option('--date', '-d', 'str_date', type=str, required=False)
@click.option('--comment', '-c', 'comment', type=str, multiple=True, required=True)
def log(project_key, str_time, str_date, comment):


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

    c.log(project_key=project_key, time_spent=time_spent, date=date, comment=comment)

    #click.echo('...')
