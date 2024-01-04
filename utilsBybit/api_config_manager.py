import json

# Chemin vers le fichier de configuration
CONFIG_FILE = "utilsBybit/api_config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        print(f"Le fichier de configuration '{CONFIG_FILE}' n'a pas été trouvé.")
        return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file, indent=4)

def update_api_key(new_api_key):
    config = load_config()
    config["api_key"] = new_api_key
    save_config(config)

def update_api_secret(new_api_secret):
    config = load_config()
    config["api_secret"] = new_api_secret
    save_config(config)
