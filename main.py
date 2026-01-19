# -*- coding: utf-8 -*-
"""
音乐元数据管理器 - Android版
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

import os
import json
from pathlib import Path

# 尝试导入音频元数据库
try:
    from mutagen import File as MutagenFile
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("警告: mutagen未安装,某些功能将受限")


class MusicFile:
    """音乐文件类,封装元数据"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.duration = ""
        
        self.load_metadata()
    
    def load_metadata(self):
        """加载音频元数据"""
        if not MUTAGEN_AVAILABLE:
            self.title = self.filename
            return
        
        try:
            audio = MutagenFile(self.filepath, easy=True)
            if audio is None:
                self.title = self.filename
                return
            
            # 提取元数据
            self.title = audio.get('title', [self.filename])[0] if 'title' in audio else self.filename
            self.artist = audio.get('artist', ['未知艺术家'])[0] if 'artist' in audio else '未知艺术家'
            self.album = audio.get('album', ['未知专辑'])[0] if 'album' in audio else '未知专辑'
            self.year = audio.get('date', [''])[0] if 'date' in audio else ''
            self.genre = audio.get('genre', [''])[0] if 'genre' in audio else ''
            
            # 获取时长
            if hasattr(audio.info, 'length'):
                duration_sec = int(audio.info.length)
                minutes = duration_sec // 60
                seconds = duration_sec % 60
                self.duration = f"{minutes}:{seconds:02d}"
                
        except Exception as e:
            print(f"加载元数据失败: {e}")
            self.title = self.filename
    
    def save_metadata(self, title, artist, album, year, genre):
        """保存音频元数据"""
        if not MUTAGEN_AVAILABLE:
            return False
        
        try:
            audio = MutagenFile(self.filepath, easy=True)
            if audio is None:
                return False
            
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            if year:
                audio['date'] = year
            if genre:
                audio['genre'] = genre
            
            audio.save()
            
            # 更新本地数据
            self.title = title
            self.artist = artist
            self.album = album
            self.year = year
            self.genre = genre
            
            return True
        except Exception as e:
            print(f"保存元数据失败: {e}")
            return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            'filepath': self.filepath,
            'filename': self.filename,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'year': self.year,
            'genre': self.genre,
            'duration': self.duration
        }


class MusicListItem(BoxLayout):
    """音乐列表项组件"""
    title = StringProperty("")
    artist = StringProperty("")
    duration = StringProperty("")
    music_file = ObjectProperty(None)
    
    def __init__(self, music_file, **kwargs):
        super().__init__(**kwargs)
        self.music_file = music_file
        self.title = music_file.title
        self.artist = music_file.artist
        self.duration = music_file.duration
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # 淡入动画
        self.opacity = 0
        anim = Animation(opacity=1, duration=0.3)
        anim.start(self)


class MainScreen(Screen):
    """主屏幕 - 显示音乐列表"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.music_files = []
        self.filtered_files = []
        Clock.schedule_once(self.init_ui, 0)
    
    def init_ui(self, dt):
        """初始化UI"""
        self.load_music_files()
    
    def get_music_directories(self):
        """获取音乐目录路径"""
        if platform == 'android':
            from android.storage import primary_external_storage_path
            from android.permissions import request_permissions, Permission
            
            # 请求权限
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            
            storage_path = primary_external_storage_path()
            music_dirs = [
                os.path.join(storage_path, 'Music'),
                os.path.join(storage_path, 'Download'),
                storage_path
            ]
        else:
            # 桌面系统的音乐目录
            home = str(Path.home())
            music_dirs = [
                os.path.join(home, 'Music'),
                os.path.join(home, 'Downloads'),
                home
            ]
        
        return [d for d in music_dirs if os.path.exists(d)]
    
    def load_music_files(self):
        """加载音乐文件"""
        self.music_files = []
        audio_extensions = ('.mp3', '.flac', '.m4a', '.ogg', '.wav', '.opus')
        
        music_dirs = self.get_music_directories()
        
        for music_dir in music_dirs:
            try:
                for root, dirs, files in os.walk(music_dir):
                    for file in files:
                        if file.lower().endswith(audio_extensions):
                            filepath = os.path.join(root, file)
                            music_file = MusicFile(filepath)
                            self.music_files.append(music_file)
                    
                    # 只扫描第一层子目录以提高性能
                    if root != music_dir:
                        break
            except Exception as e:
                print(f"扫描目录失败 {music_dir}: {e}")
        
        self.filtered_files = self.music_files.copy()
        self.update_music_list()
    
    def update_music_list(self):
        """更新音乐列表显示"""
        container = self.ids.music_list_container
        container.clear_widgets()
        
        if not self.filtered_files:
            no_music_label = Label(
                text="未找到音乐文件\n请将音乐放入Music或Download文件夹",
                halign='center',
                size_hint_y=None,
                height=dp(100)
            )
            container.add_widget(no_music_label)
            return
        
        for music_file in self.filtered_files:
            item = MusicListItem(music_file)
            item.bind(on_touch_down=lambda instance, touch, mf=music_file: 
                     self.on_music_item_click(instance, touch, mf))
            container.add_widget(item)
    
    def on_music_item_click(self, instance, touch, music_file):
        """音乐项点击事件"""
        if instance.collide_point(*touch.pos):
            self.show_detail_screen(music_file)
            return True
    
    def show_detail_screen(self, music_file):
        """显示详情屏幕"""
        detail_screen = self.manager.get_screen('detail')
        detail_screen.set_music_file(music_file)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'detail'
    
    def search_music(self, search_text):
        """搜索音乐"""
        if not search_text:
            self.filtered_files = self.music_files.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_files = [
                mf for mf in self.music_files
                if search_lower in mf.title.lower() or 
                   search_lower in mf.artist.lower() or
                   search_lower in mf.album.lower()
            ]
        
        self.update_music_list()
    
    def refresh_list(self):
        """刷新列表"""
        # 旋转动画
        refresh_btn = self.ids.refresh_button
        anim = Animation(rotation=360, duration=0.5)
        anim.bind(on_complete=lambda *args: setattr(refresh_btn, 'rotation', 0))
        anim.start(refresh_btn)
        
        self.load_music_files()


class DetailScreen(Screen):
    """详情屏幕 - 显示和编辑元数据"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_music_file = None
    
    def set_music_file(self, music_file):
        """设置当前音乐文件"""
        self.current_music_file = music_file
        
        # 更新UI
        self.ids.title_input.text = music_file.title
        self.ids.artist_input.text = music_file.artist
        self.ids.album_input.text = music_file.album
        self.ids.year_input.text = music_file.year
        self.ids.genre_input.text = music_file.genre
        self.ids.filename_label.text = f"文件名: {music_file.filename}"
        self.ids.duration_label.text = f"时长: {music_file.duration}"
    
    def save_metadata(self):
        """保存元数据"""
        if not self.current_music_file:
            return
        
        title = self.ids.title_input.text
        artist = self.ids.artist_input.text
        album = self.ids.album_input.text
        year = self.ids.year_input.text
        genre = self.ids.genre_input.text
        
        if self.current_music_file.save_metadata(title, artist, album, year, genre):
            self.show_toast("保存成功!")
            # 返回主屏幕
            Clock.schedule_once(lambda dt: self.go_back(), 1)
        else:
            self.show_toast("保存失败,请检查权限")
    
    def go_back(self):
        """返回主屏幕"""
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'main'
        # 刷新主屏幕列表
        main_screen = self.manager.get_screen('main')
        main_screen.update_music_list()
    
    def show_toast(self, message):
        """显示提示消息"""
        toast = Label(
            text=message,
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        popup = Popup(
            content=toast,
            size_hint=(None, None),
            size=(dp(200), dp(100)),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0.8)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)


class MusicMetadataApp(App):
    """音乐元数据管理器主应用"""
    
    def build(self):
        Window.clearcolor = (0.95, 0.95, 0.95, 1)
        
        # 创建屏幕管理器
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(DetailScreen(name='detail'))
        
        return sm
    
    def on_start(self):
        """应用启动时"""
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])


if __name__ == '__main__':
    MusicMetadataApp().run()
