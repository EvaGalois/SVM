import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import numpy as np
import os
import time
from pprint import pprint

# 尝试从文件加载聚合数据
def load_aggregated_data():
    try:
        if os.path.exists('aggregated_data.json') and os.path.getsize('aggregated_data.json') > 0:
            with open('aggregated_data.json', 'r') as file:
                return json.load(file)
        else:
            return {}
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return {}

aggregated_data = load_aggregated_data()

def calculate_cpk(data, target_pwr):
    if not data:
        return None
    # 直接使用 data 参数，因为它已经是一个一维列表
    spec_values = [value for value in data if value is not None]
    if not spec_values:
        return None
    avg_spec_value = np.mean(spec_values)
    std_spec_value = np.std(spec_values, ddof=1)  # 使用样本标准差进行计算
    epsilon = 1e-6
    std_spec_value = max(std_spec_value, epsilon)

    # 根据 target_pwr 计算规格界限
    if target_pwr == 0.0:
        bounds = [0.0, -0.18]
    elif target_pwr > -10.0:
        bounds = [target_pwr + 0.12, target_pwr - 0.18]
    else:
        bounds = [target_pwr + 0.24, target_pwr - 0.36]

    # 计算 CPK 值
    cpk = min((bounds[0] - avg_spec_value) / (3 * std_spec_value), (avg_spec_value - bounds[1]) / (3 * std_spec_value))
    return cpk


def update_data():
    global aggregated_data
    start_time = time.time()  # 开始计时
    items_str = items_entry.get()  # 获取输入框内容
    intervals = generate_intervals()  # 生成刻度列表
    items = 50  # 默认值
    if items_str:  # 如果输入框有内容，则尝试转换为整数
        try:
            items = int(items_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for the number of items.")
            return

    # try:
    # 获取大量工单号的Api
    url = "http://10.10.12.9:89/WebService1.asmx/GetMouldMoLoNoData"
    response = requests.get(url)
    if response.status_code == 200:
        start_tag = '<string xmlns="http://tempuri.org/">'
        end_tag = '</string>'
        start_index = response.text.find(start_tag) + len(start_tag)
        end_index = response.text.find(end_tag)
        json_data = response.text[start_index:end_index]
        data = json.loads(json_data)
        fids = [item['生产批号'] for item in data['data'][:items]]
        # print(fids)
        # exit()
        for fid in fids:
            # 工单号作为参数传进去请求“详细的生产数据”的Api
            url = "http://10.10.12.9:89/WebService1.asmx/GetMouldSCData"
            params = {'lotno': fid}
            response = requests.get(url, params=params)
            if response.status_code == 200:
                start_index = response.text.find(start_tag) + len(start_tag)
                end_index = response.text.find(end_tag)
                json_data = response.text[start_index:end_index]
                data = json.loads(json_data)
                for entry in data['data']:
                    module_type = entry['DMODULNOTYPE']
                    lotno = entry['LOTNO']
                    tag_pwr = entry['TARGETPWR']
                    
                    # 模仁在同样的工单中不可能存在两种线体，CPK数据集应该划分线体
                    # 划分线体逻辑：不同的工单，不同的线体
                    if module_type not in aggregated_data and entry['LINENO'] != None:
                        aggregated_data[module_type] = {
                            'DMODULNOTYPE': module_type,
                            'LOTNO': [lotno],
                            'LINENO': [entry['LINENO']],
                            'TARGETPWR': tag_pwr,
                            'DATA': {entry['LINENO']: [entry.get(f'规格检度数{i}', None) for i in range(1, 10)]}
                        }
                        # print(f"LINENO: {entry['LINENO']}")
                        # print(f"LINENO: {aggregated_data[module_type]['DATA']}")
                        # print(f"MODULNOTYPE: {module_type}, LINENO: {aggregated_data[module_type]['DATA'][entry['LINENO']]}, LOTNO: {lotno}, TARGETPWR: {tag_pwr}")
                        aggregated_data[module_type]['CPK'] = {entry['LINENO']: calculate_cpk(aggregated_data[module_type]['DATA'][entry['LINENO']], float(aggregated_data[module_type]['TARGETPWR']))}
                        aggregated_data[module_type]['MU'] = {entry['LINENO']: np.mean(aggregated_data[module_type]['DATA'][entry['LINENO']])}
                        aggregated_data[module_type]['IN'] = {entry['LINENO']: find_closest_interval(aggregated_data[module_type]['MU'][entry['LINENO']], intervals)}
                    elif entry['LINENO'] != None:
                        # print(aggregated_data[module_type]['LOTNO'])
                        # if lotno not in aggregated_data[module_type]['LOTNO']:
                        if entry['LINENO'] not in aggregated_data[module_type]['LINENO']:
                            aggregated_data[module_type]['LOTNO'].append(lotno)
                            aggregated_data[module_type]['LINENO'].append(entry['LINENO'])
                            # print(f"MODULNOTYPE: {module_type}, LINENO: {aggregated_data[module_type]['DATA'][entry['LINENO']]}, LOTNO: {lotno}, TARGETPWR: {tag_pwr}")
                            # if entry['LINENO'] not in aggregated_data[module_type]['LINENO'][:-2]:
                            aggregated_data[module_type]['DATA'][entry['LINENO']] = [entry.get(f'规格检度数{i}', None) for i in range(1, 10)]
                            aggregated_data[module_type]['CPK'][entry['LINENO']] = calculate_cpk(aggregated_data[module_type]['DATA'][entry['LINENO']], float(aggregated_data[module_type]['TARGETPWR']))
                            aggregated_data[module_type]['MU'][entry['LINENO']] = np.mean(aggregated_data[module_type]['DATA'][entry['LINENO']])
                            aggregated_data[module_type]['IN'][entry['LINENO']] = find_closest_interval(aggregated_data[module_type]['MU'][entry['LINENO']], intervals)
                        else:
                            aggregated_data[module_type]['DATA'][entry['LINENO']].extend(
                                [entry.get(f'规格检度数{i}', None) for i in range(1, 10)]
                            )
                            aggregated_data[module_type]['CPK'][entry['LINENO']] = calculate_cpk(aggregated_data[module_type]['DATA'][entry['LINENO']], float(aggregated_data[module_type]['TARGETPWR']))
                            aggregated_data[module_type]['MU'][entry['LINENO']] = np.mean(aggregated_data[module_type]['DATA'][entry['LINENO']])
                            aggregated_data[module_type]['IN'][entry['LINENO']] = find_closest_interval(aggregated_data[module_type]['MU'][entry['LINENO']], intervals)

        # 保存更新后的aggregated_data到文件
        with open('aggregated_data.json', 'w') as file:
            file.write(json.dumps(aggregated_data, indent=4))
        end_time = time.time()  # 结束计时 18751067736|774427202|13992185044|15385419276zxy4508173|1837053622dhy18352686979
        elapsed_time = end_time - start_time  # 计算用时
        update_info_label.config(text=f"本次更新了{items_str}条数据，用时{round(elapsed_time, 2)}秒")  # 更新标签显示的文本
            
        messagebox.showinfo("Success", "Data updated and saved successfully.")
    else:
        messagebox.showerror("Error", "Failed to fetch data.")
    # except Exception as e:
    #     messagebox.showerror("Error", str(e))

def generate_intervals():
    intervals = [0]
    # 生成从0到-10的刻度，每0.25一个刻度
    intervals.extend([-i * 0.25 for i in range(1, 41)])
    # 生成从-10.25到-20的刻度，每0.5一个刻度
    intervals.extend([-10 - i * 0.5 for i in range(1, 21)])
    return intervals

def find_closest_interval(mu, intervals):
    # 找到与mu值最接近的区间
    closest = min(intervals, key=lambda x: abs(x - mu))
    return closest

def search_moulds():
    target_pwr_str = target_pwr_entry.get()  # 获取目标度数输入框内容
    lineno_str = lineno_entry.get()  # 获取线体编号输入框内容
    try:
        target_pwr = float(target_pwr_str)  # 尝试将输入转换为浮点数
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for the target power.")
        return

    # 准备一个空列表用于存储 (模仁类型, CPK, MU) 元组
    mould_cpk_mu_pairs = []

    # 遍历 aggregated_data 寻找所有符合 IN 值 = 用户输入数字的模仁
    for module_type, module_info in aggregated_data.items():
        # # 当线体编号输入框为空或者模仁的线体编号列表中包含用户输入的线体编号时进行下一步
        # if not lineno_str or lineno_str in module_info['LINENO']:
        #     # 再检查是否有 IN 值和用户输入匹配
        #     if 'IN' in module_info and module_info['IN'] == target_pwr:
        #         cpk = module_info.get('CPK', None)  # 检查 CPK 值是否被计算
        #         mu = module_info.get('MU', None)  # 获取 MU 值
        #         tag = module_info.get('TARGETPWR', None)
        #         lineno = module_info.get('LINENO', None)
        #         if cpk is not None and mu is not None:
        #             mould_cpk_mu_pairs.append((module_type, cpk, mu, lineno))
        
        if not lineno_str or lineno_str in module_info['LINENO']:
            
            if lineno_str in module_info['IN'].keys():
                cpk_dict = module_info.get('CPK', None)
                cpk = cpk_dict[lineno_str]
                mu_dict = module_info.get('MU', None)
                mu = mu_dict[lineno_str]
                in_dict = module_info.get('IN', None)
                in_ = in_dict[lineno_str]
                tag = module_info.get('TARGETPWR', None)
                if cpk is not None and mu is not None:
                    mould_cpk_mu_pairs.append((module_type, cpk, mu, lineno_str, tag, in_))

    mould_cpk_mu_pairs = [item for item in mould_cpk_mu_pairs if item[-1] == target_pwr]

    # 按 CPK 值对模仁进行排序，从大到小
    mould_cpk_mu_pairs.sort(key=lambda x: x[1], reverse=True)
    # print(mould_cpk_mu_pairs)

    # 清空并更新模仁列表展示区
    mould_listbox.delete(0, tk.END)  # 清空列表框
    for mould, cpk, mu, lineno, tag, in_ in mould_cpk_mu_pairs:
        # mould_listbox.insert(tk.END, f"{mould}: CPK={cpk}, MU={mu}, TAG={tag}, LINENO={lineno}")  # 添加模仁到列表框
        mould_listbox.insert(tk.END, f"{mould}: LINENO={lineno}")  # 添加模仁到列表框

        
# 创建主窗口
root = tk.Tk()
root.title("模仁推荐机")
root.geometry("400x600")  # 设置初始窗口大小

# 设置暗黑风格背景颜色
root.configure(bg="#222222")

style = ttk.Style()
style.theme_use("clam")

style.configure("TFrame", background="#222222")
style.configure("TLabel", background="#222222", foreground="#CCCCCC")
style.configure("TEntry", background="#555555", foreground="black", insertbackground="black")  # 设置输入颜色为黑色
style.configure("TButton", background="#444444", foreground="#CCCCCC", borderwidth=0, font=('Helvetica', 16))  # 增大按钮189051660332103191172
style.map("TButton", background=[('active', '#666666'), ('pressed', '#555555')])

# 创建并使用 ttk.Frame 作为主容器来应用暗黑风格
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.pack(fill=tk.BOTH, expand=True)

items_label = ttk.Label(main_frame, text="更新数据量", font=('Helvetica', 12, 'bold'))
items_label.pack(pady=(10,0))

items_entry = ttk.Entry(main_frame, font=('Helvetica', 20), background="black")
items_entry.pack(pady=(0,20), fill=tk.X)

button = ttk.Button(main_frame, text="更新数据", command=update_data)
button.pack(pady=10, ipadx=10, ipady=5)  # 增加内边距来增大按钮299516859818852833198

# 创建显示更新信息的标签
update_info_label = tk.Label(root, text="", bg="#222222", fg="#CCCCCC")
update_info_label.pack(pady=(10, 0))

lineno_label = ttk.Label(main_frame, text="线体编号", font=('Helvetica', 12, 'bold'))
lineno_label.pack(pady=(20, 0))

lineno_entry = ttk.Entry(main_frame, font=('Helvetica', 20), background="black")
lineno_entry.pack(pady=(0, 20), fill=tk.X)

# 创建目标度数的输入框和标签
target_pwr_label = ttk.Label(main_frame, text="目标度数", font=('Helvetica', 12, 'bold'))
target_pwr_label.pack(pady=(20, 0))

target_pwr_entry = ttk.Entry(main_frame, font=('Helvetica', 20), background="black")
target_pwr_entry.pack(pady=(0, 20), fill=tk.X)

# 创建搜索模仁的按钮
search_button = ttk.Button(main_frame, text="模仁搜索", command=search_moulds)
search_button.pack(pady=10, ipadx=10, ipady=5)  # 增加内边距来增大按钮

# 创建滚动条和Listbox用于展示数据，调整背景颜色以适应暗黑风格
scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

mould_listbox = tk.Listbox(main_frame, yscrollcommand=scrollbar.set, bg="#222222", fg="#FFFFFF", 
                           highlightbackground="#FF00FF", selectbackground="#0077FF", 
                           selectforeground="#FFAA00", font=('Helvetica', 20), 
                           borderwidth=0, highlightthickness=0)
mould_listbox.pack(padx=10, pady=20, fill=tk.BOTH, expand=True)

scrollbar.config(command=mould_listbox.yview)

root.mainloop()