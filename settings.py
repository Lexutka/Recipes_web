import pathlib
import yaml


BASE_DIR = pathlib.Path(__file__).parent
config_path = BASE_DIR / '.config.yaml'


def get_config(path):
    with open(path) as f:
        parsed_config = yaml.safe_load(f)
        return parsed_config


config = get_config(config_path)
db_url = config['postgres']['database_url']