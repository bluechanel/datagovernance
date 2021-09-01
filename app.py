import datetime
import logging
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
import pandas as pd

app = Flask(__name__)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('data', filename)


def allowed_file(file_name: str):
    return '.' in file_name and file_name.rsplit('.', 1)[1] in ['xlsx', 'xls']


def clean(path: str) -> list[str]:
    """
    数据清洗函数
    :param path:
    :return:
    """
    result1_name = f"重复_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"空字段_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data = pd.read_excel(path)
    # 重复  根据id去重
    data_duplicates = data.drop_duplicates(subset=["卡号"], keep=False)
    result1_data = pd.merge(data, data_duplicates, how='outer', on="id", indicator=True).query(
        '_merge == "left_only"').drop(
        columns=['_merge'])
    # 有空值  所有字段空值判断
    n = data.isnull().any(axis=1)
    m = n[n is True].index
    result2_data = data[data.index.isin(m)]
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    return [result1_name, result2_name]


def finance(path1: str, path2: str) -> list[str]:
    """
    信息账单表合并函数
    :param path1:info
    :param path2:bill
    :return:
    """
    result1_name = f"信息账单交集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"账单信息差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    # 交集
    result1_data = pd.merge(data1, data2, how='inner', on="卡号")
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on="卡号", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])

    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    return [result1_name, result2_name]


def ledger(path1: str, path2: str) -> list[str]:
    """
    信息台账表合并函数
    :param path1: info
    :param path2: ledger
    :return:
    """
    result1_name = f"信息台账差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"台账信息差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    # 交集
    result1_data = pd.merge(data1, data2, how='outer', on="IP", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on="IP", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    return [result1_name, result2_name]


@app.post('/data_clean')
def clean_route():
    r = request.get_json()
    logging.info(str(r))
    result_name = clean(r["path"])
    return jsonify({"filename": f"{result_name}"})


@app.post('/finance')
def finance_route():
    r = request.get_json()
    logging.info(str(r))
    result_name = finance(r["path1"], r["path2"])
    return jsonify({"filename": result_name})


@app.post('/ledger')
def ledger_route():
    r = request.get_json()
    logging.info(str(r))
    result_name = ledger(r["path1"], r["path2"])
    return jsonify({"filename": result_name})


def mkdir(dirs: str):
    if not os.path.exists(dirs):
        os.makedirs(dirs)


if __name__ == '__main__':
    logging.warning("请不要在使用该工具时关闭当前命令行窗口！")
    logging.warning("使用浏览器访问http://127.0.0.1:5000")
    app.run()
