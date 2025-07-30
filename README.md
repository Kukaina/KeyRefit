# 关于KeyRefit
KeyRefit是一个使用pywebview + Vue3结合hook实现的按键映射程序,可用于为不支持自定义键位的游戏添加支持具有以下特点

- [x] 基于NaiveUI的用户界面
- [x] 为不同游戏分别进行映射配置
- [x] 精确和模糊两种窗口匹配
- [x] 自动按键识别和按键选择



但需要注意的是受技术限制,暂时无法在其最小化后恢复窗口

以及点击x号后默认最小化至系统托盘,退出需要右键系统托盘

# 运行教程

## 从release运行

您可以直接从项目的release下下载安装文件进行安装运行

## 从源码运行

由于使用软件主要使用了Windows相关API因此暂时只支持在Windows下运行,在运行前请确保你的电脑上已经安装了`git` `uv` `python` `pnpm`

首先克隆本项目代码

```shell
git clone https://github.com/Kukaina/KeyRefit.git
```

得到KeyRefit文件夹

- UI文件夹存放了Vue3相关代码,首次运行要前往UI/keyrefi_ui目录下安装相关依赖

  ```
  pnpm i
  ```
然后直接运行`build.bat`即可,如果运行失败请手动完成以下操作

1. 在/UI/keyrefit_ui/下执行

   ```
    pnpm run build
   ```
2. 将编译产生的dist文件夹下的内容(不包含dist文件夹)复制到根目录下的vue_dist目录(没有则创建一个)

3. 在根目录下运行

   ```
   uv run main.py
   ```

   

## 修改dll

如需修改dll代码请使用Vs2022打开根目录下的`keyrefit_hook\keyrefit_hook.sln`文件



# 如何编译

本项目使用nuitka进行打包,在编译前请先将nuitka升级至最新版

然后执行打包命令

```bash
nuitka --standalone --windows-disable-console --include-data-dir=vue_dist=vue_dist --include-data-dir=config=config --windows-icon-from-ico=icon.png --follow-imports --include-module=webview --nofollow-import-to=webview.platforms.android --nofollow-import-to=webview.platforms.gtk --nofollow-import-to=webview.platforms.qt --nofollow-import-to=webview.platforms.cocoa --include-data-files=hook.dll=./ --include-data-files=iconx64.png=./  main.py
```

编译产物就在main.dist下
