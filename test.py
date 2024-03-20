import requests
import json, time
from collections import OrderedDict
from pprint import pprint

filename = 'build/MOduleSearch/aggregated_data.json'
# 打开并读取JSON文件
with open(filename, 'r') as file:
    data = json.load(file)
# 打印所有的键
print(len(data.keys()))
exit()

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

# params = {
#     'lotno': 'F5121-240100233-001.1'
# }

datas = []
for fid in fids[:5]:
    datas.append(_get(url=url, params={'lotno': fid}))
    time.sleep(0.005)
# print(data['data'][0])
clear_datas = []
for data in datas:
    clear_datas.append(data['data'][0])
# pprint(clear_datas)

datas_clean = []
count = 0
for item in clear_datas:
    ordered_dict = OrderedDict(item)
    values_list = list(ordered_dict.values())
    clear_data = {}
    clear_data['生产批号'] = values_list[0]
    clear_data['料号'] = values_list[1]
    clear_data['线体'] = values_list[2]
    clear_data['穴号'] = values_list[3]
    clear_data['目标度数'] = values_list[4]
    clear_data['母模模仁'] = values_list[5]
    clear_data['母模R值'] = values_list[6]
    clear_data['母模R值测量值'] = values_list[7:10]
    clear_data['CT值'] = values_list[10]
    clear_data['首件CT值'] = values_list[11:14]
    clear_data['新度数'] = values_list[14]
    clear_data['是否换度'] = values_list[15]
    clear_data['规格检CT值'] = values_list[16:25]
    clear_data['规格检度数'] = values_list[25:]
    datas_clean.append(clear_data)
    count += 1
    print(count)

pprint(datas_clean)

