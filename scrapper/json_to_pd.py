import json
import pandas as pd
from typing import List

with open("../data/renting-bologna.json") as f:
    data = json.load(f)


def normalize_data(data: List[List[dict]]) -> List[dict]:
    normalized_data = []

    for nested_list in data:
        # Flatten the nested dictionaries into a single dictionary
        for item in nested_list:
            flattened_item = {}
            for sub_dict in item.values():
                if isinstance(sub_dict, dict):
                    for key, value in sub_dict.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                flattened_item[sub_key] = sub_value
                        else:
                            flattened_item[key] = value
                else:
                    flattened_item[key] = value

            normalized_data.append(flattened_item)

    return normalized_data


def create_dataframe(data: List[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)
