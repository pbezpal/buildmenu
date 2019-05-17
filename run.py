#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os,subprocess
import tempfile,shutil
import yaml,jinja2
import pathlib
import argparse
import requests
import jenkinsapi
import time
import git
from jenkinsapi.jenkins import Jenkins
from jinja2 import Template
from datetime import datetime

script_dir = os.path.realpath(os.path.dirname(sys.argv[0]))

parser = argparse.ArgumentParser()
conf_file = script_dir+'/config/project_list.yml'
work_dir = os.getcwd()
electron_version = '4.0.3'
src_dir = '/tmp/sources'
jenkins_host = 'http://10.10.199.31:8080'
config = yaml.load(open(conf_file))
username = 'shavlovskiy_sn'
token = '110afafd6a5bbe698b1e69a37390daaafd'
jenkins = Jenkins(jenkins_host, username=username, password=token)
projects = []
for project in config:
    projects.append(project['app']['name'])

parser.add_argument('-n', '--name', nargs='*',  choices=projects, default=None)
parser.add_argument('-b', '--branch', nargs='*', default=None)
parser.add_argument('-t', '--tag', nargs='*', default=None)
parser.add_argument('-nj', '--nojenkins', nargs='?', default=False)
parser.add_argument('-nw', '--nowait', nargs='?', default=False)
parser.add_argument('-l', '--list', nargs='?', default=False)

namespace = parser.parse_args()

def getSelfConfig():
    config_git_url = 'ssh://shavlovskiy_sn@10.10.199.35/opt/git/ormp_builds'
    pathlib.Path(script_dir+'/config').mkdir(parents=True,exist_ok=True)
    t = tempfile.mkdtemp()
    git.Repo.clone_from(config_git_url, t, branch='master', depth=1)
    shutil.move(os.path.join(t, 'config/project_list.yml'), os.path.join(script_dir,'config/project_list.yml'))
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
    for index, item in enumerate(tags):
        print(str(index+1)+": "+item)
    tag_number = int(input("Введите порядковый номер тега:"))
    if tags[tag_number-1] == 'HEAD':
        selectBranch(project)
    else:
        project['git']['branch'] = 'refs/tags/'+tags[tag_number-1]
            
def getProjectBranch(branch=None):
    for project in config:
        if project['app']['name'] == branch:
                return str(project['app']['git']['branch'])

def getProjectTag(tag=None):
    for project in config:
        if project['app']['name'] == tag:
                return str(project['app']['git']['tag'])

def build(project):

    if namespace.nojenkins == False:
        print('Задача отправлена на Jenkins', jenkins_host)
        parameters={"GIT_URL":project['git']['url'], "BRANCH":project['git']['branch'], "BUILD_CMD":project['buildCmd']}
        # jenkins.build_job('build', parameters)
        # job = jenkins['build']
        job = jenkins.get_job('build')
        qi = job.invoke(build_params=parameters)
        if qi.is_queued() or qi.is_running():
            # qi.block_until_complete()
            if namespace.nowait == False:
                print('Ожидание завершения сборки...')
                jenkinsapi.api.block_until_complete(jenkinsurl=jenkins_host, jobs = ['build'], maxwait=7200, interval=30, raise_on_timeout=False, username=username, password=token)
        # build = qi.get_build()
        build = job.get_last_build()
        print(build)
    else:
        print('Локальная сборка (не Jenkins) ещё не реализована.')
        #os.system("build.py")

def getSources(project):
    shell("rm -rf "+src_dir)
    shell("git clone "+project['git']['url']+" "+src_dir+"/"+project['name'])
    os.chdir(src_dir+"/"+project['name'])
    return
            
def getBranches():
    branches = shell("git branch -a").decode("utf8").split("\n")
    branches.pop()
    return branches

def selectBranch(project):
    branches = getBranches()
    for index, item in enumerate(branches):
        print(str(index+1)+": "+item.replace("remotes/origin/",""))
    branch_index = int(input("Выберите ветку (введите номер): "))-1
    branch = branches[branch_index].replace("remotes/origin/","").replace('*', '').strip()
    return branch

def makeProject(project=None):
    if namespace.branch == None and namespace.tag == None:
        getSources(project)
        selectTag(project)
    elif not namespace.branch == None:
        project['git']['branch'] = namespace.branch
    elif not namespace.tag == None:
        project['git']['branch'] = '/refs/tags/'+namespace.tag
    build(project)
    
def selectProject(project=None):
    if not project == None:
        makeProject(project)
    else:
        print("\r\nСписок проектов:\r\n")
        for i ,name in enumerate(projects):
            i += 1
            print(str(i)+".", name)
        print("\r\n")
        if namespace.list == False:
            project_index = int(input("Выберите проект (введите номер): "))-1
            project = config[project_index]['app']
            makeProject(project)
        else:
            exit(0)


if namespace.name:
    selectProject(filterProjects(namespace.name[0])[0]['app'])
else:
    selectProject()