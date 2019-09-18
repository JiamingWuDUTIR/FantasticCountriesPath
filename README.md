# FantasticCountriesPath
“朝鲜和瑞典之间只隔了一个俄罗斯”，在知乎一个关于冷知识的问题下面，看到了这条回答。  
不禁产生了一个疑问，为什么这个陈述看起来不可思议？  
因为两个国家实际距离很远，但是曼哈顿距离只有2，两者比值很大。  
所以，本项目解决一个问题，距离比值（实际距离：曼哈顿距离）最大的国家是哪两个？  
  
### 问题解析  
解决这个问题需要充足的数据支持，除此之外，一个简单的宽度有限搜索算法就可以解决曼哈顿距离的问题了。  
需要的数据有：  
1. 国家名称，对应首都，首都坐标（以首都之间的距离作为国家之间的实际距离）  
2. 国家的邻国信息  
  
### 数据来源  
通过调研，找到了一个[地理位置网站](https://www.geonames.org/)，可以通过输入地名，选择国家，查找到对应位置的坐标。  
在该网站的下载页面，有一个文件[countryInfo.txt](http://download.geonames.org/export/dump/countryInfo.txt)，记录了若干国家的近二十项信息。包括国家名称，缩写代码，首都，语言，邮政编码等。最重要的，包括邻国信息。  
似乎这个文件的国家集合是根据ISO-3166标准来的，如HK,TW等地区单独列出。所以严谨起见，原始问题的表述修改为“ISO-3166标准内的国家与地区，比值距离最大的是哪两个？”  
除此之外，邻国信息也无从验证。挑选中国为例，是14个，与高中地理课本一致。  
总而言之，一切数据以该txt文件数据为准。  
  
### 项目结构  
十分简单，两个py文件，一个收集整理数据，一个计算输出结果。  
* 数据收集  
1. raw-data.txt：将数据来源中提到的txt文件中的有效部分，复制下来。  
2. country-data-19col.csv：对原始文本数据做一个格式化处理，生成csv。  
3. need-country-data-6col.csv：保留需要的6栏数据，国家简写（2字母），国家全称，首都，邻国，首都经纬度。这里国家已经做了筛选，筛去了没有邻国的，没有首都的地区。获取首都经纬度的方法是利用爬虫从[地理位置网站](https://www.geonames.org/)的搜索结果中获取。但由于正则没写好，有的匹配错了，不作为最终的数据源。  
4. need-country-data-6col-v2.csv：同上，只是获取首都经纬度的办法改用geopy包里的接口。但是同样有很多坑（比如把“Havana Cuba”定位成了中国澳门的某个地方），好好看参数说明。  
最终计算距离需要的数据都在need-country-data-6col-v2.csv里了，在程序结果的基础上，手工修改了一点。  
* 距离计算  
算法简单，曼哈顿距离直接宽搜，暴力就完事了。记录了上一节点信息，可以通过回溯，找到国家之间的连通链条。  
1. Location.png：将所有首都的经纬度打在了一张平面图上，可以清楚的看到非洲大陆的轮廓。同时把五常和巴西用红点标出，方便观看。  
2. Manhattan_distance.csv：打了个表，可以查找任意两个国家之间的最短距离，不存在说明不连通。  
3. Divided_distance.csv：比值距离表，-1表示自身或者不连通。  
4. All_countries_path.txt：每个国家到自己可连通国家曼哈顿距离，实际距离，比值距离，路径。  
  
### 结论  
基本上result/里头的几个文件就记录了所有重要信息。感兴趣的同学可以肉眼观察，找一些最大、最小值，观察一下国家之间的最短路径。写个接口也是很简单的。  
**问题的最终答案是“俄罗斯和朝鲜”，没办法，领土大就是这么粗暴。**  
问题的起源其实是错误的，俄罗斯和瑞典根本不接壤，跟芬兰，挪威都接壤。：）
