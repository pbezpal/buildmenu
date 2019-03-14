#!/usr/bin/python
import sys
import os
import subprocess
import yaml

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
src_dir = "./git_sources"

def shell(command):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
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
    with open(conf_file, 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
    buildDeps(tag)
    
def buildDeps(tag):
    shell("cd "+src_dir+"/clients/demo && yarn install && gulp")
    shell("mkdir "+src_dir+"/clients/demo/dist/resources/app")

    build(tag)

def build(tag):
    
    os.system('ansible-playbook build.yml -e \"local_src_dir='+src_dir+' electron_version='+electron_version+' tag='+tag+'"')

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
        build()
    else:
        chooseAction(branch)
    
def chooseTag(branch):
    tags = getTags(branch)
    for index, item in enumerate(tags):
        print(str(index+1)+": "+item)
    tag_num = int(input("Введите порядковый номер тега:"))
    if affirm(tags[tag_num-1]):
        setTag(tags[tag_num-1])
        build(tags[tag_num-1])
    
def chooseBranch():
    branches = getBranches()
    if not config['app']['git']['branch']:
        for index, item in enumerate(branches):
            print(str(index+1)+": "+item)
        branch_num = int(input("Введите порядковый номер ветки:"))
        branch = branches[branch_num-1].split('/')[2]
        if affirm(branch):
            setBranch(branch)
            # chooseAction(branch)
            build()
        else:
            chooseBranch()
    else:
        setBranch(config['app']['git']['branch'])
        build()

getSources()
chooseBranch()
# chooseTag(getTags())
