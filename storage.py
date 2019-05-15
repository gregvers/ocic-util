#!/usr/bin/env python3

import sys
import argparse
import os.path
import configparser
import requests

def read_profile(filename):
    profile = {}
    config = configparser.RawConfigParser()
    config.read(filename)
    profile["user"] = config.get('Account', 'user')
    profile["password"] = config.get('Account', 'password')
    profile["identity_domain"] = config.get('Account', 'identity_domain')
    profile["compute_endpoint"] = config.get('Account', 'compute_endpoint')
    profile["storage_endpoint"] = config.get('Account', 'storage_endpoint')
    return profile

def authenticate_storage(profile):
    url = profile["storage_endpoint"]+ "/auth/v1.0/"
    StorageUser = "Storage-" + profile["identity_domain"] + ":" + profile["user"]
    StoragePass = profile["password"]
    headers = {"X-Storage-User": StorageUser, "X-Storage-Pass": StoragePass}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("failed to authenticate")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        # return response.headers["X-Auth-Token"]
        return response.text

def list_containers(profile, auth_token):
    url = profile["storage_endpoint"] + "/v1/Storage-" + profile["identity_domain"] + "/"
    headers = {"Accept": "application/json", "X-Auth-Token": auth_token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        for container in response.json():
            print('name: {0:120}  count: {1:10}  MB: {2:15}'.format(container["name"], str(container["count"]), str(round(container["bytes"]/1024/1024))))

######## MAIN #########
def main(argv):
    argparser = argparse.ArgumentParser(prog='storage', usage='%(prog)s command [options]')
    argparser.add_argument("command", type=str, action='store', choices=['auth', 'list','create','delete','update'], help="command")
    argparser.add_argument("-p", "--profile", action="store", nargs='?', default="./default.cfg")
    args = argparser.parse_args()
    if os.path.isfile(args.profile):
        profile = read_profile(args.profile)
    else:
        print("Profile file is not found: " + args.profile)
        sys.exit()
    auth_token = authenticate_storage(profile)
    if args.command == "list":
        list_containers(profile, auth_token)
    elif args.command == "create":
        print("create")
    elif args.command == "delete":
        print("delete")
    elif args.command == "update":
        print("update")
    elif args.command == "auth":
        print(auth_token)


if __name__ == "__main__":
    main(sys.argv[1:])
