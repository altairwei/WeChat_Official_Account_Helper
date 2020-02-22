import os

import confuse


config = confuse.Configuration("docpub")
configfile = os.path.join(config.config_dir(), confuse.CONFIG_FILENAME)


def save_config():
    with open(configfile, 'w', encoding='utf-8') as fh:
        fh.write(config.dump())
