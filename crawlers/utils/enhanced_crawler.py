#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Crawler - 增强的爬虫基类
集成CookieCloud动态cookie管理功能

Features:
- 自动从CookieCloud获取最新cookie
- 智能回退到硬编码cookie
- 统一的header管理接口
- 错误处理和重试机制
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# 导入CookieCloud管理器
from crawlers.utils.cookiecloud_manager import get_cookie_manager
from crawlers.utils.logger import logger


class EnhancedCrawlerMixin:
    """增强爬虫混入类，为现有爬虫添加CookieCloud支持"""
    
    def __init__(self):
        """初始化增强爬虫功能"""
        self.cookie_manager = get_cookie_manager()
        self._platform_name = None
        self._config_cache = {}
    
    def _get_platform_name(self) -> str:
        """获取当前平台名称（由子类实现）"""
        if self._platform_name:
            return self._platform_name
        
        # 尝试从类名推断平台名称
        class_name = self.__class__.__name__.lower()
        if 'douyin' in class_name:
            self._platform_name = 'douyin'
        elif 'tiktok' in class_name:
            self._platform_name = 'tiktok'
        elif 'bilibili' in class_name:
            self._platform_name = 'bilibili'
        else:
            logger.warning(f"无法从类名 {self.__class__.__name__} 推断平台名称")
            self._platform_name = 'unknown'
        
        return self._platform_name
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path in self._config_cache:
            return self._config_cache[config_path]
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self._config_cache[config_path] = config
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return {}
    
    def _get_fallback_cookie(self, platform: str, config_path: str) -> str:
        """获取回退cookie（从配置文件读取硬编码cookie）"""
        try:
            config = self._load_config_file(config_path)
            
            if platform == 'douyin':
                return config.get('TokenManager', {}).get('douyin', {}).get('headers', {}).get('Cookie', '')
            elif platform == 'tiktok':
                return config.get('TokenManager', {}).get('tiktok', {}).get('headers', {}).get('Cookie', '')
            elif platform == 'bilibili':
                return config.get('TokenManager', {}).get('bilibili', {}).get('headers', {}).get('cookie', '')
            
        except Exception as e:
            logger.error(f"获取{platform}回退cookie失败: {e}")
        
        return ""
    
    def get_enhanced_headers(self, config_path: str, platform: str = None) -> Dict[str, Any]:
        """
        获取增强的请求头，优先使用CookieCloud的cookie
        
        Args:
            config_path: 配置文件路径
            platform: 平台名称，如果不提供则自动推断
            
        Returns:
            包含headers和proxies的字典
        """
        if platform is None:
            platform = self._get_platform_name()
        
        # 加载基础配置
        config = self._load_config_file(config_path)
        if not config:
            logger.error(f"无法加载配置文件: {config_path}")
            return {"headers": {}, "proxies": {}}
        
        # 获取基础配置
        try:
            if platform == 'douyin':
                platform_config = config['TokenManager']['douyin']
                base_headers = {
                    "Accept-Language": platform_config["headers"]["Accept-Language"],
                    "User-Agent": platform_config["headers"]["User-Agent"],
                    "Referer": platform_config["headers"]["Referer"],
                }
                fallback_cookie = platform_config["headers"]["Cookie"]
                
            elif platform == 'tiktok':
                platform_config = config['TokenManager']['tiktok']
                base_headers = {
                    "User-Agent": platform_config["headers"]["User-Agent"],
                    "Referer": platform_config["headers"]["Referer"],
                }
                fallback_cookie = platform_config["headers"]["Cookie"]
                
            elif platform == 'bilibili':
                platform_config = config['TokenManager']['bilibili']
                base_headers = {
                    "accept-language": platform_config["headers"]["accept-language"],
                    "origin": platform_config["headers"]["origin"],
                    "referer": platform_config["headers"]["referer"],
                    "user-agent": platform_config["headers"]["user-agent"],
                }
                fallback_cookie = platform_config["headers"]["cookie"]
                
            else:
                logger.error(f"不支持的平台: {platform}")
                return {"headers": {}, "proxies": {}}
            
            # 获取代理配置
            proxies = {
                "http://": platform_config["proxies"]["http"],
                "https://": platform_config["proxies"]["https"]
            }
            
        except KeyError as e:
            logger.error(f"配置文件格式错误，缺少字段: {e}")
            return {"headers": {}, "proxies": {}}
        
        # 尝试从CookieCloud获取cookie
        dynamic_cookie = None
        if self.cookie_manager.enabled:
            try:
                dynamic_cookie = self.cookie_manager.get_cookies(platform)
                if dynamic_cookie:
                    logger.info(f"使用CookieCloud的{platform} cookie")
                else:
                    logger.warning(f"CookieCloud未返回{platform} cookie，使用回退cookie")
            except Exception as e:
                logger.error(f"从CookieCloud获取{platform} cookie失败: {e}")
        
        # 选择cookie
        final_cookie = dynamic_cookie if dynamic_cookie else fallback_cookie
        
        if not final_cookie:
            logger.warning(f"{platform}没有可用的cookie")
        
        # 设置cookie到headers
        if platform == 'bilibili':
            base_headers["cookie"] = final_cookie
        else:
            base_headers["Cookie"] = final_cookie
        
        return {
            "headers": base_headers,
            "proxies": proxies
        }


def create_enhanced_crawler_class(base_class):
    """
    创建增强的爬虫类，为现有爬虫类添加CookieCloud支持
    
    Args:
        base_class: 原始爬虫类
        
    Returns:
        增强后的爬虫类
    """
    
    class EnhancedCrawler(base_class, EnhancedCrawlerMixin):
        """增强的爬虫类"""
        
        def __init__(self, *args, **kwargs):
            # 初始化基类
            if hasattr(base_class, '__init__'):
                base_class.__init__(self, *args, **kwargs)
            
            # 初始化增强功能
            EnhancedCrawlerMixin.__init__(self)
        
        # 重写获取headers的方法（如果存在）
        async def get_douyin_headers(self):
            """获取抖音请求头（增强版）"""
            if hasattr(self, '_get_platform_name') and self._get_platform_name() == 'douyin':
                config_path = os.path.join(os.path.dirname(__file__), '..', 'douyin', 'web', 'config.yaml')
                return self.get_enhanced_headers(config_path, 'douyin')
            elif hasattr(super(), 'get_douyin_headers'):
                return await super().get_douyin_headers()
            else:
                return {"headers": {}, "proxies": {}}
        
        async def get_tiktok_headers(self):
            """获取TikTok请求头（增强版）"""
            if hasattr(self, '_get_platform_name') and self._get_platform_name() == 'tiktok':
                config_path = os.path.join(os.path.dirname(__file__), '..', 'tiktok', 'web', 'config.yaml')
                return self.get_enhanced_headers(config_path, 'tiktok')
            elif hasattr(super(), 'get_tiktok_headers'):
                return await super().get_tiktok_headers()
            else:
                return {"headers": {}, "proxies": {}}
        
        async def get_bilibili_headers(self):
            """获取B站请求头（增强版）"""
            if hasattr(self, '_get_platform_name') and self._get_platform_name() == 'bilibili':
                config_path = os.path.join(os.path.dirname(__file__), '..', 'bilibili', 'web', 'config.yaml')
                return self.get_enhanced_headers(config_path, 'bilibili')
            elif hasattr(super(), 'get_bilibili_headers'):
                return await super().get_bilibili_headers()
            else:
                return {"headers": {}, "proxies": {}}
    
    # 设置类名
    EnhancedCrawler.__name__ = f"Enhanced{base_class.__name__}"
    EnhancedCrawler.__qualname__ = f"Enhanced{base_class.__qualname__}"
    
    return EnhancedCrawler
