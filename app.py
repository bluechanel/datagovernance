import datetime
import logging
import os
from typing import Union, Any

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


def clean(path: str, dup_col: list[str], na_col: list[str]) -> Any:
    """
    数据清洗函数
    :param na_col:
    :param dup_col:
    :param path:
    :return:
    """
    result_name = f"数据清洗_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    writer = pd.ExcelWriter(f'data/{result_name}')

    # result1_name = f"重复_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    # result2_name = f"空字段_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    # result3_name = f"清洗完成_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data = pd.read_excel(path)
    msg = f"文件原始数据为：{len(data)}条；"
    # 重复  根据卡号去重
    if len(dup_col) > 0:
        data_duplicates = data.drop_duplicates(subset=dup_col, keep=False)
        result1_data = pd.merge(data, data_duplicates, how='outer', on="卡号", indicator=True).query(
            '_merge == "left_only"').drop(
            columns=['_merge'])
        result1_data.to_excel(writer, sheet_name="重复")
        msg += f"重复数据为：{len(result1_data)}条；"
    # 有空值  所有字段空值判断
    if len(na_col) > 0:
        tmp_data = data.loc[:, na_col]
        n = tmp_data.isnull().any(axis=1)
        # == 是因为这里是numpy
        m = n[n == True].index
        result2_data = data[data.index.isin(m)]
        result2_data.to_excel(writer, sheet_name="空字段")
        msg += f"空字段数据为：{len(result2_data)}条；"

    if len(dup_col) > 0 and len(na_col) < 1:
        result3_data = data.drop_duplicates(subset=dup_col, keep='first')
        result3_data.to_excel(writer, sheet_name="清洗完成")
        msg += f"清洗后数据为：{len(result3_data)}条；"
    if len(dup_col) < 1 and len(na_col) > 0:
        result3_data = data.dropna(subset=na_col)
        result3_data.to_excel(writer, sheet_name="清洗完成")
        msg += f"清洗后数据为：{len(result3_data)}条；"
    if len(dup_col) > 0 and len(na_col) > 0:
        result3_data = data.drop_duplicates(subset=dup_col, keep='first')
        result3_data = result3_data.dropna(subset=na_col)
        result3_data.to_excel(writer, sheet_name="清洗完成")
        msg += f"清洗后数据为：{len(result3_data)}条；"
    writer.save()
    writer.close()
    return {"filename": [result_name], "msg": msg}


def finance(path1: str, path2: str) -> dict[str, Union[list[str], str]]:
    """
    信息账单表合并函数
    :param path1:info
    :param path2:bill
    :return:
    """
    result_name = f"信息账单表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    writer = pd.ExcelWriter(f'data/{result_name}')

    # result1_name = f"卡号一致明细表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    # result2_name = f"账单中不在系统的卡_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    # result3_name = f"系统中不在账单卡_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    msg = f"表一原始数据为：{len(data1)}条；"
    msg += f"表二原始数据为：{len(data2)}条；"
    # 交集
    result1_data = pd.merge(data1, data2, how='inner', on="卡号")
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on="卡号", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result3_data = pd.merge(data1, data2, how='outer', on="卡号", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result1_data.to_excel(writer, sheet_name="卡号一致明细表")
    msg += f"卡号一致明细表数据为：{len(result1_data)}条；"
    result2_data.to_excel(writer, sheet_name="账单中不在系统的卡")
    msg += f"账单中不在系统的卡数据为：{len(result2_data)}条；"
    result3_data.to_excel(writer, sheet_name="系统中不在账单卡")
    msg += f"系统中不在账单卡数据为：{len(result3_data)}条；"
    writer.save()
    writer.close()
    return {"filename": [result_name], "msg": msg}


def ledger(path1: str, path2: str, col: str) -> dict[str, Union[list[str], str]]:
    """
    信息台账表合并函数
    :param col:
    :param path1: info
    :param path2: ledger
    :return:
    """
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    if col == "IP":
        result_name = f"信息台账_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        name1 = "信息台账差集表"
        name2 = "台账信息差集表"
        name3 = "台账信息交集拼接"
        msg = f"信息表原始数据为：{len(data1)}条；"
        msg += f"台账表原始数据为：{len(data2)}条；"
        # result1_name = f"信息台账差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        # result2_name = f"台账信息差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        # result3_name = f"台账信息交集拼接_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    else:
        result_name = f"合并表表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        name1 = "表1表2差集表"
        name2 = "表2表1差集表"
        name3 = "表1表2交集拼接"
        msg = f"表一原始数据为：{len(data1)}条；"
        msg += f"表二原始数据为：{len(data2)}条；"
        # result1_name = f"表1表2差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        # result2_name = f"表2表1差集表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        # result3_name = f"表1表2交集拼接_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    writer = pd.ExcelWriter(f'data/{result_name}')
    # 交集
    result1_data = pd.merge(data1, data2, how='outer', on=col, indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    # 差集
    result2_data = pd.merge(data2, data1, how='outer', on=col, indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
    result3_data = pd.merge(data1, data2, how='inner', on=col)
    result1_data.to_excel(writer, sheet_name=name1)
    msg += f"{name1}数据为：{len(result1_data)}条；"
    result2_data.to_excel(writer, sheet_name=name2)
    msg += f"{name2}数据为：{len(result2_data)}条；"
    result3_data.to_excel(writer, sheet_name=name3)
    msg += f"{name3}数据为：{len(result3_data)}条；"
    writer.save()
    writer.close()
    return {"filename": [result_name], "msg": msg}


def diff(path1: str, path2: str) -> dict[str, Union[list[str], str]]:
    result_name = f"费用比较表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    writer = pd.ExcelWriter(f'data/{result_name}')
    # result1_name = f"费用一致表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    # result2_name = f"费用不一致表_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    data1 = pd.read_excel(path1)
    data2 = pd.read_excel(path2)
    msg = f"表一原始数据为：{len(data1)}条；"
    msg += f"表二原始数据为：{len(data2)}条；"
    # 清洗
    dup1 = data1.drop_duplicates(subset=["卡号"], keep=False)
    dup1_f = data1.drop_duplicates(subset=["卡号"], keep="first")
    msg += f"表一重复数据为：{len(data1) - len(dup1)}条；去重(对于重复数据保留第一条)后得到：{len(dup1_f)}条；"
    dup2 = data2.drop_duplicates(subset=["卡号"], keep=False)
    dup2_f = data2.drop_duplicates(subset=["卡号"], keep="first")
    msg += f"表二重复数据为：{len(data2) - len(dup2)}条；去重后(对于重复数据保留第一条)得到：{len(dup2_f)}条；"

    merge_data = pd.merge(dup1_f, dup2_f, how='inner', on="卡号")
    merge_data["说明"] = merge_data.apply(lambda x: judge(x.费用_x, x.费用_y), axis=1)
    # msg += f"表一有{len(merge_data[merge_data['费用_x']].isna)}条不再表二中；"
    # msg += f"表二有{len(merge_data[merge_data['费用_y']].isna)}条不再表一中；"
    msg += f"表一有{merge_data['费用_x'].isnull().sum(axis=0)}条不再表二中；"
    msg += f"表二有{merge_data['费用_y'].isnull().sum(axis=0)}条不再表一中；"
    msg += f"相同卡号的有{len(merge_data)}条；"
    result1_data = merge_data[merge_data['说明'] == '一致']
    result2_data = merge_data[merge_data['说明'] == '不一致']
    result1_data.to_excel(writer, sheet_name="一致")
    msg += f"一致数据为：{len(result1_data)}条；"
    result2_data.to_excel(writer, sheet_name="不一致")
    msg += f"不一致数据为：{len(result2_data)}条；"
    writer.save()
    writer.close()

    return {"filename": [result_name], "msg": msg}


@app.post('/data_clean')
def clean_route():
    r = request.get_json()
    dup_col = r["dup_col"].split(",")
    na_col = r["na_col"].split(",")
    result = clean(r["path"], dup_col, na_col)
    return jsonify(result)


@app.post('/finance')
def finance_route():
    r = request.get_json()
    result = finance(r["path1"], r["path2"])
    return jsonify(result)


@app.post('/ledger')
def ledger_route():
    r = request.get_json()
    result = ledger(r["path1"], r["path2"], "IP")
    return jsonify(result)


@app.post('/merge')
def merge_route():
    r = request.get_json()
    result = ledger(r["path1"], r["path2"], r["col"])
    return jsonify(result)


@app.post('/diff')
def diff_route():
    r = request.get_json()
    result = diff(r["path1"], r["path2"])
    return jsonify(result)


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
