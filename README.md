# MinIO 对象存储的自动备份脚本，支持目录和数据库
# pip安装指南:pip/pip3 install minio
# MinIO 快速入门指南: https://docs.min.io/cn/minio-quickstart-guide.html
# MinIO PythonAPI: https://docs.min.io/cn/python-client-api-reference.html
# 本脚本使用之前，推荐安装宝塔面板，并且按照实际情况填写#参数
# 使用方法:
#python myminio.py site bucket_name backup_name /backup_path keep_newest_copies
#Example: python myminio.py site testbucket mywebsite /backup 5
