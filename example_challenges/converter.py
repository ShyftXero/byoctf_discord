import json
import toml
import yaml


import fire


def to_yaml(inFile, outFile):
    """converts toml to yaml"""
    try:
        obj = toml.loads(open(inFile).read())
        with open(outFile, "w") as out:
            out.write(yaml.dump(obj))
    except yaml.YAMLError as e:
        print("error in yaml")
    except toml.TomlDecodeError as e:
        print("error in toml")
    except BaseException as e:
        print(e)


def to_toml(inFile, outFile):
    """Converts a json challenge in to toml"""

    try:
        obj = json.loads(open(inFile).read())
        with open(outFile, "w") as out:
            out.write(toml.dumps(obj))
    except json.JSONDecodeError as e:
        print("error in json")
    except toml.TomlDecodeError as e:
        print("error in toml")
    except BaseException as e:
        print(e)


def to_json(inFile, outFile):
    """Converts a toml challenge in to json"""
    try:
        obj = toml.loads(open(inFile).read())
        with open(outFile, "w") as out:
            out.write(json.dumps(obj))
    except json.JSONDecodeError as e:
        print("error in json")
    except toml.TomlDecodeError as e:
        print("error in toml")
    except BaseException as e:
        print(e)


if __name__ == "__main__":
    fire.Fire()
