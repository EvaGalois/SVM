import requests
import json, time
from collections import OrderedDict
import matplotlib.pyplot as plt
from pprint import pprint
import numpy as np
import csv

def _get(url:str = None, params: dict = {}):
    response = requests.get(url, params=params)

    # 检查响应状态码是否为 200（HTTP OK）
    if response.status_code == 200:
        # 提取<string>标签中的内容
        start_tag = '<string xmlns="http://tempuri.org/">'
        end_tag = '</string>'
        start_index = response.text.find(start_tag) + len(start_tag)
        end_index = response.text.find(end_tag)
        json_data = response.text[start_index:end_index]

        # 解析 JSON 数据
        data = json.loads(json_data)

    else:
        # 打印状态码和错误信息
        print(f"GET request failed with status code {response.status}")
    return data

FID = _get(url="http://10.10.12.9:89/WebService1.asmx/GetMouldMoLoNoData", params=None)
fids = []
for item in FID['data']:
    fids.append(item['生产批号'])

url = "http://10.10.12.9:89/WebService1.asmx/GetMouldSCData"

datas = []
for fid in fids[:50]:
    datas.append(_get(url=url, params={'lotno': fid})['data'][0])
    time.sleep(0.001)

import numpy as np

aggregated_data = {}

for entry in datas:
    module_type = entry['DMODULNOTYPE']
    if module_type not in aggregated_data:
        # 如果这个模仁类型还没有被记录，则初始化
        aggregated_data[module_type] = {
            'DMODULNOTYPE': module_type,
            'LINENO': entry['LINENO'],  # 假设 LINENO 和 TARGETPWR 在同一模仁类型中不变
            'TARGETPWR': entry['TARGETPWR'],
            'DATA': []  # 初始化空的list，用于存放所有的规格检度数
        }
    
    # 直接将规格检度数添加到DATA列表中，而不是作为子列表
    aggregated_data[module_type]['DATA'].extend([entry.get(f'规格检度数{i}', None) for i in range(1, 10)])

# 计算每个模仁的Cpk
for module_type, module_data in aggregated_data.items():
    # 过滤掉None值
    spec_values = [value for value in module_data['DATA'] if value is not None]
    
    if spec_values:
        TARGETPWR = float(module_data['TARGETPWR'])
        avg_spec_value = np.mean(spec_values)
        std_spec_value = np.std(spec_values, ddof=1)  # 使用样本标准差
        epsilon = 1e-6
        std_spec_value = max(std_spec_value, epsilon)

        if TARGETPWR == 0.0:
            bounds = [0.0, -0.18]
        elif TARGETPWR > -10.0:
            bounds = [TARGETPWR + 0.12, TARGETPWR - 0.18]
        else:
            bounds = [TARGETPWR + 0.24, TARGETPWR - 0.36]

        Cpk = min((bounds[0]-avg_spec_value)/(3*std_spec_value), (avg_spec_value-bounds[1])/(3*std_spec_value))
        
        # 存储Cpk相关数据
        aggregated_data[module_type]["CPK相关数据"] = {
            'avg_spec_value': avg_spec_value,
            'std_spec_value': std_spec_value,
            'Cpk': Cpk
        }

pprint(aggregated_data)

    