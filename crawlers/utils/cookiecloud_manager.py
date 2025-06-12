#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CookieCloud Manager - 动态Cookie管理器
用于从CookieCloud获取和缓存cookie，支持自动更新配置文件

Features:
- 从CookieCloud动态获取cookie
- 智能缓存机制，避免频繁请求
- 自动更新配置文件
- 支持多平台（抖音、TikTok、B站等）
- 错误处理和回退机制
"""

import os
import json
import time
import yaml
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# 第三方库
try:
    from PyCookieCloud import PyCookieCloud
    from dotenv import load_dotenv, set_key
    COOKIECLOUD_AVAILABLE = True
except ImportError:
    COOKIECLOUD_AVAILABLE = False

# 日志
from crawlers.utils.logger import logger


class CookieCloudManager:
    """CookieCloud动态Cookie管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化CookieCloud管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录的config.yaml
        """
        # 设置路径
        if config_path is None:
            # 获取项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = Path(config_path)
        self.project_root = self.config_path.parent
        self.env_path = self.project_root / ".env"
        
        # 加载配置
        self._load_config()
        self._load_env()
        
        # 初始化CookieCloud客户端
        self.client = None
        self._init_client()
        
        # 缓存相关
        self.cache = {}
        self.cache_timestamps = {}
        
        logger.info("CookieCloud管理器初始化完成")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 获取CookieCloud配置
            self.cookiecloud_config = self.config.get('CookieCloud', {})
            self.enabled = self.cookiecloud_config.get('Enable', False)
            self.cache_ttl = self.cookiecloud_config.get('Cache_TTL', 3600)
            self.domain_mapping = self.cookiecloud_config.get('Domain_Mapping', {})
            self.fallback_enabled = self.cookiecloud_config.get('Fallback_Enabled', True)
            
            logger.info(f"配置加载成功，CookieCloud启用状态: {self.enabled}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 设置默认值
            self.config = {}
            self.cookiecloud_config = {}
            self.enabled = False
            self.cache_ttl = 3600
            self.domain_mapping = {}
            self.fallback_enabled = True
    
    def _load_env(self):
        """加载环境变量"""
        # 加载.env文件
        load_dotenv(self.env_path)
        
        # 获取CookieCloud配置
        self.server_url = os.getenv('COOKIECLOUD_SERVER_URL', '')
        self.uuid = os.getenv('COOKIECLOUD_UUID', '')
        self.password = os.getenv('COOKIECLOUD_PASSWORD', '')
        
        # 可选配置
        env_cache_ttl = os.getenv('COOKIECLOUD_CACHE_TTL')
        if env_cache_ttl:
            try:
                self.cache_ttl = int(env_cache_ttl)
            except ValueError:
                logger.warning(f"无效的缓存TTL值: {env_cache_ttl}")
        
        self.debug = os.getenv('COOKIECLOUD_DEBUG', 'false').lower() == 'true'
        
        if self.debug:
            logger.info(f"环境变量加载完成 - 服务器: {self.server_url}, UUID: {self.uuid}")
    
    def _init_client(self):
        """初始化CookieCloud客户端"""
        if not COOKIECLOUD_AVAILABLE:
            logger.warning("PyCookieCloud库未安装，CookieCloud功能不可用")
            self.enabled = False
            return
        
        if not self.enabled:
            logger.info("CookieCloud功能已禁用")
            return
        
        if not all([self.server_url, self.uuid, self.password]):
            logger.warning("CookieCloud配置不完整，请检查.env文件")
            self.enabled = False
            return
        
        try:
            self.client = PyCookieCloud(self.server_url, self.uuid, self.password)
            logger.info("CookieCloud客户端初始化成功")
        except Exception as e:
            logger.error(f"CookieCloud客户端初始化失败: {e}")
            self.enabled = False
    
    def _is_cache_valid(self, platform: str) -> bool:
        """检查缓存是否有效"""
        if platform not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[platform]
        current_time = time.time()
        
        return (current_time - cache_time) < self.cache_ttl
    
    def _get_domain_for_platform(self, platform: str) -> str:
        """获取平台对应的域名"""
        return self.domain_mapping.get(platform, f"{platform}.com")
    
    def _format_cookies_for_requests(self, cookies: list) -> str:
        """将cookie列表格式化为requests可用的字符串格式"""
        if not cookies:
            return ""
        
        cookie_pairs = []
        for cookie in cookies:
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            if name and value:
                cookie_pairs.append(f"{name}={value}")
        
        return "; ".join(cookie_pairs)
    
    def get_cookies(self, platform: str, force_refresh: bool = False) -> Optional[str]:
        """
        获取指定平台的cookie
        
        Args:
            platform: 平台名称 (douyin, tiktok, bilibili)
            force_refresh: 是否强制刷新缓存
            
        Returns:
            cookie字符串，失败时返回None
        """
        if not self.enabled:
            logger.debug(f"CookieCloud未启用，跳过{platform}的cookie获取")
            return None
        
        # 检查缓存
        if not force_refresh and self._is_cache_valid(platform):
            logger.debug(f"使用{platform}的缓存cookie")
            return self.cache.get(platform)
        
        try:
            # 从CookieCloud获取数据
            logger.info(f"从CookieCloud获取{platform}的cookie...")
            
            if not self.client:
                logger.error("CookieCloud客户端未初始化")
                return None
            
            # 获取所有cookie数据
            all_cookies = self.client.get_decrypted_data()
            if not all_cookies:
                logger.error("从CookieCloud获取数据失败")
                return None
            
            # 获取目标域名
            target_domain = self._get_domain_for_platform(platform)
            
            # 查找匹配的cookies
            matched_cookies = []
            for domain, cookie_list in all_cookies.items():
                if domain == 'update_time':
                    continue
                
                if isinstance(cookie_list, list):
                    for cookie in cookie_list:
                        cookie_domain = cookie.get('domain', '').lower()
                        
                        # 域名匹配逻辑
                        if (cookie_domain == target_domain or
                            cookie_domain == f".{target_domain}" or
                            target_domain in cookie_domain or
                            cookie_domain.lstrip('.') == target_domain or
                            target_domain.endswith(cookie_domain.lstrip('.'))):
                            matched_cookies.append(cookie)
            
            if not matched_cookies:
                logger.warning(f"未找到{platform}({target_domain})的cookie")
                return None
            
            # 格式化cookie
            cookie_string = self._format_cookies_for_requests(matched_cookies)
            
            # 更新缓存
            self.cache[platform] = cookie_string
            self.cache_timestamps[platform] = time.time()
            
            logger.info(f"成功获取{platform}的cookie，包含{len(matched_cookies)}个cookie")
            
            return cookie_string
            
        except Exception as e:
            logger.error(f"获取{platform}的cookie失败: {e}")
            return None
    
    def update_config_file(self, platform: str, cookie: str) -> bool:
        """
        更新配置文件中的cookie
        
        Args:
            platform: 平台名称
            cookie: cookie字符串
            
        Returns:
            是否更新成功
        """
        try:
            # 确定配置文件路径
            config_file_map = {
                'douyin': self.project_root / 'crawlers' / 'douyin' / 'web' / 'config.yaml',
                'tiktok': self.project_root / 'crawlers' / 'tiktok' / 'web' / 'config.yaml',
                'bilibili': self.project_root / 'crawlers' / 'bilibili' / 'web' / 'config.yaml'
            }
            
            config_file = config_file_map.get(platform)
            if not config_file or not config_file.exists():
                logger.error(f"找不到{platform}的配置文件: {config_file}")
                return False
            
            # 读取配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                platform_config = yaml.safe_load(f)
            
            # 更新cookie
            if platform == 'douyin':
                platform_config['TokenManager']['douyin']['headers']['Cookie'] = cookie
            elif platform == 'tiktok':
                platform_config['TokenManager']['tiktok']['headers']['Cookie'] = cookie
            elif platform == 'bilibili':
                platform_config['TokenManager']['bilibili']['headers']['cookie'] = cookie
            
            # 写回配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(platform_config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            logger.info(f"成功更新{platform}配置文件中的cookie")
            return True
            
        except Exception as e:
            logger.error(f"更新{platform}配置文件失败: {e}")
            return False
    
    def refresh_all_cookies(self) -> Dict[str, bool]:
        """
        刷新所有平台的cookie
        
        Returns:
            各平台刷新结果的字典
        """
        results = {}
        
        for platform in self.domain_mapping.keys():
            logger.info(f"刷新{platform}的cookie...")
            
            # 获取新cookie
            cookie = self.get_cookies(platform, force_refresh=True)
            
            if cookie:
                # 更新配置文件
                success = self.update_config_file(platform, cookie)
                results[platform] = success
                
                if success:
                    logger.info(f"✅ {platform} cookie刷新成功")
                else:
                    logger.error(f"❌ {platform} cookie刷新失败（配置文件更新失败）")
            else:
                results[platform] = False
                logger.error(f"❌ {platform} cookie刷新失败（获取失败）")
        
        return results
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态信息"""
        status = {}
        current_time = time.time()
        
        for platform in self.domain_mapping.keys():
            if platform in self.cache_timestamps:
                cache_time = self.cache_timestamps[platform]
                age = current_time - cache_time
                remaining = max(0, self.cache_ttl - age)
                
                status[platform] = {
                    'cached': True,
                    'cache_age_seconds': int(age),
                    'remaining_seconds': int(remaining),
                    'is_valid': self._is_cache_valid(platform),
                    'last_update': datetime.fromtimestamp(cache_time).isoformat()
                }
            else:
                status[platform] = {
                    'cached': False,
                    'cache_age_seconds': 0,
                    'remaining_seconds': 0,
                    'is_valid': False,
                    'last_update': None
                }
        
        return status


# 全局实例
_cookie_manager = None

def get_cookie_manager() -> CookieCloudManager:
    """获取全局CookieCloud管理器实例"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieCloudManager()
    return _cookie_manager
