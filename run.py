#!/usr/bin/python
# coding=UTF-8

import os
import subprocess
import sys
import pymysql.cursors
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

host1 = cfg['db1']['host']
user1 = cfg['db1']['user']
password1 = cfg['db1']['password']
dbName1 = cfg['db1']['db']

host2 = cfg['db2']['host']
user2 = cfg['db2']['user']
password2 = cfg['db2']['password']
dbName2 = cfg['db2']['db']

tableList1 = []
tableList2 = []
tableList3 = []

git_remote = 'git@github.com:dkben/diff-db.git'


try:
    connections = {
        'conn1': pymysql.connect(host=host1,
                                 user=user1,
                                 password=password1,
                                 db=dbName1,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor),
        'conn2': pymysql.connect(host=host2,
                                 user=user2,
                                 password=password2,
                                 db=dbName2,
                                 charset='utf8',
                                 cursorclass=pymysql.cursors.DictCursor),
    }
except pymysql.err.OperationalError as e:
    print("Error: 資料庫連線異常...")
    sys.exit()


def get_tables1():
    cursor1.execute("SHOW TABLES")
    tables = cursor1.fetchall()
    for table in tables:
        tableList1.append(table["Tables_in_" + dbName1])


def get_tables2():
    cursor2.execute("SHOW TABLES")
    tables = cursor2.fetchall()
    for table in tables:
        tableList2.append(table["Tables_in_" + dbName2])


def get_tables3():
    global tableList1, tableList2, tableList3
    tableList3 = sorted(list(set(tableList1) & set(tableList2)))


def diff(first, second):
    second = set(second)
    return [item for item in first if item not in second]


def get_columns(db, table_name):
    if db == "db1":
        cursor1.execute("SHOW columns FROM " + table_name)
        columns = cursor1.fetchall()
    elif db == "db2":
        cursor2.execute("SHOW columns FROM " + table_name)
        columns = cursor2.fetchall()
    column_list = []
    for column in columns:
        column_list.append(column["Field"] + ":" + column["Type"])
    return column_list


def get_diff_table_column():
    for table in tableList3:
        column1 = get_columns("db1", table)
        column2 = get_columns("db2", table)
        diff1 = sorted(list(set(column1) - set(column2)))
        diff2 = sorted(list(set(column2) - set(column1)))
        if len(diff1) > 0 or len(diff2) > 0:
            print("資料表：", table)
            # print("DB1:", column1)
            # print("DB2:", column2)
            print("============================================================")
            print("DB1 - DB2:", diff1)
            print("============================================================")
            print("DB2 - DB1:", diff2)
            print("============================================================")


def check_update():
    check = str(input('是否檢查更新？y 檢查更新 / n 繼續...[y/n]:'))
    if check == 'y':
        print('檢查更新中...')
        local_hash = subprocess.check_output('git log --pretty="%h" -n1 HEAD'.split()).decode()[1:8]
        remote_hash = subprocess.check_output(
            ('git ls-remote %s HEAD' % git_remote).split()).decode()[0:7]
        print(local_hash, remote_hash)
        if local_hash != remote_hash:
            skip = str(input('有新版程式，請 git pull 更新...，按 y 繼續 / n 離開程式...[y/n]:'))
            if skip == 'n':
                sys.exit()
        else:
            input('已經是最新版...按任意鍵繼續...')


def main():
    print("============================================================")
    check_update()
    get_tables1()
    get_tables2()
    get_tables3()
    print("============================================================")
    print("資料表數量比較")
    # print("DB1：", tableList1)
    # print("DB2: ", tableList2)
    print("DB1:", len(tableList1), "(張), DB2:", len(tableList2), "(張)")
    # print(set(tableList1) - set(tableList2))
    # print(set(tableList2) - set(tableList1))
    print("DB1 - DB2 =", diff(tableList1, tableList2))
    print("DB2 - DB1 =", diff(tableList2, tableList1))
    print("============================================================")
    print("============================================================")
    print("============================================================")
    print("雙方資料表內容比較，只比較雙方都有的資料表")
    print(len(tableList3), "(張)")
    print("============================================================")
    get_diff_table_column()
    print("比對結束")


if __name__ == '__main__':
    try:
        with connections["conn1"].cursor() as cursor1, connections["conn2"].cursor() as cursor2:
            main()
    finally:
        connections["conn1"].close()
        connections["conn2"].close()
