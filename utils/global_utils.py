import os

ROOT_DIR= os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/"
DATA_DIR= ROOT_DIR + "data/"
STRING_DIR= DATA_DIR + "strings/"

BOT_CONFIG_FILE= DATA_DIR + "bot_config.json"

HELP_STRING_FILE= STRING_DIR + "help.yaml"
ERROR_STRING_FILE= STRING_DIR + "errors.yaml"
COG_STRING_FILE= STRING_DIR + "cog_descriptions.yaml"