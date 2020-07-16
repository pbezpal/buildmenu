#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os,subprocess
import os
import sys
import re
import tempfile,shutil
import jinja2
import yaml
import pathlib
import argparse
import hashlib
import getpass
import requests
import jenkins,jenkinsapi
import time
import git
import calendar
from jenkinsapi.jenkins import Jenkins
from jinja2 import Template
from datetime import datetime
from time import sleep

try:
    import spur
except ImportError:
    print('Lib spur not find, installing...')
    os.system('pip3 install spur')

"""Lib for run shell commands"""
import spur
"""Requests patch for fix readtimeout exception"""
import requests

def request_patch(slf, *args, **kwargs):
    timeout = kwargs.pop('timeout', 100)
    return slf.request_orig(*args, **kwargs, timeout=timeout)

setattr(requests.sessions.Session, 'request_orig', requests.sessions.Session.request)
requests.sessions.Session.request = request_patch

script_dir = os.path.realpath(os.path.dirname(sys.argv[0]))



parser = argparse.ArgumentParser()
conf_file = script_dir+'/config/project_list.yml'
work_dir = os.getcwd()
electron_version = '4.0.3'
src_dir = '/tmp/sources'
jenkins_host = 'http://10.10.199.31:8080'
config = yaml.safe_load(open(conf_file, 'r', encoding='utf8'))
config_users = yaml.safe_load(open("./config/users.yml", 'r', encoding='utf8'))
parser_user = argparse.ArgumentParser()

users = []
for user in config_users:
    users.append(user['user']['name'])

parser_user.add_argument('-n', '--name', nargs='*',  choices=users, default=None)
parser_user.add_argument('-u', '--username', nargs='*', default=None)
parser_user.add_argument('-p', '--passwird', nargs='*', default=None)
parser_user.add_argument('-t', '--token', nargs='*', default=None)
parser_user.add_argument('-l', '--list', nargs='?', default=False)

nameuser = parser_user.parse_args()

def filterUsers(users):
    if not users == None:
        users_config = list(filter(lambda x: x['user']['name'] in users, config_users))
        return users_config
    else:
        return config_users

if not nameuser.name == None:
    users = filterUsers(nameuser.name)

def userSelected(user=None):
    password=hashlib.md5(getpass.getpass("Enter password: ").encode("utf-8")).hexdigest()
    if(password == user['password']):
        global username
        username = user['username']
        global token
        token = user['token'][::-1]
    else:
        print("Wrong password")
        exit(0)


def selectUsers(user=None):
    while True:
        print("\r\nList users:\r\n")
        for index ,name in enumerate(users):
            print(str(index+1)+".", name)
        print("\nq: Quit")
        print("\r\n")
        if nameuser.list == False:
            user_index = input("Select user (type number): ")
            if user_index.isnumeric():
                user_index = int(user_index)-1
                if user_index == 1 or user_index <= index:
                    user = config_users[user_index]['user']
                    userSelected(user)
                    break
            elif user_index == 'q':
                exit(0)

if nameuser.name:
    selectUsers(filterUsers(nameuser.name[0])[0]['user'])
else:
    selectUsers()

jenkins_main = Jenkins(jenkins_host, username=username, password=token)
jenkins_helper = jenkins.Jenkins(jenkins_host, username=username, password=token)

projects = []
for project in config:
    projects.append(project['app']['name'])

parser.add_argument('-n', '--name', nargs='*',  choices=projects, default=None)
parser.add_argument('-b', '--branch', nargs='*', default=None)
parser.add_argument('-t', '--tag', nargs='*', default=None)
parser.add_argument('-nj', '--nojenkins', nargs='?', default=False)
parser.add_argument('-nw', '--nowait', nargs='?', default=False)
parser.add_argument('-l', '--list', nargs='?', default=False)
parser.add_argument('-T', '--test', nargs='?', default=False)

namespace = parser.parse_args()

"""Get configs for build"""
def getSelfConfig():
    config_git_url = 'ssh://shavlovskiy_sn@10.10.199.35/opt/git/ormp_builds'
    pathlib.Path(script_dir+'/config').mkdir(parents=True, exist_ok=True)
    pathlib.Path(script_dir+'/config').chmod(0o777)
    t = tempfile.mkdtemp()
    git.Repo.clone_from(config_git_url, t, branch='master', depth=1)
    shutil.move(os.path.join(t, 'config/project_list.yml'), os.path.join(script_dir,'config/project_list.yml'))
    shutil.move(os.path.join(t, 'config/builder-centos/jenkins_job_pipeline.xml'), os.path.join(script_dir,'config/builder-centos/jenkins_job_pipeline.xml'))
    shutil.move(os.path.join(t, 'config/builder-centos/jenkins_job_test.xml'), os.path.join(script_dir,'config/builder-centos/jenkins_job_test.xml'))
    shutil.move(os.path.join(t, 'config/builder-debian/jenkins_job.xml'), os.path.join(script_dir,'config/builder-debian/jenkins_job.xml'))
    shutil.move(os.path.join(t, 'config/builder-debian/jenkins_job_client_pipeline.xml'), os.path.join(script_dir,'config/builder-debian/jenkins_job_client_pipeline.xml'))
    shutil.rmtree(t)

getSelfConfig()


def filterProjects(projects):
    if not projects == None:
        projects_config = list(filter(lambda x: x['app']['name'] in projects, config))
        return projects_config
    else:
        return config

if not namespace.name == None:
    projects = filterProjects(namespace.name)

def shell(command):
    p = subprocess.Popen(['/bin/bash -c "'+command+'"'], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()

def getProjectUrl(name=None):
    for project in config:
        if project['app']['name'] == name:
                return str(project['app']['git']['url'])

def getTags():
    tags = shell("git tag ").decode("utf8").split("\n")
    return tags

def selectTag(project):
    tags = getTags()
    if not tags[len(tags)-1]:
        tags.pop()
    tags.append('HEAD')
    while True:
        for index, item in enumerate(tags):
            print(str(index+1)+": "+item)
        print("\nq: Quit")
        tag_number = input("Select tag (type number): ")
        if tag_number.isnumeric():
            tag_number = int(tag_number)
            if tag_number == 1 or tag_number <= index:
                project['git']['tag'] = tags[tag_number-1]
                if project['git']['tag'] == 'HEAD':
                    project['git']['branch'] = selectBranch(project)
                else:
                    project['git']['branch'] = 'refs/tags/'+project['git']['tag']
                break
        elif tag_number == 'q':
            exit(0)

def getProjectBranch(branch=None):
    for project in config:
        if project['app']['name'] == branch:
                return str(project['app']['git']['branch'])

def getProjectTag(tag=None):
    for project in config:
        if project['app']['name'] == tag:
                return str(project['app']['git']['tag'])

"""This method create job with parameters and monitoring status job"""
def build(project):
    if namespace.nojenkins == False:
        """Deleting roschat-node-module for copy new version to server build docker"""
        if project['name'] == 'roschat-server':
            shell = spur.SshShell(hostname="10.10.199.47", username="root", password="nimda123",missing_host_key=spur.ssh.MissingHostKey.accept)
            shell.run(["sh", "-c","rm -f /tmp/rpms/roschat-node-modules-*"])
        if project['name'] == 'roschat-client':
            jenkins_job = open(script_dir+'/config/builder-'+project['buildMachine']+'/jenkins_job_client_pipeline.xml', 'r').read()
        elif namespace.test:
            jenkins_job = open(script_dir+'/config/builder-'+project['buildMachine']+'/jenkins_job_test.xml', 'r').read()
        else:
            jenkins_job = open(script_dir+'/config/builder-'+project['buildMachine']+'/jenkins_job_pipeline.xml', 'r').read()
        print('Job sent to Jenkins', jenkins_host)
        if not project['name'] == 'roschat-client':
            print("\r\nList type build:\r\n")
            print("1. Develop")
            print("2. Pre-Release")
            print("3. Release")
            print("\nq: Quit")
            while True:
                type_build = input("Select type build: ")
                if type_build.isnumeric():
                    type_build = int(type_build)
                    if type_build == 1:
                        build_type = 'develop'
                        break
                    elif type_build == 2:
                        build_type = 'pre-release'
                        break
                    elif type_build == 3:
                        build_type = 'release'
                        break
                elif type_build == 'q':
                    exit(0)
            parameters = {
                "PROJECT_NAME": project['name'],
                "GIT_URL": project['git']['url'],
                "BRANCH": project['git']['branch'],
                "BUILD_CMD": project['buildCmd'],
                "BUILD_MACHINE": project['buildMachine'],
                "VERSION": re.sub(r'e', '', project['git']['tag']),
                "TYPE": project['type'],
                "BUILD_TIME": datetime.now().strftime('%d.%m.%Y_%H:%M'),
                "BUILD_TYPE": build_type
            }
        else:
            print("\r\nList type build:\r\n")
            print("1. Develop")
            print("2. Release")
            print("\nq: Quit")
            while True:
                type_build = input("Select type build: ")
                if type_build.isnumeric():
                    type_build = int(type_build)
                    if type_build == 1:
                        build_type = 'develop'
                        break
                    elif type_build == 2:
                        build_type = 'release'
                        break
                elif type_build == 'q':
                    exit(0)
            parameters = {
                "PROJECT_NAME": project['name'],
                "GIT_URL": project['git']['url'],
                "BRANCH": project['git']['branch'],
                "BUILD_CMD": project['buildCmd'],
                "BUILD_MACHINE": project['buildMachine'],
                "VERSION": re.sub(r'e', '', project['git']['tag']),
                "TYPE": project['type'],
                "BUILD_TIME": datetime.now().strftime('%d.%m.%Y_%H:%M'),
                "BUILD_TYPE": build_type
            }
        print(project['git']['branch'])
        if not jenkins_helper.job_exists(project['name']):
            jenkins_helper.create_job(project['name'], jenkins_job)
        else:
            jenkins_helper.reconfig_job(project['name'], jenkins_job)
        job = jenkins_main.get_job(project['name'])
        """Transmit parameters to build job"""
        job.invoke(build_params=parameters)
        try:
            last_build_number = job.get_last_buildnumber()
        except:
            last_build_number = 0
        point = 1
        """Monitoring status job"""
        while True:
            try:
                build_number = job.get_last_buildnumber()
            except:
                build_number = 0
            if last_build_number != build_number:
                break
            sys.stdout.write("\r" + "Waiting for build " + project['name'] + " to start" + "." * point)
            sleep(2)
            point += 1
            sys.stdout.flush()
        print("\n")
        build_info = jenkins_helper.get_build_info(project['name'], build_number)
        print("Build number: " + str(build_number) + "\n")
        while True:
            persent = round((int(str(calendar.timegm(time.gmtime())) + "000") - int(build_info['timestamp'])) / int(build_info['estimatedDuration']) * 100)
            if (persent == 100 or persent > 100):
               break
            space = 100 - persent
            sys.stdout.write("\r" + "Complete [" + str(persent) + "% " + "=" * persent + ">" + " " * space + "]")
            sleep(5)
            sys.stdout.flush()
        sys.stdout.write("\b\r" + "Complete [100% " +  "=" * 100 + ">]\n")
        sys.stdout.flush()
        result = jenkins_helper.get_build_info(project['name'], build_number)
        if result['result'] != 'SUCCESS':
            print("\n" + jenkins_helper.get_build_console_output(project['name'], build_number))
        else:
            print("\nResult build: " + result['result'])
    else:
        print('Local build not implemented yet')

def getSources(project):
    shell("rm -rf "+src_dir)
    pathlib.Path(src_dir+"/"+project['name']).mkdir(parents=True, exist_ok=True)
    pathlib.Path(src_dir).chmod(0o777)
    pathlib.Path(src_dir+"/"+project['name']).chmod(0o777)
    shell("git clone "+project['git']['url']+" "+src_dir+"/"+project['name'])
    os.chdir(src_dir+"/"+project['name'])
    return

def getBranches():
    branches = shell("git branch -a").decode("utf8").split("\n")
    branches.pop()
    return branches

def selectBranch(project):
    branches = getBranches()
    while True:
        for index, item in enumerate(branches):
            print(str(index+1)+": "+item.replace("remotes/origin/",""))
        print("\nq: Quit")
        branch_index = input("Select branch (type number): ")
        if branch_index.isnumeric():
            branch_index = int(branch_index)-1
            if branch_index == 1 or branch_index <= index:
                branch = branches[branch_index].replace("remotes/origin/","").replace('*', '').strip()
                print(branch)
                return branch
        elif branch_index == 'q':
            exit(0)

def makeProject(project=None):
    if namespace.branch == None and namespace.tag == None:
        getSources(project)
        selectTag(project)
    elif not namespace.branch == None:
        project['git']['branch'] = namespace.branch
    elif not namespace.tag == None:
        project['git']['tag'] = namespace.tag[0]
        project['git']['branch'] = 'refs/tags/'+project['git']['tag']
    build(project)

def selectProject(project=None):
    if not project == None:
        makeProject(project)
    else:
        while True:
            print("\r\nProjects list:\r\n")
            for i ,name in enumerate(projects):
                print(str(i+1)+".", name)
            print("\nq: Quit")
            print("\r\n")
            if namespace.list == False:
                project_index = input("Select project (type number): ")
                if project_index.isnumeric():
                    project_index = int(project_index)-1
                    if project_index == 1 or project_index <= i:
                        project = config[project_index]['app']
                        makeProject(project)
                        break
                elif project_index == 'q':
                    exit(0)

if namespace.name:
    selectProject(filterProjects(namespace.name[0])[0]['app'])
else:
    selectProject()
