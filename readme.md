## 一个非常简单的空间搜索引擎api 调用工具：
### fofa-web.2.5 2024年11月23日更新
![image](https://github.com/user-attachments/assets/8ba13010-af4d-4773-b502-8abcdca6210d)


### 01.在2.0版本的基础上进行了大升级

#### 一、Fofa 查询（支撑语法参考、导出 、高级搜索功能，分页、筛选、右键菜单、双击复制，host超链接等等）

##### 1.1 Foda 查询主界面优化
###### 1、优化了数据的排列顺序
###### 2、优化了界面前端按钮样式
###### 3、优化了右键菜单，将右键浏览器打开，修改为超链接单击打开，并且做了优化只打开url
![image](https://github.com/user-attachments/assets/16f35d1d-2a3d-4ed5-bd48-ed5fddd77b31)


##### 1.2 高级搜索功能（再也不需要记忆复杂的Fofa 语法）
###### 1、再也不需要记忆复杂的Fofa语法, 可快速进行高级语法组合查询
![image](https://github.com/user-attachments/assets/305ebce9-1bcf-470b-a82a-7d5baa270318)
![image](https://github.com/user-attachments/assets/9da3037e-09cb-4ff1-b610-f308ff19f588)

#### 二、Quake 查询（支撑语法参考、导出 、高级搜索功能，分页、筛选、右键菜单、双击复制，host超链接等等）

##### 2.1 Quake 查询主界面优化
###### 1、优化了数据的排列顺序
###### 2、优化了界面前端按钮样式
###### 3、优化了右键菜单，将右键浏览器打开，修改为超链接单击打开，并且做了优化只打开url
![image](https://github.com/user-attachments/assets/cf9e83ea-77b5-47da-8832-1cf7119e0425)


##### 2.2 高级搜索功能
###### 1、再也不需要记忆复杂的Quake 语法，可快速进行高级语法组合查询
![image](https://github.com/user-attachments/assets/67f5940d-9f70-4636-99f3-74ef0a99e13e)
![image](https://github.com/user-attachments/assets/39d126b5-4efe-4624-b34c-7bd62bfb4c39)


#### 三、数据聚合界面优化
###### 1、对来自空间搜索引擎的数据，根据IP 端口 网页标题等进行了去重复
###### 2、新增删除单行 和 复制单行的功能
###### 3、把同步数据到"精简面板放到了前端"，用户可在此处使用删除行的功能对数据做进一步的降噪处理
###### 4、优化了右键菜单，将右键浏览器打开，修改为超链接单击打开，并且做了优化只打开url
###### 5、同时优化了前端的布局，数据显示顺序，按钮样式等等
![image](https://github.com/user-attachments/assets/ab275950-4b24-4547-b805-dfff2b39ff6e)


#### 四、精简面板界面
###### 1、进行了重大的前端调整，包括布局，按钮，卡片，配色等等
![image](https://github.com/user-attachments/assets/3d1fdbf8-5cf3-4750-98d6-235d7bb90b28)


###### 2、具备IP 资产卡片的缩放功能
收起
![image](https://github.com/user-attachments/assets/ecc94f3a-feb9-47b2-8c4f-fa9c0ce87033)

展开
![image](https://github.com/user-attachments/assets/f399cb08-ddd1-4211-9ef1-4cfb82c802bc)

###### 3、增加了备注与打标签的功能，包含备注与标签的增加，删除，更新等
![image](https://github.com/user-attachments/assets/ff595ad7-b57d-4ee6-833d-7912c381adf1)

并且备注或打标签后，卡片标题变为蓝色，方便团队协作时，不用重复浪费劳动力
并且还添加了一键筛选，对已打标签的IP进行快速查看
![image](https://github.com/user-attachments/assets/62f71c73-67c5-4b13-80e0-4168ad69d743)

鼠标悬停，不展开卡片，也可以快速查看 标签和备注功能
![image](https://github.com/user-attachments/assets/f69aee22-16e8-440c-8901-065b452d14bc)


###### 4、可删除IP卡片中不重要的端口，进行降噪
![image](https://github.com/user-attachments/assets/9404bca7-9a34-4cd8-9ed1-66ba7d0b7a63)


###### 5、新增IP卡片功能，添加新发现的IP 或端口
![image](https://github.com/user-attachments/assets/0f48191b-2770-49ce-8968-3a8f9925c459)


###### 6、统计功能，再次去重后的统计结果
![image](https://github.com/user-attachments/assets/921e9062-b64b-4f42-8e76-94496d8426c4)

###### 7、宏观 按钮，可以在界面中展示足够多的卡片
![image](https://github.com/user-attachments/assets/a65e540a-623d-4831-b3be-279ed96d62e5)


### 01. 系统的安装

#### 1、安装所需的模块

python 环境 大于等于 3.10

pip install requirements.txt


#### 2、在打开程序前新建一个数据库，在 http://127.0.0.1:5000/configure 配置好所需的 fofa key 、 Quake Token 数据库配置等

![627b5436e7fd06a64fd1ab95c9fc946](https://github.com/user-attachments/assets/80580399-0d61-4504-b488-2755e527eeb5)


####  3、然后访问：http://127.0.0.1:5000/fofa_search 即可


## 觉得工具不错的，请给一个免费的 "点赞" !!!! 谢谢


## 最后欢迎关注公众号 “和光同尘hugh”

![hugh](https://github.com/user-attachments/assets/096a2113-dc90-4207-8f9e-dcdfa019fa35)


