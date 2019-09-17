import pandas as pd
import requests
import re
import numpy as np
from geopy.geocoders import Nominatim
import time


def deal_raw_data():
    """
    把txt读出来，结构化存成csv，只运行一次
    :return:
    """
    data_path = './data/raw-data.txt'
    with open(data_path, 'r', encoding='utf-8') as f_open:
        lines = f_open.readlines()

    titles = lines[0].strip('\n').split('\t')
    lst = []
    for line in lines[1:]:
        line = line.strip('\n')
        lst.append(line.split('\t'))
    df = pd.DataFrame(lst, columns=titles)

    df.to_csv('./data/country-data-19col.csv', index=False)
    print('done!')


def _catch_index(city_name, country_code):
    """
    根据城市名称和国家代码，在查找结果中找到具备首都属性的，返回经纬度
    正则写的有点问题，获取的可能不是首都的经纬度
    不管了，用第二个版本接口获取
    :param city_name: 城市名称
    :param country_code: 国家代码 如 CN
    :return:
    """
    url_base = 'https://www.geonames.org/search.html?q={}&country={}'
    url_todo = url_base.format(city_name, country_code)

    r = requests.get(url_todo)
    content = r.content.decode('utf-8')
    pattern = re.compile('capital of a political entity.*</td>.*([NS] \d+° \d+\' \d+\'\')</td>.*([EW] \d+° \d+\' \d+\'\')</td>', re.S)
    lst = re.findall(pattern, content)
    if len(lst) == 1:
        return lst[0]
    else:
        return None


def filter_need_data():
    """
    只选取需要读数据栏，同时通过爬虫获得首都的经纬度信息
    :return:
    """
    df = pd.read_csv('./data/country-data-19col.csv')
    print(df.shape)

    # 筛选出具备首都和邻国的
    df_4col = df[['ISO', 'Country', 'Capital', 'neighbours']]
    df_need = df_4col[(df_4col['Capital'].notna()) & (df_4col['neighbours'].notna())]
    print(df_need.shape)
    df_need = df_need.reset_index(drop=True)

    # 查询首都经纬度
    latitude_lst = []
    longitude_lst = []
    code_lst = df_need['ISO']
    for i, cap in enumerate(df_need['Capital']):
        res = _catch_index(cap, code_lst[i])
        if res:
            latitude_lst.append(res[0])
            longitude_lst.append(res[1])
            print(res[0], res[1])
        else:
            latitude_lst.append(np.nan)
            longitude_lst.append(np.nan)
            print(cap, code_lst[i], 'not found!!!!!')

    df_need['latitude'] = latitude_lst
    df_need['longitude'] = longitude_lst
    df_need.to_csv('./data/need-country-data-6col.csv', index=False)


def _get_lat_long(cap, con):
    """
    使用接口获取经纬度，优先获取首都的，不行则获取国家的
    注意先用 国家 + 首都  免得地名重名
    :param cap:首都名称
    :param con:国家名称
    :return:
    """
    try:
        # 有可能首都地名找不到，那就找国家名字
        obj = Nominatim()
        # loc = cap + ' ' + con
        loc = {'country': con, 'city': cap}
        msg = obj.geocode(loc)
        if msg:
            lat, long = msg.latitude, msg.longitude
            print(loc, lat, long)
        else:
            lat, long = np.nan, np.nan
            print(loc, 'not find!!!')
        # else:
        #     obj = Nominatim()
        #     msg = obj.geocode(con)
        #     if msg:
        #         lat, long = msg.latitude, msg.longitude
        #         print('con', con, lat, long)
        #     else:
        #         lat, long = np.nan, np.nan
        #         print('cap not find!!!')
        return lat, long
    except:
        print("Error: %s!!!" % cap)
        return np.nan, np.nan


def filter_need_data_v2():
    """
    第二个版本，利用geopy的接口获取经纬度
    :return:
    """
    df = pd.read_csv('./data/country-data-19col.csv')
    print(df.shape)

    # 筛选出具备首都和邻国的
    df_4col = df[['ISO', 'Country', 'Capital', 'neighbours']]
    df_need = df_4col[(df_4col['Capital'].notna()) & (df_4col['neighbours'].notna())]
    df_need = df_need.reset_index(drop=True)
    print(df_need.shape)
    df_need['latitude'] = np.nan
    df_need['longitude'] = np.nan

    # 查询首都经纬度
    for i in df_need.index:
        con = df_need.loc[i, 'Country'].strip()
        cap = df_need.loc[i, 'Capital'].strip()
        lat, long = _get_lat_long(cap, con)
        df_need.loc[i, 'latitude'] = lat
        df_need.loc[i, 'longitude'] = long
        time.sleep(1.5)

    df_need.to_csv('./data/need-country-data-6col-v2.csv', index=False)


def fix_missing_loc():
    """
    由于这个接口会迷之报错，所以重复几次，把没有弄好的经纬度反复补充
    :return:
    """
    df = pd.read_csv('./data/need-country-data-6col-v2.csv')

    missing_df = df[df['latitude'].isna()]
    print(missing_df.shape)

    for i in missing_df.index:
        con = df.loc[i, 'Country'].strip()
        cap = df.loc[i, 'Capital'].strip()
        lat, long = _get_lat_long(cap, con)
        df.loc[i, 'latitude'] = lat
        df.loc[i, 'longitude'] = long
        time.sleep(1.5)

    df.to_csv('./data/need-country-data-6col-v2.csv', index=False)


# filter_need_data_v2()
fix_missing_loc()
