#!/usr/bin/env python
# coding: utf-8


import platform
import sys
import os


# ouput system type and version info
import logging




def init_logger(log_name, log_file):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.FileHandler(log_file)
    ch.setLevel(logging.ERROR)

    ch2 = logging.StreamHandler()
    ch2.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #ch.setFormatter(formatter)
    #ch2.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(ch2)

    return logger

def out_put_system_info(logger):
    logger.info("platform.machine()=%s", platform.machine())
    logger.info("platform.node()=%s", platform.node())
    logger.info("platform.platform()=%s", platform.platform())
    logger.info("platform.processor()=%s", platform.processor())
    logger.info("platform.python_build()=%s", platform.python_build())
    logger.info("platform.python_compiler()=%s", platform.python_compiler())
    logger.info("platform.python_branch()=%s", platform.python_branch())
    logger.info("platform.python_implementation()=%s", platform.python_implementation())
    logger.info("platform.python_revision()=%s", platform.python_revision())
    logger.info("platform.python_version()=%s", platform.python_version())
    logger.info("platform.python_version_tuple()=%s", platform.python_version_tuple())
    logger.info("platform.release()=%s", platform.release())
    logger.info("platform.system()=%s", platform.system())
    # logging.info("platform.system_alias()=%s", platform.system_alias());
    logger.info("platform.version()=%s", platform.version())
    logger.info("platform.uname()=%s", platform.uname())

def main():
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.log")
    log_name = "simple_example"
    logger = init_logger(log_name, log_file)
    out_put_system_info(logger)
    return True

if __name__ == "__main__":
    sys.exit(0) if main() else sys.exit(1)