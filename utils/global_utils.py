import os

ROOT_DIR= os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/"
CONFIG_DIR= ROOT_DIR + "config/"
DATA_DIR= ROOT_DIR + "data/"
CACHE_DIR= ROOT_DIR + "cache/"
STRING_DIR= CONFIG_DIR + "strings/"
PERMS_DIR= CONFIG_DIR + "perms/"
COG_CONFIG_DIR= CONFIG_DIR + "cog_configs/"

BOT_CONFIG_FILE= CONFIG_DIR + "bot_config.json"

HELP_STRING_FILE= STRING_DIR + "help.yaml"
ERROR_STRING_FILE= STRING_DIR + "errors.yaml"
COG_STRING_FILE= STRING_DIR + "cog_descriptions.yaml"
PPRINT_STRING_FILE= STRING_DIR + "pprint.yaml"
NAME_STRING_FILE= STRING_DIR + "cog_command_names.yaml"

GLOBAL_PERMS_FILE= PERMS_DIR + "00globals.yaml"

AUCTION_CONFIG= COG_CONFIG_DIR + "auction_config.yaml"
AUCTION_FILE= DATA_DIR + "auc_data.json"

SUPER_DIR= CACHE_DIR + "super/"
SUPER_HTML_DIR= SUPER_DIR + "html/"
SUPER_CACHE_FILE= SUPER_DIR + "cache.json"
SUPER_EQUIP_FILE= SUPER_DIR + "equips.json"
SUPER_ITEM_FILE= SUPER_DIR + "items.json"