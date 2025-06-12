#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CookieCloud API端点
提供CookieCloud管理相关的API接口

Features:
- 获取缓存状态
- 刷新cookie
- 测试连接
- 配置管理
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

# 导入CookieCloud管理器
from crawlers.utils.cookiecloud_manager import get_cookie_manager
from crawlers.utils.logger import logger

# 创建路由器
router = APIRouter()


# 响应模型
class CookieCloudStatusResponse(BaseModel):
    """CookieCloud状态响应"""
    enabled: bool
    cache_status: Dict[str, Any]
    server_url: Optional[str] = None
    last_error: Optional[str] = None


class RefreshCookieRequest(BaseModel):
    """刷新Cookie请求"""
    platforms: Optional[List[str]] = None
    force_refresh: bool = False


class RefreshCookieResponse(BaseModel):
    """刷新Cookie响应"""
    success: bool
    results: Dict[str, bool]
    message: str


class ConnectionTestResponse(BaseModel):
    """连接测试响应"""
    success: bool
    message: str
    server_info: Optional[Dict[str, Any]] = None


@router.get("/status", response_model=CookieCloudStatusResponse, summary="获取CookieCloud状态")
async def get_cookiecloud_status():
    """
    获取CookieCloud的当前状态信息
    
    Returns:
        CookieCloud状态信息，包括启用状态、缓存状态等
    """
    try:
        manager = get_cookie_manager()
        
        # 获取缓存状态
        cache_status = manager.get_cache_status()
        
        # 构建响应
        response = CookieCloudStatusResponse(
            enabled=manager.enabled,
            cache_status=cache_status,
            server_url=manager.server_url if manager.enabled else None
        )
        
        return response
        
    except Exception as e:
        logger.error(f"获取CookieCloud状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/test-connection", response_model=ConnectionTestResponse, summary="测试CookieCloud连接")
async def test_cookiecloud_connection():
    """
    测试与CookieCloud服务器的连接
    
    Returns:
        连接测试结果
    """
    try:
        manager = get_cookie_manager()
        
        if not manager.enabled:
            return ConnectionTestResponse(
                success=False,
                message="CookieCloud功能未启用"
            )
        
        if not manager.client:
            return ConnectionTestResponse(
                success=False,
                message="CookieCloud客户端未初始化，请检查配置"
            )
        
        # 尝试获取数据
        data = manager.client.get_decrypted_data()
        
        if not data:
            return ConnectionTestResponse(
                success=False,
                message="连接失败：未获取到数据"
            )
        
        # 统计信息
        total_cookies = 0
        domains = []
        
        for domain, cookie_list in data.items():
            if domain == 'update_time':
                continue
            if isinstance(cookie_list, list):
                total_cookies += len(cookie_list)
                domains.append(domain)
        
        server_info = {
            "total_domains": len(domains),
            "total_cookies": total_cookies,
            "update_time": data.get('update_time'),
            "sample_domains": domains[:5]  # 前5个域名作为示例
        }
        
        return ConnectionTestResponse(
            success=True,
            message="连接成功",
            server_info=server_info
        )
        
    except Exception as e:
        logger.error(f"测试CookieCloud连接失败: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"连接测试失败: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshCookieResponse, summary="刷新Cookie")
async def refresh_cookies(request: RefreshCookieRequest, background_tasks: BackgroundTasks):
    """
    刷新指定平台的cookie
    
    Args:
        request: 刷新请求，包含平台列表和是否强制刷新
        background_tasks: 后台任务，用于异步执行刷新操作
        
    Returns:
        刷新结果
    """
    try:
        manager = get_cookie_manager()
        
        if not manager.enabled:
            return RefreshCookieResponse(
                success=False,
                results={},
                message="CookieCloud功能未启用"
            )
        
        # 确定要刷新的平台
        if request.platforms:
            platforms = request.platforms
            # 验证平台名称
            valid_platforms = set(manager.domain_mapping.keys())
            invalid_platforms = set(platforms) - valid_platforms
            if invalid_platforms:
                return RefreshCookieResponse(
                    success=False,
                    results={},
                    message=f"不支持的平台: {', '.join(invalid_platforms)}"
                )
        else:
            # 如果没有指定平台，刷新所有平台
            platforms = list(manager.domain_mapping.keys())
        
        # 执行刷新
        results = {}
        success_count = 0
        
        for platform in platforms:
            try:
                # 获取cookie
                cookie = manager.get_cookies(platform, force_refresh=request.force_refresh)
                
                if cookie:
                    # 更新配置文件
                    update_success = manager.update_config_file(platform, cookie)
                    results[platform] = update_success
                    if update_success:
                        success_count += 1
                        logger.info(f"成功刷新{platform}的cookie")
                    else:
                        logger.error(f"刷新{platform}的cookie失败：配置文件更新失败")
                else:
                    results[platform] = False
                    logger.error(f"刷新{platform}的cookie失败：获取cookie失败")
                    
            except Exception as e:
                results[platform] = False
                logger.error(f"刷新{platform}的cookie时发生错误: {e}")
        
        # 构建响应
        total_count = len(platforms)
        success = success_count == total_count
        
        message = f"刷新完成：{success_count}/{total_count} 成功"
        if not success:
            failed_platforms = [p for p, r in results.items() if not r]
            message += f"，失败的平台: {', '.join(failed_platforms)}"
        
        return RefreshCookieResponse(
            success=success,
            results=results,
            message=message
        )
        
    except Exception as e:
        logger.error(f"刷新cookie失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新失败: {str(e)}")


@router.get("/platforms", summary="获取支持的平台列表")
async def get_supported_platforms():
    """
    获取支持的平台列表
    
    Returns:
        支持的平台列表和域名映射
    """
    try:
        manager = get_cookie_manager()
        
        return {
            "platforms": list(manager.domain_mapping.keys()),
            "domain_mapping": manager.domain_mapping,
            "enabled": manager.enabled
        }
        
    except Exception as e:
        logger.error(f"获取平台列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取平台列表失败: {str(e)}")


@router.delete("/cache", summary="清除Cookie缓存")
async def clear_cookie_cache():
    """
    清除所有平台的cookie缓存
    
    Returns:
        清除结果
    """
    try:
        manager = get_cookie_manager()
        
        # 清除缓存
        manager.cache.clear()
        manager.cache_timestamps.clear()
        
        logger.info("Cookie缓存已清除")
        
        return {
            "success": True,
            "message": "Cookie缓存已清除"
        }
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.get("/config", summary="获取CookieCloud配置信息")
async def get_cookiecloud_config():
    """
    获取CookieCloud的配置信息（不包含敏感信息）
    
    Returns:
        配置信息
    """
    try:
        manager = get_cookie_manager()
        
        # 返回非敏感的配置信息
        config_info = {
            "enabled": manager.enabled,
            "cache_ttl": manager.cache_ttl,
            "domain_mapping": manager.domain_mapping,
            "fallback_enabled": manager.fallback_enabled,
            "server_configured": bool(manager.server_url),
            "client_initialized": bool(manager.client)
        }
        
        return config_info
        
    except Exception as e:
        logger.error(f"获取配置信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置信息失败: {str(e)}")
