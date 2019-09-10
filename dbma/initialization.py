"""
实现自动初始化 dbm-agent 相关的功能
1、创建用户
2、创建用户组
3、创建相应的目录
"""

import os
import sys
import pwd
import grp
import time
import dbma
import shutil
import logging
import argparse
import subprocess
import contextlib
import configparser
import logging.handlers

# exit 1

# 初始化时使用如下日志格式


@contextlib.contextmanager
def sudo(message="sudo"):
    """# sudo 上下文
    提升当前进程的权限到 root 以完成特定的操作，操作完成后再恢复权限
    """
    # 得到当前进程的 euid 
    old_euid = os.geteuid()
    # 提升权限到 root
    os.seteuid(0)
    yield message
    # 恢复到普通权限
    os.seteuid(old_euid)

def is_user_exists(user_name:str)->bool:
    """
    检查操作系统上面是否存在 user_name 变量指定的用户
    """
    try:
        pwd.getpwnam(user_name)
        return True
    except KeyError as err:
        pass
    return False

def is_root()->bool:
    """
    检查当前的 euser 是不是 rot
    """
    return os.geteuid() == 0

def create_user(user_name:str)->bool:
    """
    创建 user_name 给定的用户
    """
    try:
        with sudo(f"create user {user_name} and user group {user_name}"):
            logging.info(f"groupadd {user_name}")
            subprocess.run(f"groupadd {user_name}",shell=True)
            subprocess.run(f"useradd {user_name} -g {user_name} ",shell=True)
    except Exception as err:
        logging.error(f"an exception been tiggered in create usere stage. {str(err)}")
        logging.error(f"{type(err)}")

def get_uid_gid(user_name):
    """
    返回给定用户的 (uid,gid) 组成的元组.
    如果用户不存在就返回 None
    """
    try:
        user = pwd.getpwnam(user_name)
        return user.pw_uid,user.pw_gid
    except KeyError as err:
        # 当给定的用户不存在的话会报 KeyError
        return None

def init(args):
    """
    完成所有 dbm-agent 初始化的逻辑
    1、创建用户
    2、创建工作目录 (/usr/local/dbm-agent)
    3、创建配置文件 (/usr/local/dbm-agent/etc/dbma.cnf)
    """
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",level=logging.DEBUG)
    
    # 检查用户是不是 root 不是的话就直接退出
    if not is_root():
        logging.error("mast use root user to execute this program. sudo su; dbam-agent init ")
        sys.exit(1)
    # 检查用户 dbma 用户是否存在，如果不存在就创建它
    if not is_user_exists(args.user_name):
        logging.info(f" user '{args.user_name}' not exists going to create it ")
        create_user(args.user_name)

    # 检查工作目录是否存在，不存在就创建它 /usr/local/dbm-agent/
    if not os.path.isdir(args.base_dir):
        logging.info(f"create dir {args.base_dir}")
        os.mkdir(args.base_dir)
        os.mkdir(os.path.join(args.base_dir,'etc'))
        os.mkdir(os.path.join(args.base_dir,'pkg'))
        os.mkdir(os.path.join(args.base_dir,'logs'))

    # 增加默认配置文件
    cnf = os.path.join(args.base_dir,'etc/dbma.cnf')
    logging.info(f"create config file '{cnf}' ")
    parser = configparser.ConfigParser(allow_no_value=True,inline_comment_prefixes='#')
    parser['dbma'] = {k:v for k,v in args.__dict__.items() if k != 'action'}
    with open(cnf,'w') as cnf:
        parser.write(cnf)

    # 复制 MySQL 配置文件模板
    pkg_dir = os.path.join(os.path.dirname(dbma.__file__),'static/cnfs')
    shutil.copytree(pkg_dir,os.path.join(args.base_dir,'etc/templates'))

    # 修改 /usr/local/dbm-agent 目录的权限
    if is_user_exists(args.user_name):
        subprocess.run(["chown","-R",f"{args.user_name}:{args.user_name}",args.base_dir ])


    







    

    




