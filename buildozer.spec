[app]
# 应用名称（显示在手机桌面）
title = 训练我的第一个分类器

# 应用包名（反向域名，唯一标识）
package.name = garbage_classifier

# 包域（与包名组合成完整包标识符）
package.domain = org.fengxian.school

# 主程序文件
source.dir = .
source.main = app_android.py

# 版本号
version = 1.0

# 依赖包（仅 kivy，无第三方包）
requirements = python3==3.11.0,kivy==2.3.0

# 包含的文件扩展名（py=代码，json=数据，otf/ttf=中文字体）
source.include_exts = py,json,otf,ttf

# 包含中文字体文件（需把字体放在同目录）
source.include_patterns = NotoSansCJKsc-Regular.otf

# 屏幕方向（landscape=横屏，适合课堂展示；portrait=竖屏）
orientation = landscape

# Android 最低 API（Android 5.0 以上均可安装）
android.minapi = 21

# Android 目标 API
android.api = 33

# NDK 版本
android.ndk = 25b

# 权限（读写外部存储，用于保存学生数据）
android.permissions = android.permission.WRITE_EXTERNAL_STORAGE,android.permission.READ_EXTERNAL_STORAGE

# 架构（arm64 = 现代 Android 手机/平板，armeabi-v7a = 旧设备）
android.archs = arm64-v8a, armeabi-v7a

# 自动接受许可证
android.accept_sdk_license = True

# 图标（可选，替换成自己的图标文件）
# icon.filename = %(source.dir)s/icon.png

# 启动画面（可选）
# presplash.filename = %(source.dir)s/presplash.png

# 日志级别（调试时改为 2）
log_level = 1

[buildozer]
# Buildozer 日志级别
log_level = 2

# 是否警告未知的 Kivy 依赖
warn_on_root = 1
