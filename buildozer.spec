[app]

# 应用标题
title = 音乐管理器
package.name = musicmanager
package.domain = org.example

# 版本信息
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# 主文件
main = music_manager.py

# 要求
requirements = python3,kivy==2.1.0,mutagen,pillow

# Android配置
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 30
android.minapi = 21
android.sdk = 24
android.ndk = 23b
android.ndk_api = 21
android.gradle_dependencies = 'com.android.support:support-v4:28.0.0'

# 支持的架构
android.arch = armeabi-v7a,arm64-v8a

# 图标和闪屏
icon.filename = icon.png
presplash.filename = presplash.png

# 方向
orientation = portrait

# 完整屏幕
fullscreen = 0

# 日志级别
log_level = 2

# 打包选项
android.accept_sdk_license = True