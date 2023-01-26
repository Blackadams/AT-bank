import logging

# create a logger for post requests
post_logger = logging.getLogger('post_logger')
post_logger.setLevel(logging.INFO)
# create a file handler for the post logger
file_handler = logging.FileHandler('logs/post_requests.log')
file_handler.setLevel(logging.INFO)
# create a formatter and set it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
# add the file handler to the post logger
post_logger.addHandler(file_handler)

# create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# create a file handler
file_handler = logging.FileHandler("logs/errors.log")
file_handler.setLevel(logging.ERROR)

# create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# add the file handler to the logger
logger.addHandler(file_handler)