import pandas as pd
import re
import numpy as np
from geopy.distance import vincenty
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import matplotlib
from pyecharts.charts import HeatMap, Scatter

def _get_neighbours(neighbour_str, exist_lst):
    """
    将一个国家的邻国字符串转换成列表，注意筛去不存在首都的国家
    新版本不用了
    :param neighbour_str:
    :param exist_lst: 存在首都国家列表
    :return:
    """
    raw_lst = neighbour_str.split(',')
    res_lst = list(filter(lambda x: 1 if x in exist_lst else 0, raw_lst))
    return res_lst


def _get_neighbour_graph(data_df):
    """
    生成邻国节点图，key是国家编号，value是邻国的编号list
    :param data_df:
    :return:
    """
    dct = {}
    for i in data_df.index:
        code = data_df.loc[i, 'ISO']
        if code is np.nan:  # 会把字符串NA认成nan 佛了
            code = 'NA'
        neighbours_str = data_df.loc[i, 'neighbours']
        dct[code] = neighbours_str.split(',')
    return dct


def _check_bidirection_line(dct):
    """
    检查一下所有邻国的连线是不是双向的，有异常会输出
    :param dct:
    :return:
    """
    flag = False
    for country, nei_list in dct.items():
        for nei in nei_list:
            if nei in dct:
                if country not in dct[nei]:
                    print(country, nei, list(dct[nei]))
                    flag = True
                    dct[nei].append(country)  # 补进去，完备双向边
            else:
                flag = True
                print(nei, 'not in dict keys')
    if not flag:
        print('all lines are bidirection, good graph!')


def get_graph():
    df = pd.read_csv('./data/need-country-data-6col-v2.csv')
    print(df.shape)

    # 生成节点图，用字典保存
    graph_dct = _get_neighbour_graph(df)
    _check_bidirection_line(graph_dct)
    _check_bidirection_line(graph_dct)  # 第一遍检测双向边并补齐，第二遍确认
    return graph_dct


def _get_one_path_dct(start_name, graph):
    """
    给定一个图和一个起点，返回这个起点到图中所有点的最短距离。
    由于边的权值都是1，所以用了很简单的dfs
    :param start_name: 起点
    :param graph: 图
    :return path_dct: 字典，键是图中所有点，值是一个list包括了距离和上位点（为了回溯还原路径）
    """
    INF = 10000
    path_dct = {}
    for each_point in graph.keys():
        if each_point != start_name:
            path_dct[each_point] = [INF, '@@@']  # 记录最短路径和上位点，这里做初始化
        else:
            path_dct[each_point] = [0, '@@@']  # 自己

    queue = []
    for each_point in graph[start_name]:
        path_dct[each_point] = [1, start_name]
        queue.append(each_point)     # 队列初始化，加入第一批相邻节点
    while queue:
        deal_point = queue.pop(0)

        deal_point_distance = path_dct[deal_point][0]
        deal_point_neighbours = graph[deal_point]
        for neighbour_point in deal_point_neighbours:
            neighbour_point_distance = path_dct[neighbour_point][0]
            if neighbour_point_distance <= deal_point_distance:  # 入过队的就不用再入了
                pass
            else:
                path_dct[neighbour_point] = [deal_point_distance+1, deal_point]
                queue.append(neighbour_point)
    return path_dct


def _get_full_path(destination, path_dct):
    """
    根据生成的最短路径字典，回溯生成最短路径
    :param destination: 终点名称
    :param path_dct: 最短路径字典
    :return: list记录了每一步的名称
    """
    path_lst = []
    pre = path_dct[destination][1]
    while pre != '@@@':
        path_lst.append(pre)
        pre = path_dct[pre][1]
    if path_lst:
        path_lst.reverse()
        path_lst.append(destination)
    return path_lst


def get_manhattan_distance_dct(graph):
    distance_dtc = {}
    path_dct = {}
    for start_point in graph.keys():
        start_dct = _get_one_path_dct(start_point, graph)

        INF = 10000
        one_distance_dct = {}
        one_path_dct = {}
        for each_des, msg in start_dct.items():
            if msg[0] != INF:
                one_distance_dct[each_des] = msg[0]
            else:
                one_distance_dct[each_des] = None
            one_path_dct[each_des] = _get_full_path(each_des, start_dct)

        distance_dtc[start_point] = one_distance_dct
        path_dct[start_point] = one_path_dct
    return distance_dtc, path_dct


def get_real_distance_dct():
    df = pd.read_csv('./data/need-country-data-6col-v2.csv')
    # 每个节点的经纬度字典
    location_dct = {}
    for i in df.index:
        lat = df.loc[i, 'latitude']
        long = df.loc[i, 'longitude']
        code = df.loc[i, 'ISO']
        if code is np.nan:
            code = 'NA'
        location_dct[code] = [lat, long]

    # 根据节点图，计算每两个节点间的实际距离
    real_distance_dct = {}
    for start in location_dct.keys():
        loc_a = location_dct[start]
        real_distance_dct[start] = {}
        for end in location_dct.keys():
            if end != start:
                loc_b = location_dct[end]
                distance = vincenty(loc_a, loc_b).meters
                real_distance_dct[start][end] = distance
            else:
                real_distance_dct[start][end] = 0
    return location_dct, real_distance_dct


def calculate_s_e(s_code, e_code, m_dct, dis_dct, path_dct, loc_dct):
    """
    给定起点，重点的国家code，输出信息
    :param s_code:
    :param e_code:
    :param m_dct:
    :param dis_dct:
    :param path_dct:
    :param loc_dct:
    :return:
    """
    m_dis = m_dct[s_code][e_code]
    real_dis = dis_dct[s_code][e_code]
    full_path = path_dct[s_code][e_code]
    res = real_dis / m_dis
    print(s_code, loc_dct[s_code])
    print(e_code, loc_dct[e_code])
    print(res, real_dis, m_dis)
    print(full_path)


def get_name_dct():
    df = pd.read_csv('./data/need-country-data-6col-v2.csv')
    code2name = {}
    name2code = {}
    name2cap = {}
    for i in df.index:
        code = df.loc[i, 'ISO']
        if code is np.nan:
            code = 'NA'
        con_name = df.loc[i, 'Country']
        cap_name = df.loc[i, 'Capital']

        code2name[code] = con_name
        name2code[con_name] = code
        name2cap[con_name] = cap_name

    return code2name, name2code, name2cap


def write_result():
    # 解决中文和负号的显示问题
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False

    # 绘制地理位置散点图
    loc_sort = sorted(loc_dct.items(), key=lambda x: x[1][1])
    lat_lst = [int(i[1][0]) for i in loc_sort]
    long_lst = [int(i[1][1]) for i in loc_sort]
    name_lst = [code2name[i[0]] for i in loc_sort]
    lighting_country_lst = ['China', 'United States', 'France', 'Brazil', 'United Kingdom', 'Russia']
    color_lst = ['red' if i in lighting_country_lst else 'blue' for i in name_lst]

    plt.scatter(long_lst, lat_lst, c=color_lst)
    plt.title('地理位置平面图')
    plt.xlabel('经度')
    plt.ylabel('纬度')
    plt.savefig('./result/Location.png')

    # 把曼哈顿距离和比值距离存成csv
    code_lst = m_dis_dct.keys()
    name_lst = [code2name[i] for i in code_lst]
    m_data = []
    div_data = []
    for s in code_lst:
        s_m_lst = []
        s_div_lst = []
        for e in code_lst:
            m_dis = m_dis_dct[s][e]
            r_dis = real_distance_dct[s][e]
            if m_dis:
                div_dis = int(r_dis / m_dis / 1000)
            else:
                div_dis = -1
            s_m_lst.append(m_dis)
            s_div_lst.append(div_dis)

        m_data.append(s_m_lst)
        div_data.append(s_div_lst)

    m_dis_df = pd.DataFrame(m_data, index=name_lst, columns=name_lst)
    m_dis_df.to_csv('./result/Manhattan_distance.csv')

    div_dis_df = pd.DataFrame(div_data, index=name_lst, columns=name_lst)
    div_dis_df.to_csv('./result/Divided_distance.csv')

    # 写每个国家的全路径
    with open('./result/All_countries_path.txt', 'w', encoding='utf-8') as f_open:
        f_open.write('终点  曼哈顿距离  实际距离  比值距离  路径\n')
        f_open.write('**********************\n')
        for s in code_lst:
            f_open.write('%s\n' % code2name[s])
            for e, m_dis in m_dis_dct[s].items():
                if m_dis:
                    r_dis = int(real_distance_dct[s][e] / 1000)
                    one_path = str([code2name[i] for i in full_path_dct[s][e]])
                    str_one = ' '.join([code2name[e], str(m_dis), str(r_dis), str(int(r_dis/m_dis)), one_path])
                    f_open.write(str_one + '\n')
            f_open.write('**********************\n')


code2name, name2code, name2cap = get_name_dct()
graph_dct = get_graph()

m_dis_dct, full_path_dct = get_manhattan_distance_dct(graph_dct)
loc_dct, real_distance_dct = get_real_distance_dct()
write_result()

# 输入两个国家代码，可以看到相关信息
s_code = ''
e_code = ''
calculate_s_e(s_code, e_code, m_dis_dct, real_distance_dct, full_path_dct, loc_dct)



# max_dif = 0
# min_dif = 10000000
# max_res = []
# min_res = []
# for s, s_dct in m_dis_dct.items():
#     for e, m_s_e in s_dct.items():
#         if m_s_e:
#             dif = real_distance_dct[s][e] / m_s_e
#             if dif > max_dif:
#                 max_dif = dif
#                 max_res = [s, e]
#             if dif != 0 and dif < min_dif:
#                 min_dif = dif
#                 min_res = [s, e]
#
# print('\n')
# calculate_s_e(max_res[0], max_res[1], m_dis_dct, real_distance_dct, full_path_dct, loc_dct)
# print('\n')
# calculate_s_e(min_res[0], min_res[1], m_dis_dct, real_distance_dct, full_path_dct, loc_dct)


