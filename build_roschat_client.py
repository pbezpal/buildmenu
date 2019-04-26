#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import pathlib
#reload(sys)
#sys.setdefaultencoding("utf-8")
import os
import subprocess
import yaml
from jinja2 import Template

# if len(sys.argv) < 2:
cwd = sys.argv[1]
conf_file = cwd+'/roschat.yml'
# else:
# conf_file = sys.argv[3]

os.chdir(cwd)

config = yaml.load(open(conf_file))
prev_full_version = config['app']['version']
prev_build_version = str(prev_full_version).split('.')[2]
cur_build_version = str(int(prev_build_version)+1)
major_version = prev_full_version.split('.')[0]
minor_version = prev_full_version.split('.')[1]

cur_full_version = major_version+'.'+minor_version+'.'+cur_build_version

# cwd = os.getcwd()
# src_dir = os.getcwd()+"/git_sources"
src_dir = sys.argv[2]

print("Начинаю сборку "+config['app']['name']+" v"+cur_full_version)

def shell(command):
    p = subprocess.Popen(['/bin/bash -c "'+command+'"'], stdout=subprocess.PIPE, shell=True)
    return p.stdout.read()


# electron_version = "1.6.16"
# electron_version = "2.0.10"
electron_version = "4.0.3"

def prepareBuild(tag=""):
    if tag == "":
        tag = cur_full_version
    else:
        tag = tag+'.'+cur_build_version
    config['app']['version'] = tag
    config['app']['name'] = config['app']['name']
    with open(conf_file, 'w') as of:
        yaml.dump(config, of, default_flow_style=False, allow_unicode=True)
    # shell("mkdir "+src_dir+"/clients/demo/js/electron/config/ && cp ./roschat.yml "+src_dir+"/clients/demo/js/electron/config/default.yml")
    buildDeps(tag)
    
def buildDeps(tag):
    shell("cd "+src_dir+"/clients/demo && yarn install && gulp")
    shell("rm -rf "+src_dir+"/clients/demo/dist/resources/app")
    # shell("mkdir -p "+src_dir+"/clients/demo/dist/resources/app/config")
    pathlib.Path(src_dir+"/clients/demo/js/electron/config/").mkdir(parents=True, exist_ok=True)
    shell("cp "+cwd+"/roschat.yml "+src_dir+"/clients/demo/js/electron/config/default.yml")
    # tpl = open('./resources/app/package.json.tpl').read()
    template = Template(open(cwd+'/resources/app/package.json.tpl').read())
    package_json = template.render({'appname': config['app']['name'], 'tag': tag})
    pathlib.Path(src_dir+"/clients/demo/dist/resources/app/").mkdir(parents=True, exist_ok=True)
    with open(src_dir+"/clients/demo/dist/resources/app/package.json", "w") as of:
        of.write(package_json)
    shell("cp -r "+src_dir+"/clients/demo/{dist,js/electron/dist}")
    with open(src_dir+"/clients/demo/js/electron/package.json", "w") as of:
        of.write(package_json)
    shell("cd "+src_dir+"/clients/demo/js/electron/ && yarn install")
    if config['app']['platforms']['rpm'] or config['app']['platforms']['deb']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . RosChat --overwrite --platform=linux --arch=x64 --icon "+src_dir+"/clients/demo/js/electron/img/Roschat_color_64x64.png --prune=true --out="+src_dir+"/../amd64 --electronVersion "+electron_version)
    if config['app']['platforms']['windows']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . "+config['app']['name']+" --overwrite --platform win32 --arch x64 --icon "+src_dir+"/clients/demo/js/electron/img/roschat5.ico --out "+src_dir+"/../win32  --electronVersion "+electron_version)
    if config['app']['platforms']['macos']:
       shell("cd "+src_dir+"/clients/demo/js/electron/ && electron-packager . --overwrite --platform=darwin --arch=x64 --icon "+src_dir+"/clients/demo/js/electron/img/roschat5.png.icns --prune=true --out="+cwd+"/../darwin --electronVersion="+electron_version+" "+config['app']['name'])
    build(tag)

def build(tag):
   if config['app']['platforms']['rpm']:
      shell("cd "+src_dir+"/../amd64  &&  echo 'IIIIIIIIIIIIIIIII' && pwd && electron-installer-redhat --src  RosChat-linux-x64/ --dest "+cwd+"/../setup/rpm/ --arch x86_64 --config "+src_dir+"/clients/demo/js/electron/config.json")
   if config['app']['platforms']['deb']:
      shell("cd "+src_dir+"/../amd64 && electron-installer-debian --src  RosChat-linux-x64/ --dest "+cwd+"/../setup/deb/ --arch amd64 --config "+src_dir+"/clients/demo/js/electron/config.json")
   os.chdir(cwd)
   shell('ansible-playbook '+cwd+'/build.yml -e \"deb=false rpm=false windows='+str(config['app']['platforms']['windows'])+' macos='+str(config['app']['platforms']['macos'])+' local_src_dir='+src_dir+' electron_version='+electron_version+' appname='+config['app']['name']+' tag='+tag+'"')

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
    
# def chooseBranch():
#     branches = getBranches()
#     if not config['app']['git']['branch']:
#         for index, item in enumerate(branches):
#             print(str(index+1)+": "+item)
#         branch_num = int(input("Введите порядковый номер ветки:"))
#         branch = branches[branch_num-1]
#         if affirm(branch):
#             setBranch(branch)
#             # chooseAction(branch)
#             prepareBuild()
#         else:
#             chooseBranch()
#     else:
#         setBranch(config['app']['git']['branch'])
#         prepareBuild()
prepareBuild()
# getSources()
# chooseBranch()
# chooseTag(getTags())
