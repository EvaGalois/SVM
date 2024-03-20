import requests
import json, time
from collections import OrderedDict
import matplotlib.pyplot as plt
from pprint import pprint
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

# params = {
#     'lotno': 'F5121-240100233-001.1'
# }

datas = []
for fid in fids[:5]:
    datas.append(_get(url=url, params={'lotno': fid})['data'][0])
    time.sleep(0.001)

# targe = []
# for i in datas:
#     targe.append(i['TARGETPWR'])
# print(targe)
# exit()

result_dict = {}
for data in datas:
    DMODULNOTYPE = data['DMODULNOTYPE']
    TARGETPWR = data['TARGETPWR']
    spec_values = [data[f'规格检度数{i}'] for i in range(1, 10) if data[f'规格检度数{i}'] is not None]
    if not spec_values:
        continue
    avg_spec_value = sum(spec_values) / len(spec_values)

    if DMODULNOTYPE in result_dict:
        result_dict[DMODULNOTYPE].append((TARGETPWR, avg_spec_value))
    else:
        result_dict[DMODULNOTYPE] = [(TARGETPWR, avg_spec_value)]

pprint(result_dict)
exit()
cluster = {}
for k, v in result_dict.items():
    sum = 0
    for i in v:
        sum += i[1]
    # cluster[k] = ["{:.2f}".format(i[1] / len(v) * 100), len(v)]
    cluster[k] = float("{:.2f}".format(i[1] / len(v)))

pprint(cluster)
# file_path = 'MODULE.csv'
# with open(file_path, mode='w', newline='') as file:
#     writer = csv.writer(file)
#     # 写入字典的键和值
#     for key, value in cluster.items():
#         writer.writerow([key, value])

# exit()

plt.rcParams['font.sans-serif']=['SimHei']
plt.rcParams['axes.unicode_minus']=False 
plt.rcParams['font.size'] = 12

model_counts = {key: len(value) for key, value in result_dict.items()}

sorted_model_counts = dict(sorted(model_counts.items(), key=lambda item: item[1], reverse=True))
model_names = list(sorted_model_counts.keys())
model_appearances = list(sorted_model_counts.values())

plt.figure(figsize=(10, 6))
plt.bar(model_names, model_appearances)
plt.xlabel('模仁')
plt.ylabel('统计量')
plt.title('模仁统计量分布')

plt.xticks(rotation=270, ha='right')
plt.tight_layout()
plt.show()