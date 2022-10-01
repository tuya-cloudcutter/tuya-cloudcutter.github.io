# Copyright (c) Kuba Szczodrzyński 2022-09-30.

import json
from glob import glob
from os import makedirs, unlink
from os.path import basename, join


def load_all(path: str) -> dict[str, dict]:
    out = {}
    for file in glob(join(path, "*.json")):
        with open(file, "r") as f:
            data = json.load(f)
        slug = basename(file)[:-5]
        out[slug] = data
    return out


def clean_dir(path: str):
    for file in glob(join(path, "*.json")):
        unlink(file)


def write_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f)


def put_list(obj: dict, key: str):
    if key not in obj:
        obj[key] = []


def sort_list(obj: dict, key: str):
    obj[key] = sorted(obj[key])


DIR_OUTPUT = "site"
DIR_DEVICES = join(DIR_OUTPUT, "devices")
DIR_PROFILES = join(DIR_OUTPUT, "profiles")
IMAGES_URL = "https://tuya-cloudcutter.github.io/cloudcutter-data/images"

makedirs(DIR_DEVICES, exist_ok=True)
makedirs(DIR_PROFILES, exist_ok=True)
clean_dir(DIR_DEVICES)
clean_dir(DIR_PROFILES)

devices = load_all("devices/")
profiles = load_all("profiles/")
base_devices = []
base_profiles = []


def get_base_device(device: dict) -> dict:
    out = dict(
        slug=device["slug"],
        manufacturer=device["manufacturer"],
        name=device["name"],
    )
    if device.get("image_url", None):
        out["image_url"] = device["image_url"]
    return out


def get_base_profile(profile: dict) -> dict:
    out = dict(
        slug=profile["slug"],
        name=profile["name"],
        type=profile["type"],
    )
    if profile.get("icon", None):
        out["icon"] = profile["icon"]
    return out


# add slug names to objects
for slug, device in devices.items():
    device["slug"] = slug

for slug, profile in profiles.items():
    profile["slug"] = slug


# create and assign base objects
for slug, device in devices.items():
    # assign default image URL
    if device["image_urls"]:
        device["image_url"] = device["image_urls"][0]
    # prepend local image URLs with repo URL
    for i, url in enumerate(device["image_urls"]):
        if url.startswith("https://") or url.startswith("http://"):
            continue
        device["image_urls"][i] = f"{IMAGES_URL}/{url}"
        if i == 0:
            device["image_url"] = f"{IMAGES_URL}/thumbs/{url}"

    # add missing empty lists
    put_list(device, "github_issues")
    put_list(device, "image_urls")
    put_list(device, "profiles")
    # get profile objects
    device_profiles = [profiles[p_slug] for p_slug in device["profiles"]]
    # set base profiles
    device["profiles"] = [get_base_profile(profile) for profile in device_profiles]
    # store base device object
    base_devices.append(get_base_device(device))
    # save full device object
    sort_list(device, "github_issues")
    write_json(join(DIR_DEVICES, f"{slug}.json"), device)

    # fill profiles with assigned devices, and their related GH issues
    for profile in device_profiles:
        if "devices" not in profile:
            profile["devices"] = []
        if "github_issues" not in profile:
            profile["github_issues"] = []
        profile["devices"].append(slug)
        profile["github_issues"] += device["github_issues"]

for slug, profile in profiles.items():
    # add missing empty lists
    put_list(profile, "github_issues")
    put_list(profile, "devices")
    # get device objects
    profile_devices = [devices[d_slug] for d_slug in profile["devices"]]
    # set base devices
    profile["devices"] = [get_base_device(device) for device in profile_devices]
    # store base profile object
    base_profiles.append(get_base_profile(profile))
    # save full profile object
    sort_list(profile, "github_issues")
    write_json(join(DIR_PROFILES, f"{slug}.json"), profile)

# write base object lists
write_json(join(DIR_OUTPUT, "devices.json"), base_devices)
write_json(join(DIR_OUTPUT, "profiles.json"), base_profiles)
