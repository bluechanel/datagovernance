import datetime
import logging
import os

from flask import Flask, render_template, jsonify, request, send_from_directory
import pandas as pd
import webbrowser

app = Flask(__name__)


def judge(col1, col2):
    return "一致" if col1 == col2 else "不一致"


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('data', filename)


def allowed_file(file_name: str):
    return '.' in file_name and file_name.rsplit('.', 1)[1] in ['xlsx', 'xls']


def clean(path: str, dup_col: list[str], na_col: list[str]) -> list[str]:
    """
    数据清洗函数
    :param na_col:
    :param dup_col:
    :param path:
    :return:
    """
    result1_name = f"重复_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"空字段_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result3_name = f"清洗完成_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data = pd.read_excel(path)
    # 重复  根据卡号去重
    data_duplicates = data.drop_duplicates(subset=dup_col, keep=False)
    result1_data = pd.merge(data, data_duplicates, how='outer', on="卡号", indicator=True).query(
        '_merge == "left_only"').drop(
        columns=['_merge'])
    # 有空值  所有字段空值判断
    tmp_data = data.loc[:, na_col]
    n = tmp_data.isnull().any(axis=1)
    # == 是因为这里是numpy
    m = n[n == True].index
    result2_data = data[data.index.isin(m)]
    result3_data = data.drop_duplicates(subset=dup_col, keep='first')
    result3_data = result3_data.dropna(subset=na_col)
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    result3_data.to_excel(f'data/{result3_name}')
    return [result1_name, result2_name, result3_name]


def finance(path1: str, path2: str) -> list[str]:
    """
    信息账单表合并函数
    :param path1:info
    :param path2:bill
    :return:
    """
    result1_name = f"账单中不在系统的卡_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"卡号一致明细表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result3_name = f"系统中不在账单卡_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    # 交集
    result1_data = pd.merge(data1, data2, how='inner', on="卡号")
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on="卡号", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result3_data = pd.merge(data1, data2, how='outer', on="卡号", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    result3_data.to_excel(f'data/{result3_name}')
    return [result1_name, result2_name, result3_name]


def ledger(path1: str, path2: str, col: str) -> list[str]:
    """
    信息台账表合并函数
    :param col:
    :param path1: info
    :param path2: ledger
    :return:
    """
    if col == "IP":
        result1_name = f"信息台账差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        result2_name = f"台账信息差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        result3_name = f"台账信息交集拼接_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    else:
        result1_name = f"表1表2差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        result2_name = f"表2表1差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        result3_name = f"表1表2交集拼接_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    # 交集
    result1_data = pd.merge(data1, data2, how='outer', on=col, indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on=col, indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result3_data = pd.merge(data1, data2, how='inner', on=col)
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')
    result3_data.to_excel(f'data/{result3_name}')
    return [result1_name, result2_name, result3_name]


def diff(path1: str, path2: str) -> list[str]:
    result1_name = f"费用一致表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    result2_name = f"费用不一致表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    merge_data = pd.merge(data1, data2, how='outer', on="卡号")
    print(merge_data)
    merge_data["说明"] = merge_data.apply(lambda x: judge(x.费用_x, x.费用_y), axis=1)
    print(merge_data)
    result1_data = merge_data[merge_data['说明'] == '一致']
    result2_data = merge_data[merge_data['说明'] == '不一致']
    result1_data.to_excel(f'data/{result1_name}')
    result2_data.to_excel(f'data/{result2_name}')

    return [result1_name, result2_name]


@app.post('/data_clean')
def clean_route():
    r = request.get_json()
    dup_col = r["dup_col"].split(",")
    na_col = r["na_col"].split(",")
    result_name = clean(r["path"], dup_col, na_col)
    return jsonify({"filename": result_name})


@app.post('/finance')
def finance_route():
    r = request.get_json()
    result_name = finance(r["path1"], r["path2"])
    return jsonify({"filename": result_name})


@app.post('/ledger')
def ledger_route():
    r = request.get_json()
    result_name = ledger(r["path1"], r["path2"], "IP")
    return jsonify({"filename": result_name})


@app.post('/merge')
def merge_route():
    r = request.get_json()
    result_name = ledger(r["path1"], r["path2"], r["col"])
    return jsonify({"filename": result_name})


@app.post('/diff')
def diff_route():
    r = request.get_json()
    result_name = diff(r["path1"], r["path2"])
    return jsonify({"filename": result_name})


def mkdir(dirs: str):
    if not os.path.exists(dirs):
        os.makedirs(dirs)


def main():
    logging.warning("请不要在使用该工具时关闭当前命令行窗口！")
    logging.warning("使用浏览器访问http://127.0.0.1:5000")
    webbrowser.open_new_tab("http://127.0.0.1:5000")
    app.run()


if __name__ == '__main__':
    main()
