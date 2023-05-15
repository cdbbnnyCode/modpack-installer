import argparse


parser = argparse.ArgumentParser(description="Copy options file from one pack to another.")
parser.add_argument(
    "copy_file",
    action="store",
    type=str,
    help="The options file which should be copied.",
)
parser.add_argument(
    "paste_file",
    action="store",
    type=str,
    help="The options file which should be pasted.",
)
args = parser.parse_args()


def get_data(file):
    with open(file, "r") as f:
        keys = []
        values = []
        for line in f.readlines():
            key, value = line.rstrip().split(":")
            keys.append(key)
            values.append(value)
        return keys, values


def write_data(keys, values, file):
    if len(keys) != len(values):
        raise ValueError(
            "The given keys and values don't match in length!", keys, values
        )

    with open(file, "w") as f:
        f.writelines(["{}:{}\n".format(keys[i], values[i]) for i in range(len(keys))])


def search_and_replace(file_to_copy, file_to_paste):
    copy_keys, copy_values = get_data(file_to_copy)
    paste_keys, paste_values = get_data(file_to_paste)

    assert len(copy_values) == len(copy_values)
    assert len(paste_keys) == len(paste_values)

    for i, copy_key in enumerate(copy_keys):
        for j, paste_key in enumerate(paste_keys):
            if copy_key == paste_key:
                paste_values[j] = copy_values[i]
                break

    return paste_keys, paste_values


def main(file_to_copy, file_to_paste):
    keys, values = search_and_replace(file_to_copy, file_to_paste)
    print(keys, values)
    write_data(keys, values, file_to_paste)


if __name__ == "__main__":
    main(args.copy_file, args.paste_file)
