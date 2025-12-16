#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐获取工具模块，支持多种音乐播放器
"""

import win32gui
import win32process
import psutil
import re

# 支持的音乐播放器列表
SUPPORTED_PLAYERS = {
    "QQ音乐": {
        "process_name": "QQMusic.exe",
        "window_class": "OrpheusBrowserHost"
    },
    "酷我音乐": {
        "process_name": "KuwoMusic.exe",
        "window_class": "kwplayer_main_window"
    },
    "网易云音乐": {
        "process_name": "cloudmusic.exe",
        "window_class": "OrpheusBrowserHost"
    },
    "汽水音乐": {
        "process_name": "QSMusic.exe",
        "window_class": "QSMainWindowClass"
    },
    "Spotify": {
        "process_name": "Spotify.exe",
        "window_class": "Chrome_WidgetWin_0"
    },
    "Windows Media Player": {
        "process_name": "wmplayer.exe",
        "window_class": "WMPlayerApp"
    }
}

def get_active_window_info():
    """
    获取当前活动窗口的信息
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        
        # 获取进程ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            return {
                "hwnd": hwnd,
                "window_text": window_text,
                "class_name": class_name,
                "pid": pid,
                "process_name": process_name
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    except Exception:
        return None

def extract_music_info_from_window_title(title, player_name):
    """
    从窗口标题中提取音乐信息
    """
    if not title:
        return None, None
    
    # 去除播放器名称
    title = title.replace(player_name, "").strip()
    
    # 处理常见的音乐信息格式
    # 格式1: 歌曲名 - 艺术家
    match = re.match(r"^(.*?)\s+-\s+(.*?)$", title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # 格式2: 艺术家 - 歌曲名
    match = re.match(r"^(.*?)\s+-\s+(.*?)$", title)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    
    # 如果没有匹配的格式，返回整个标题作为歌曲名
    return title.strip(), ""

def get_current_playing_music():
    """
    获取当前正在播放的音乐信息
    """
    try:
        window_info = get_active_window_info()
        if not window_info:
            return None, None
        
        window_text = window_info["window_text"]
        process_name = window_info["process_name"]
        class_name = window_info["class_name"]
        
        # 检查是否是支持的播放器
        for player_name, player_info in SUPPORTED_PLAYERS.items():
            if process_name == player_info["process_name"] or class_name == player_info["window_class"]:
                # 从窗口标题中提取音乐信息
                song, artist = extract_music_info_from_window_title(window_text, player_name)
                
                # 检查是否是有效的音乐信息（过滤空标题或只包含播放器名称的标题）
                if song and song != player_name:
                    return song, artist
        
        return None, None
    except Exception:
        return None, None

def get_all_running_players():
    """
    获取所有正在运行的支持的音乐播放器
    """
    running_players = []
    
    try:
        # 获取所有运行的进程
        processes = psutil.process_iter()
        
        for process in processes:
            try:
                process_name = process.name()
                
                # 检查是否是支持的播放器
                for player_name, player_info in SUPPORTED_PLAYERS.items():
                    if process_name == player_info["process_name"]:
                        running_players.append(player_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    
    return list(set(running_players))

def get_player_window_by_name(player_name):
    """
    根据播放器名称获取窗口句柄
    """
    if player_name not in SUPPORTED_PLAYERS:
        return None
    
    player_info = SUPPORTED_PLAYERS[player_name]
    target_process = player_info["process_name"]
    target_class = player_info["window_class"]
    
    hwnds = []
    
    def enum_windows_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                if process.name() == target_process:
                    hwnds.append(hwnd)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return True
    
    win32gui.EnumWindows(enum_windows_callback, None)
    
    for hwnd in hwnds:
        if win32gui.GetClassName(hwnd) == target_class:
            return hwnd
    
    return hwnds[0] if hwnds else None

def get_music_from_specific_player(player_name):
    """
    从特定的音乐播放器获取当前播放的音乐
    """
    if player_name not in SUPPORTED_PLAYERS:
        return None, None
    
    hwnd = get_player_window_by_name(player_name)
    if not hwnd:
        return None, None
    
    window_text = win32gui.GetWindowText(hwnd)
    if not window_text:
        return None, None
    
    return extract_music_info_from_window_title(window_text, player_name)
