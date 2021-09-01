# -*- coding:utf-8 -*-
"""
@Author: wileyZhang
@Date: 8/30/21 11:16
@IDE: PyCharm
@Description=''
"""
import pandas as pd

# 导出重复的数据
data = pd.read_excel('/Users/jonzhang/Downloads/test.xlsx')
# a = data.groupby(['id']).count() > 1
# p = a[a['name'] == True].index
# rd = data[data['id'].isin(p)]
# print(rd)

data2 = data.drop_duplicates(subset=["id"], keep=False)
s = pd.merge(data, data2, how='outer', on="id", indicator=True).query('_merge == "left_only"').drop(
        columns=['_merge'])
print(s)

# 找出行中有空的数据
# data = pd.read_excel('/Users/jonzhang/Downloads/test.xlsx')
# # print(data.index.tolist())
# # print(data)
# n = data.isnull().any(axis=1)
# m = n[n == True].index
# dd = data[data.index.isin(m)]
# print(dd)
