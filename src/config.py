import logging

logging.basicConfig(
    level=logging.INFO,
    format=r"%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("logger.log"),
    ]
)
