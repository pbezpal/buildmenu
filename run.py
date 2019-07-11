#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os,subprocess
import re
import tempfile,shutil
import yaml,jinja2
import pathlib
import argparse
import requests
import jenkins,jenkinsapi
import time
import git
from jenkinsapi.jenkins import Jenkins
from jinja2 import Template
from datetime import datetime

# Requests patch for fix readtimeout exception
import requests

def request_patch(slf, *args, **kwargs):
    # print("Fix called")
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
config = yaml.safe_load(open(conf_file))
username = 'shavlovskiy_sn'
# token = '110afafd6a5bbe698b1e69a37390daaafd'
token = '113e520c92adf331cee8df264326529ceb'
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
# parser.add_argument('-bn', '--buildnumber', nargs='?', default=False)

namespace = parser.parse_args()

def getSelfConfig():
    config_git_url = 'ssh://shavlovskiy_sn@10.10.199.35/opt/git/ormp_builds'
    pathlib.Path(script_dir+'/config').mkdir(parents=True, exist_ok=True).chmod(0o777)
    t = tempfile.mkdtemp()
    git.Repo.clone_from(config_git_url, t, branch='master', depth=1)
    shutil.move(os.path.join(t, 'config/project_list.yml'), os.path.join(script_dir,'config/project_list.yml'))
    shutil.move(os.path.join(t, 'config/builder-centos/jenkins_job.xml'), os.path.join(script_dir,'config/builder-centos/jenkins_job.xml'))
    shutil.move(os.path.join(t, 'config/builder-debian/jenkins_job.xml'), os.path.join(script_dir,'config/builder-debian/jenkins_job.xml'))
    shutil.move(os.path.join(t, 'config/builder-debian/jenkins_job_roschat-client.xml'), os.path.join(script_dir,'config/builder-debian/jenkins_job_roschat-client.xml'))
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
    project['git']['tag'] = tags[tag_number-1]
    if project['git']['tag'] == 'HEAD':
        project['git']['branch'] = selectBranch(project)
    else:
        project['git']['branch'] = 'refs/tags/'+project['git']['tag']
            
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
        if project['name'] == 'roschat-client':
            jenkins_job_config = open(script_dir+'/config/builder-'+project['buildMachine']+'/jenkins_job_roschat-client.xml', 'r')
        else:
            jenkins_job_config = open(script_dir+'/config/builder-'+project['buildMachine']+'/jenkins_job.xml', 'r')
        jenkins_job = jenkins_job_config.read()
        print('Задача отправлена на Jenkins', jenkins_host)
        parameters={"GIT_URL":project['git']['url'], "BRANCH":project['git']['branch'], "BUILD_CMD":project['buildCmd'],"BUILD_MACHINE": project['buildMachine'], "VERSION":re.sub(r'e', '', project['git']['tag']), "TYPE":project['type'], "BUILD_TIME": datetime.now().strftime('%d.%m.%Y_%H:%M')}
        print(project['git']['branch'])
        # jenkins.build_job('build', parameters)
        if not jenkins_helper.job_exists(project['name']):
            jenkins_helper.create_job(project['name'], jenkins_job)
        else:
            jenkins_helper.reconfig_job(project['name'], jenkins_job)
        job = jenkins_main.get_job(project['name'])
        # if namespace.buildnumber:
        #     jenkins_helper.set_next_build_number(project['name'], int(namespace.buildnumber))
        qi = job.invoke(build_params=parameters)
        if qi.is_queued() or qi.is_running():
            # qi.block_until_complete()
            if namespace.nowait == False:
                print('Ожидание завершения сборки...')
                try:
                    jenkinsapi.api.block_until_complete(jenkinsurl=jenkins_host, jobs = [project['name']], maxwait=7200, interval=60, raise_on_timeout=False, username=username, password=token)
                except Exception:
                    jenkinsapi.api.block_until_complete(jenkinsurl=jenkins_host, jobs = [project['name']], maxwait=7200, interval=120, raise_on_timeout=False, username=username, password=token)
        build_number = job.get_last_completed_buildnumber()
        result = jenkins_helper.get_build_info(project['name'], build_number)
        if result['result'] == 'FAILURE':
            print(jenkins_helper.get_build_console_output(project['name'], build_number))
        else:
            print(result['result'])
    else:
        print('Локальная сборка (не Jenkins) ещё не реализована.')
        #os.system("build.py")

def getSources(project):
    shell("rm -rf "+src_dir)
    pathlib.Path(src_dir+"/"+project['name']).mkdir(parents=True, exist_ok=True).chmod(0o777)
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
    print(branch)
    return branch

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
