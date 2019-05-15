#!/usr/bin/env python3

import sys
import argparse
import os.path
import configparser
import requests
import pickle
import json

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

def authenticate_compute(profile):
    url = profile["compute_endpoint"]+ "/authenticate/"
    payload  = "{\n \"password\": \"" + profile["password"] + "\",\n \"user\": \"/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "\"\n}"
    headers = {"Content-Type": "application/oracle-compute-v3+json"}
    response = requests.request("POST", url, data=payload, headers=headers)
    if response.status_code != 204:
        print("failed to authenticate")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        return response.cookies

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
        return response.headers["X-Auth-Token"]

def list_ipreservation(profile, cookiejar):
    url = profile["compute_endpoint"] + "/network/v1/ipreservation/Compute-" + profile["identity_domain"] + "/"
    headers = {"Content-Type": "application/oracle-compute-v3+json", "Accept": "application/oracle-compute-v3+json"}
    response = requests.request("GET", url, headers=headers, cookies=cookiejar)
    if response.status_code != 200:
        print("failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        for ipres in response.json()["result"]:
            print('name: {0:90}  IP: {1:20}  pool: {2:20}'.format(ipres["name"], str(ipres["ipAddress"]), ipres["ipAddressPool"]))

def storage_object_exist(profile, storage_token, objectname):
    # checking if object exists in Storage
    url = profile["storage_endpoint"] + "/v1/Storage-" + profile["identity_domain"] + "/compute_images/" + objectname
    headers = {"Accept": "application/json", "X-Auth-Token": storage_token}
    response = requests.head(url, headers=headers)
    if response.status_code == 404:
        return False
    elif response.status_code == 200:
        return True
    else:
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(2)

def machineimage_exist(profile, cookiejar, imagename):
    # checking if machineimage exists and create it if it does not
    url = profile["compute_endpoint"] + "/machineimage/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "/" + imagename
    headers = {"Content-Type": "application/oracle-compute-v3+json", "Accept": "application/oracle-compute-v3+json"}
    response = requests.request("GET", url, headers=headers, cookies=cookiejar)
    if response.status_code == 200:
        print("machineimage exists")
        return True
    elif response.status_code == 404:
        print("machineimage does not exist")
        return False

    else:
        print("failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(3)

def list_image(profile, cookiejar):
    url = profile["compute_endpoint"] + "/imagelist/Compute-" + profile["identity_domain"] + "/"
    headers = {"Content-Type": "application/oracle-compute-v3+json", "Accept": "application/oracle-compute-v3+json"}
    response = requests.request("GET", url, headers=headers, cookies=cookiejar)
    if response.status_code != 200:
        print("failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        for image in response.json()["result"]:
            print('imagelist: {0:110} \t\t default version: {1:2}'.format(image["name"], image["default"]))
            for image_entry in image["entries"]:
                print('\t machineimage: ', end='')
                for machineimage in image_entry["machineimages"]:
                    print('{0:110} '.format(machineimage), end='')
                print('\t version: {0:2}'.format(image_entry["version"]))

def create_machineimage(profile, cookiejar, imagename, objectname):
    url = profile["compute_endpoint"] + "/machineimage/Compute-" + profile["identity_domain"] + "/" + profile[
        "user"] + "/" + imagename
    headers = {
                "Content-Type": "application/oracle-compute-v3+json",
                "Accept": "application/oracle-compute-v3+json"
              }
    payload = json.dumps({
                "name": "/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "/" + imagename,
                "sizes": {"total":0},
                "no_upload": True,
                "account": "/Compute-" + profile["identity_domain"] + "/cloud_storage",
                "file": objectname,
                "platform": "windows"
              })
    print(url)
    print(headers)
    print(payload)
    response = requests.request("POST", url, headers=headers, data=payload, cookies=cookiejar)
    if response.status_code != 201:
        print("machineimage creation failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        print("machineimage created")

def create_imagelist(profile, cookiejar, imagename):
    url = profile["compute_endpoint"] + "/imagelist/Compute-" + profile["identity_domain"] + "/" + profile[
        "user"] + "/" + imagename
    headers = {
                "Content-Type": "application/oracle-compute-v3+json",
                "Accept": "application/oracle-compute-v3+json"
              }
    payload = {
                "name": "/Compute-" + profile["identity_domain"] + " / " + profile["user"] + "/" + imagename,
                "description": imagename
              }
    response = requests.request("POST", url, headers=headers, data=payload, cookies=cookiejar)
    if response.status_code != 200:
        print("imagelist  creation failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        print("imagelist created")

def create_imagelist_entry(profile, cookiejar, imagename, version):
    url = profile["compute_endpoint"] + "/imagelist/Compute-" + profile["identity_domain"] + "/" + profile[
        "user"] + "/" + imagename + "/entry/"
    headers = {
                "Content-Type": "application/oracle-compute-v3+json",
                "Accept": "application/oracle-compute-v3+json"
              }
    payload = {
                "machineimages": ["/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "/" + imagename],
                "version": version
              }
    response = requests.request("POST", url, headers=headers, data=payload, cookies=cookiejar)
    if response.status_code != 200:
        print("imagelist entry creation failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)
        sys.exit(1)
    else:
        print("imagelist entry created")

def create_image(profile, cookiejar, storage_token, imagename, objectname):
    if storage_object_exist(profile, storage_token, objectname):
        print("storage object exists")
    else:
        print("storage object does not exist")
        sys.exit(1)
    if machineimage_exist(profile, cookiejar, imagename):
        print("machineimage exists")
    else:
        print("machineimage does not exist")
        create_machineimage(profile, cookiejar, imagename, objectname)
    # checking if imagelist exists and create it if it does not
    url = profile["compute_endpoint"] + "/imagelist/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "/" + imagename
    headers = {"Content-Type": "application/oracle-compute-v3+json", "Accept": "application/oracle-compute-v3+json"}
    response = requests.request("GET", url, headers=headers, cookies=cookiejar)
    if response.status_code == 200:
        print("imagelist exists")
        latest_version = 0
        for image_entry in response.json()["entries"]:
            if image_entry["version"] > latest_version:
                latest_version = image_entry["version"]
            if image_entry["machineimages"][0] == "/Compute-" + profile["identity_domain"] + "/" + profile["user"] + "/" + imagename:
                print("machineimage is already part of the imagelist as version " + str(image_entry["version"]))
                sys.exit(5)
        next_version = latest_version + 1
        create_imagelist_entry(profile, cookiejar, imagename, next_version)
    elif response.status_code == 404:
        print("imagelist does not exist")
        create_imagelist(profile, cookiejar, imagename)
    else:
        print("failed")
        print("req status code: " + str(response.status_code))
        print("req response text: " + response.text)


######## MAIN #########
def main(argv):
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-p", "--profile", action="store", nargs='?', default="./default.cfg")
    main_parser = argparse.ArgumentParser()
    service_subparsers = main_parser.add_subparsers(title="service", dest="service")
    auth_parser = service_subparsers.add_parser("auth", help="auth", parents=[parent_parser])
    image_parser = service_subparsers.add_parser("image", help="image", parents=[parent_parser])
    image_command_subparser = image_parser.add_subparsers(title="image_command", dest="command")
    image_list_parser = image_command_subparser.add_parser("list", help="list", parents=[parent_parser])
    image_create_parser = image_command_subparser.add_parser("create", help="create", parents=[parent_parser])
    image_create_parser.add_argument("imagename", action='store', help="image name")
    image_create_parser.add_argument("objectname", action='store', help="object name")
    image_create_parser.add_argument("--platform", action='store', choices=['linux','windows'], help="windows or linux", default="linux")
    image_delete_parser = image_command_subparser.add_parser("delete", help="delete", parents=[parent_parser])
    image_delete_parser.add_argument("imagename", action='store', help="image name")

    args = main_parser.parse_args()
    print(args)
    if os.path.isfile(args.profile):
        profile = read_profile(args.profile)
    else:
        print("Profile file is not found: " + args.profile)
        sys.exit()
    compute_cookie_jar = authenticate_compute(profile)
    storage_token = authenticate_storage(profile)

    if args.service == "auth":
        with open("./compute-cookie", 'wb') as f:
            pickle.dump(compute_cookie_jar, f)
        print("Compute cookie is saved as ./compute-cookie")
        with open("./storage-token", 'w+') as f:
            f.write(storage_token)
        print("Storage token is saved as ./storage-token")
    elif args.service == "image":
        if args.command == 'list':
            list_image(profile, compute_cookie_jar)
        elif args.command == 'create':
            print("creating image {0} from storage object {1}...".format(args.imagename, args.objectname))
            create_image(profile, compute_cookie_jar, storage_token, args.imagename, args.objectname)
        elif args.command == 'delete':
            print("deleting image {0} ...".format(args.imagename))
        else:
            image_parser.print_help()
    else:
        main_parser.print_help()

if __name__ == "__main__":
    main(sys.argv[1:])
