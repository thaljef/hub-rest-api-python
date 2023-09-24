#!/usr/bin/env python

'''
Copyright (C) 2023 Synopsys, Inc.
http://www.blackducksoftware.com/

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements. See the NOTICE file
distributed with this work for additional information
regarding copyright ownership. The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the
specific language governing permissions and limitations
under the License.
'''

import argparse
import json
import logging
import sys

from blackduck import Client

parser = argparse.ArgumentParser("Remove direct access to project")
parser.add_argument("-u", "--base-url",                        required=True,  help="Hub server URL e.g. https://your.blackduck.url")
parser.add_argument("-t", "--token-file", dest='token_file',   required=True,  help="containing access token")
parser.add_argument("--no-verify",        dest='verify', action='store_false', help="Disable TLS certificate verification")
parser.add_argument("--project",          dest='project_name', required=True,  help="Project name")
parser.add_argument("--user",             dest='user_name',    required=True,  help="User name")

args = parser.parse_args()


logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("blackduck").setLevel(logging.WARNING)

with open(args.token_file, 'r') as tf:
    access_token = tf.readline().strip()

bd = Client(
    base_url=args.base_url,
    token=access_token,
    verify=args.verify
)

params = {'q': [f"name:{args.project_name}"]}
projects = [p for p in bd.get_resource('projects', params=params) if p['name'] == args.project_name]
assert len(projects) == 1, f"There should be one, and only one project named {args.project_name}. We found {len(projects)}"
project_url = projects[0]["_meta"]["href"]

params  = {'q': [f"entityName:{args.user_name}"]}
headers = {'Accept' : 'application/vnd.blackducksoftware.internal-1+json'}
user    = bd.get_json(f"{project_url}/users", params=params, headers=headers)

assert user["totalCount"] != 0, f"User {args.user_name} is not a member of project {args.project_name}"
assert user["items"][0]["isDirect"] == True, f"User {args.user_name} does not have direct access to project {args.project_name}"

user_url=user["items"][0]["_meta"]["links"][0]["href"]
bd.session.delete(user_url)
