#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
import sys,os,time,re
reload(sys)
sys.setdefaultencoding('utf-8')
from minio import Minio
from minio.error import ResponseError
import urllib3

# MinIO 对象存储的自动备份脚本，支持目录和数据库
# pip安装指南:pip/pip3 install minio
# MinIO 快速入门指南: https://docs.min.io/cn/minio-quickstart-guide.html
# MinIO PythonAPI: https://docs.min.io/cn/python-client-api-reference.html
# 本脚本使用之前，推荐安装宝塔面板，并且按照实际情况填写#参数
# 使用方法:
#python myminio.py site bucket_name backup_name /backup_path keep_newest_copies
#Example: python myminio.py site testbucket mywebsite /backup 5


def ReadFile(filename,mode = 'r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename): return False
    try:
        fp = open(filename, mode)
        f_body = fp.read()
        fp.close()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode,encoding="utf-8")
                f_body = fp.read()
                fp.close()
            except Exception as ex2:
                WriteLog('打开文件',str(ex2))
                return False
        else:
            WriteLog('打开文件',str(ex))
            return False
    return f_body

def readFile(filename,mode='r'):
    return ReadFile(filename,mode)

def WriteFile(filename,s_body,mode='w+'):
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

def writeFile(filename,s_body,mode='w+'):
    return WriteFile(filename,s_body,mode)

def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    import shlex
    import datetime
    import subprocess
    import time

    if shell:
        cmdstring_list = cmdstring
    else:
        cmdstring_list = shlex.split(cmdstring)
    if timeout:
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    
    sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,shell=shell,bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    
    while sub.poll() is None:
        time.sleep(0.1)
        if timeout:
            if end_time <= datetime.datetime.now():
                raise Exception("Timeout：%s"%cmdstring)
            
    return sub.communicate()

class minioapi:
    # 参数
    server     = "YOUR MINIO SERVER:9000"                               # MinIO服务器地址
    secret_id  = "YOUR ACCESS KEY"                      # 用户的access_key
    secret_key = "YOUR SECRET KEY"  # 用户的secret_key
    mysql_usr  = "root"                                      # MySQL用户名
    mysql_pass = "ROOT PASSWORD"                          # MySQL密码
    bucket = None
    client = None
    isSSL = False

    __error_count = 0
    __error_msg = "ERROR: 无法连接到 MinIO，请检查参数设置是否正确!"
    __bucket_path = "/"

    def __init__(self, _bucket="default"):
        self.client = Minio(self.server,
                            access_key=self.secret_id,
                            secret_key=self.secret_key,
                            secure=self.isSSL);
        self.bucket = _bucket

    # 同步时间
    def sync_date(self):
        ExecShell("ntpdate 0.asia.pool.ntp.org");

    # 获取所有桶
    def list_bucket(self):
        try:
            buckets = self.client.list_buckets()
            for bucket in buckets:
                print(bucket.name, bucket.creation_date)
        except Exception, ex:
            return "";

    # 获取某个桶内所有文件或前缀为_prefix的文件
    def list_file(self, _prefix=''):
        try:
            # List all object paths in bucket that begin with my-prefixname.
            data = [];
            objects = self.client.list_objects(self.bucket, prefix=_prefix, recursive=True)
            for obj in objects:
                #print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
                #      obj.etag, obj.size, obj.content_type)
                tmp = {}
                tmp['bucket_name'] = obj.bucket_name
                tmp['size'] = obj.size
                tmp['content_type'] = obj.content_type
                tmp['etag'] = obj.etag
                tmp['last_modified'] = obj.last_modified
                tmp['object_name'] = obj.object_name.encode('utf-8')
                data.append(tmp)
            mlist = {}
            mlist['list'] = data;
            #print(mlist);
            return mlist;
        except Exception, ex:
            return "";

    # 创建目录
    def create_bucket(self, bucket_name):
        try:
            self.client.make_bucket(self.bucket, location=bucket_name)
        except ResponseError as err:
            print(err)

    # 上传文件
    def upload_file(self, filename, local_path):
        try:
            print(self.client.fput_object(self.bucket, filename, local_path))
        except ResponseError as err:
            print(err)
            
    # 上传文件到某个目录
    def upload_file_in_folder(self, folder, filename, local_path):
        try:
            print(self.client.fput_object(self.bucket, folder + "/" + filename, local_path))
        except ResponseError as err:
            print(err)

    # 下载文件
    def download_file(self, filename, local_path):
        try:
            print(self.client.fget_object(self.bucket, filename, local_path))
        except ResponseError as err:
            print(err)

    # 删除文件
    def delete_file(self, filename):
        # Remove an object.
        try:
            self.client.remove_object(self.bucket, filename)
        except ResponseError as err:
            print(err)

    # 删除多个文件
    def delete_files(self, filenames):
        # Remove multiple objects in a single library call.
        try:
            # objects_to_delete = ['SQLQuery1.sql1', 'SQLQuery2.sql1', 'SQLQuery3.sql1']
            # force evaluation of the remove_objects() call by iterating over
            # the returned value.
            for del_err in self.client.remove_objects(self.bucket, filenames):
                print("Deletion Error: {}".format(del_err))
        except ResponseError as err:
            print(err)

    # 清理多余的备份文件
    def delete_backup(self, _prefix = "", count = 5):
        list = self.list_file(_prefix)["list"];
        list.sort(key=lambda x: x["last_modified"]);
        #print(list)
        #print str(len(list))
        for i in range(0, len(list) - count):
            self.delete_file(list[i]["object_name"]);
            print("|---已清理过期备份文件：" + list[i]["object_name"])

    # 备份网站
    def backupSite(self, name, path, count):
        prefix = "Web_" + name + "_"
        folder = 'Website_' + name
        filename = prefix + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        ExecShell("cd " + os.path.dirname(path) + " && tar zcvf /root/'" + filename + "' '" + os.path.basename(
            path) + "' > /dev/null")

        # 上传文件
        self.upload_file_in_folder(folder, filename, "/root/" + filename);
        # 清理本地文件
        ExecShell("rm -f /root/" + filename)
        # 清理多余备份
        self.delete_backup(folder + '/' + prefix, count);

        return None

    # 备份数据库
    def backupDatabase(self, name, dbname, count):
        prefix = "Db_" + name + "_"
        folder = 'Db_' + name
        filename = prefix + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"

        import re
        mycnf = readFile('/etc/my.cnf');
        rep = "\[mysqldump\]\nuser=" + self.mysql_usr
        sea = '[mysqldump]\n'
        subStr = sea + "user=" + self.mysql_usr + "\npassword=" + self.mysql_pass + "\n";
        mycnf = mycnf.replace(sea, subStr)
        if len(mycnf) > 100:
            writeFile('/etc/my.cnf', mycnf);

        ExecShell("/www/server/mysql/bin/mysqldump --opt --default-character-set=utf8 " + dbname + " | gzip > /root/" + filename)

        mycnf = readFile('/etc/my.cnf');
        mycnf = mycnf.replace(subStr, sea)
        if len(mycnf) > 100:
            writeFile('/etc/my.cnf', mycnf);


        # 上传文件
        self.upload_file_in_folder(folder, filename, filename);
        # 清理本地文件
        ExecShell("rm -f /root/" + filename)
        # 清理多余备份
        self.delete_backup(folder + '/' + prefix, count);

        return None

    # 取目录路径
    def get_path(self, path):
        if path == '/': path = '';
        if path[:1] == '/':
            path = path[1:];
            if path[-1:] != '/': path += '/';
        return path;


if __name__ == "__main__":
    import json

    data = None
    _type = sys.argv[1];
    _bucket = sys.argv[2];
    _name = sys.argv[3];
    _path = sys.argv[4];
    _count = int(sys.argv[5]);
    m = minioapi(_bucket);
    if _type == 'site':
        data = m.backupSite(_name, _path, _count);
        exit()
    elif _type == 'database':
        data = m.backupDatabase(_name, _path, _count);
        exit()
    else:
        data = 'ERROR: 参数不正确!';

    #print(json.dumps(data));