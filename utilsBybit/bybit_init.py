import json
from classes.Asset import AssetThorchain, AssetBybit, AssetMaya


def createAssetsFromJSON(asset_class):
    file_path = f"constantes/myAssets/{asset_class.__name__}.json"
    with open(file_path, 'r') as file:
        json_data = json.load(file)

    assets = []
    for key, value in json_data.items():
        # Initialize a dictionary for constructor arguments
        init_args = {}

        # Get all the constructor argument names, excluding 'self'
        arg_names = asset_class.__init__.__code__.co_varnames[1:asset_class.__init__.__code__.co_argcount]

        for field in arg_names:
            if field in value:
                # Add the fields present in the JSON
                init_args[field] = value[field]
            else:
                # Provide None or some default value if the field is missing
                # You can customize the default value as per your class design
                init_args[field] = None

        # Create an instance of the class with the collected arguments
        asset = asset_class(**init_args)
        assets.append(asset)

    return assets

