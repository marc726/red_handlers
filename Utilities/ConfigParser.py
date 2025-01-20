import configparser
import os

def get_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'userinfo.cfg')
    config.read(config_path)
    return config