#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import subprocess
import yaml
from jinja2 import Template

if len(sys.argv) < 2:
   conf_file = './config.yml'
else:
    conf_file = sys.argv[1]    

config = yaml.load(open(conf_file))
prev_full_version = config['app']['version']
prev_build_version = str(prev_full_version).split('.')[2]
cur_build_version = str(int(prev_build_version)+1)
major_version = prev_full_version.split('.')[0]
minor_version = prev_full_version.split('.')[1]

cur_full_version = major_version+'.'+minor_version+'.'+cur_build_version

cwd = os.getcwd()
src_dir = os.getcwd()+"/git_sources"

print("Начинаю сборку "+config['app']['name']+" v"+cur_full_version)

def shell(command):
    p = subprocess.Popen(['/bin/bash -c "'+command+'"'], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()


# electron_version = "1.6.16"
# electron_version = "2.0.10"
electron_version = "4.0.3"

def getTags(branch=""):
    if branch == "":
        points = ""
    else:
        points = "--points-at "+branch
    os.chdir(src_dir)
    tags = shell("git tag "+points).decode("utf8").split("\n")
    os.chdir(cwd)
    tags.pop()
    return tags

def getBranches():
    os.chdir(src_dir)
    branches = shell("git branch -a").decode("utf8").split("\n")
    branches.pop()
    os.chdir(cwd)
    return branches
    
def getSources():
    shell("rm -rf "+src_dir)
    shell(config['app']['git']['url']+" "+src_dir)

def prepareBuild(tag=""):
    if tag == "":
        tag = cur_full_version
    else:
        tag = tag+'.'+cur_build_version
    config['app']['version'] = tag
    config['app']['name'] = config['app']['name']
    with open(conf_file, 'w') as of:
        yaml.dump(config, of, default_flow_style=False, allow_unicode=True)
    buildDeps(tag)
    
def buildDeps(tag):
    shell("cd "+src_dir+"/clients/demo && yarn install && gulp")
    shell("rm -rf "+src_dir+"/clients/demo/dist/resources/app")
    shell("mkdir -p "+src_dir+"/clients/demo/dist/resources/app")
    # tpl = open('./resources/app/package.json.tpl').read()
    template = Template(open('./resources/app/package.json.tpl').read())
    package_json = template.render({'appname': config['app']['name'], 'tag': tag})
    with open(src_dir+"/clients/demo/dist/resources/app/package.json", "w") as of:
        of.write(package_json)
    shell("cp -r "+src_dir+"/clients/demo/{dist,js/electron/dist}")
    with open(src_dir+"/clients/demo/js/electron/package.json", "w") as of:
        of.write(package_json)
    shell("cd "+src_dir+"/clients/demo/js/electron/ && yarn install")
    if config['app']['platforms']['rpm'] or config['app']['platforms']['deb']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . "+config['app']['name']+" --overwrite --asar --platform=linux --arch=x64 --icon "+src_dir+"/clients/demo/js/electron/img/rch_logo1_32x32.png --prune=true --out="+src_dir+"/../amd64 --electronVersion "+electron_version)
    if config['app']['platforms']['windows']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . "+config['app']['name']+" --overwrite --platform win32 --arch x64 --icon "+src_dir+"/clients/demo/js/electron/img/roschat5.ico --out "+src_dir+"/../win32  --electronVersion "+electron_version)
    if config['app']['platforms']['macos']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . --overwrite --platform=darwin --arch=x64 --icon "+src_dir+"/clients/demo/js/electron/img/roschat5.png.icns --prune=true --out="+src_dir+"/../darwin --electronVersion="+electron_version+" "+config['app']['name'])
    build(tag)

def build(tag):
    os.system('ansible-playbook build.yml -e \"deb='+str(config['app']['platforms']['deb'])+' rpm='+str(config['app']['platforms']['rpm'])+' windows='+str(config['app']['platforms']['windows'])+' macos='+str(config['app']['platforms']['macos'])+' local_src_dir='+src_dir+' electron_version='+electron_version+' appname='+config['app']['name']+' tag='+tag+'"')

def setBranch(branch):
    os.chdir(src_dir)
    print("switch to "+branch)
    b = shell("git checkout "+branch+" > /dev/null")
    os.chdir(cwd)
    
def setTag(tag):
    os.chdir(src_dir)
    shell("git checkout tags/"+tag+" > /dev/null")
    os.chdir(cwd)
    
def affirm(item):
    confirm = input("Выбрано "+item+". Продолжить?[да/нет](по умолчанию \"да\"):")
    if confirm == "yes" or confirm == "да" or confirm == "":
        return True
    elif not confirm == "yes" and not confirm == "да" and not confirm == "no" and not confirm == "нет":
        print("Введите <да|нет|yes|no> или оставьте строку пустой")
        affirm(item)
    elif confirm == "no" or confirm == "нет":
        return False

def chooseAction(branch):
    print("Ветка "+branch)
    print("1: Выбрать тег")
    print("2: Собрать")
    choose = int(input("Выберите действие:"));
    if choose == 1:
        chooseTag(branch)
    elif choose == 2:
        prepareBuild()
    else:
        chooseAction(branch)
    
def chooseTag(branch):
    tags = getTags(branch)
    for index, item in enumerate(tags):
        print(str(index+1)+": "+item)
    tag_num = int(input("Введите порядковый номер тега:"))
    if affirm(tags[tag_num-1]):
        setTag(tags[tag_num-1])
        prepareBuild(tags[tag_num-1])
    
def chooseBranch():
    branches = getBranches()
    if not config['app']['git']['branch']:
        for index, item in enumerate(branches):
            print(str(index+1)+": "+item)
        branch_num = int(input("Введите порядковый номер ветки:"))
        branch = branches[branch_num-1]
        if affirm(branch):
            setBranch(branch)
            # chooseAction(branch)
            prepareBuild()
        else:
            chooseBranch()
    else:
        setBranch(config['app']['git']['branch'])
        prepareBuild()

getSources()
chooseBranch()
# chooseTag(getTags())
