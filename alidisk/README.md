#### AliDisk
---
#### 用法
`python3 -m pip install aligo`

`python3 alidisk.py`
修改文件260行邮箱及提示语。

感谢aligo大牛门造出陆虎，咱不过就是那个给陆风改车漆的，不值一提。贴上[aligo](https://pypi.org/project/aligo/)链接，以表敬意。

---
#### 支持命令&功能
- ls - 列出当前目录内容
- pwd - 显示当前所在目录
- cd - 更改目录
- mv - 移动文件｜目录
- cp - 复制文件｜目录
- rm - 删除文件｜目录
- 文件名自动补全

---
#### 目前存在bug
- 尚不支持带特殊字符的目录&文件名
- 尚不支持除上述列表以外其它命令

---
#### 示例
##### 1. 登陆
aligo提供了两种方式登陆，不指定接受邮箱时直接打开二维码，扫码登陆；或者指定接受二维码的邮箱，在收件中扫码登陆。

<img src="https://norvyn.com/wp-content/uploads/2022/08/Screen-Shot-2022-08-20-at-18.54.39.png" width="70%">

So easy! 不费话。

##### 2. 列出目录内容并删除文件
`cd test`
`rm batt<tab>`

<img src="https://norvyn.com/wp-content/uploads/2022/08/ezgif-4-95078e96b5.gif" width="40%">

##### 3.明天再补充
```
# todo add support for uploading & downloading files via command line.
```
