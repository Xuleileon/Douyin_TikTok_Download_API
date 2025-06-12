#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie管理工具
用于管理CookieCloud的cookie获取、缓存和配置文件更新

Usage:
    python manage_cookies.py --help
    python manage_cookies.py refresh --all
    python manage_cookies.py refresh --platform douyin
    python manage_cookies.py status
    python manage_cookies.py test-connection
"""

import argparse
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from crawlers.utils.cookiecloud_manager import get_cookie_manager
from crawlers.utils.logger import logger


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🍪 Cookie管理工具                          ║
║              Douyin_TikTok_Download_API                      ║
║                   CookieCloud Manager                       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def test_connection():
    """测试CookieCloud连接"""
    print("🔗 测试CookieCloud连接...")
    
    manager = get_cookie_manager()
    
    if not manager.enabled:
        print("❌ CookieCloud功能未启用")
        print("💡 请检查config.yaml中的CookieCloud.Enable设置")
        return False
    
    if not manager.client:
        print("❌ CookieCloud客户端未初始化")
        print("💡 请检查.env文件中的CookieCloud配置")
        return False
    
    try:
        # 尝试获取数据
        print("📡 正在连接CookieCloud服务器...")
        data = manager.client.get_decrypted_data()
        
        if not data:
            print("❌ 连接失败：未获取到数据")
            return False
        
        # 统计信息
        total_cookies = 0
        domains = []
        
        for domain, cookie_list in data.items():
            if domain == 'update_time':
                continue
            if isinstance(cookie_list, list):
                total_cookies += len(cookie_list)
                domains.append((domain, len(cookie_list)))
        
        print("✅ 连接成功！")
        print(f"📊 统计信息:")
        print(f"   - 域名数量: {len(domains)}")
        print(f"   - Cookie总数: {total_cookies}")
        
        if 'update_time' in data:
            print(f"   - 更新时间: {data['update_time']}")
        
        # 显示前5个域名
        if domains:
            print(f"\n🌐 域名列表 (前5个):")
            domains.sort(key=lambda x: x[1], reverse=True)
            for i, (domain, count) in enumerate(domains[:5]):
                print(f"   {i+1}. {domain}: {count} 个cookie")
        
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def show_status():
    """显示缓存状态"""
    print("📊 Cookie缓存状态")
    print("-" * 50)
    
    manager = get_cookie_manager()
    
    if not manager.enabled:
        print("❌ CookieCloud功能未启用")
        return
    
    status = manager.get_cache_status()
    
    for platform, info in status.items():
        print(f"\n🔸 {platform.upper()}:")
        if info['cached']:
            print(f"   ✅ 已缓存")
            print(f"   ⏰ 缓存时间: {info['cache_age_seconds']}秒前")
            print(f"   ⏳ 剩余时间: {info['remaining_seconds']}秒")
            print(f"   📅 最后更新: {info['last_update']}")
            print(f"   🔄 状态: {'有效' if info['is_valid'] else '已过期'}")
        else:
            print(f"   ❌ 未缓存")


def refresh_cookies(platforms=None, all_platforms=False):
    """刷新cookie"""
    manager = get_cookie_manager()
    
    if not manager.enabled:
        print("❌ CookieCloud功能未启用")
        return False
    
    if all_platforms:
        platforms = list(manager.domain_mapping.keys())
    elif not platforms:
        print("❌ 请指定要刷新的平台或使用 --all 刷新所有平台")
        return False
    
    print(f"🔄 开始刷新cookie...")
    print(f"📋 目标平台: {', '.join(platforms)}")
    print("-" * 50)
    
    results = {}
    
    for platform in platforms:
        if platform not in manager.domain_mapping:
            print(f"❌ 不支持的平台: {platform}")
            results[platform] = False
            continue
        
        print(f"\n🔄 刷新 {platform.upper()} cookie...")
        
        # 获取cookie
        cookie = manager.get_cookies(platform, force_refresh=True)
        
        if cookie:
            # 更新配置文件
            success = manager.update_config_file(platform, cookie)
            results[platform] = success
            
            if success:
                print(f"✅ {platform} cookie刷新成功")
                # 显示cookie预览（前50个字符）
                preview = cookie[:50] + "..." if len(cookie) > 50 else cookie
                print(f"   📝 Cookie预览: {preview}")
            else:
                print(f"❌ {platform} cookie刷新失败（配置文件更新失败）")
        else:
            results[platform] = False
            print(f"❌ {platform} cookie刷新失败（获取失败）")
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 刷新结果总结:")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for platform, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {platform}: {status}")
    
    print(f"\n🎯 总计: {success_count}/{total_count} 成功")
    
    return success_count == total_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Cookie管理工具 - 管理CookieCloud的cookie获取和缓存',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  %(prog)s test-connection              # 测试CookieCloud连接
  %(prog)s status                      # 显示缓存状态
  %(prog)s refresh --all               # 刷新所有平台的cookie
  %(prog)s refresh --platform douyin   # 刷新抖音cookie
  %(prog)s refresh --platform douyin tiktok  # 刷新多个平台
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 测试连接命令
    subparsers.add_parser('test-connection', help='测试CookieCloud连接')
    
    # 状态命令
    subparsers.add_parser('status', help='显示cookie缓存状态')
    
    # 刷新命令
    refresh_parser = subparsers.add_parser('refresh', help='刷新cookie')
    refresh_group = refresh_parser.add_mutually_exclusive_group(required=True)
    refresh_group.add_argument('--all', action='store_true', help='刷新所有平台的cookie')
    refresh_group.add_argument('--platform', nargs='+', 
                              choices=['douyin', 'tiktok', 'bilibili'],
                              help='指定要刷新的平台')
    
    args = parser.parse_args()
    
    # 显示横幅
    print_banner()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'test-connection':
            success = test_connection()
            sys.exit(0 if success else 1)
            
        elif args.command == 'status':
            show_status()
            
        elif args.command == 'refresh':
            if args.all:
                success = refresh_cookies(all_platforms=True)
            else:
                success = refresh_cookies(platforms=args.platform)
            
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.error(f"管理工具错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
