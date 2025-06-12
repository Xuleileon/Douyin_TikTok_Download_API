#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CookieCloud 集成测试脚本
测试 CookieCloud 功能是否正常工作

Usage:
    python test_cookiecloud_integration.py
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from crawlers.utils.cookiecloud_manager import get_cookie_manager
from crawlers.douyin.web.web_crawler import DouyinWebCrawler
from crawlers.tiktok.web.web_crawler import TikTokWebCrawler
from crawlers.bilibili.web.web_crawler import BilibiliWebCrawler
from crawlers.utils.logger import logger


class CookieCloudIntegrationTest:
    """CookieCloud 集成测试"""
    
    def __init__(self):
        self.manager = get_cookie_manager()
        self.test_results = {}
    
    def print_banner(self):
        """打印测试横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                🧪 CookieCloud 集成测试                        ║
║              Douyin_TikTok_Download_API                      ║
║                Integration Test Suite                       ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def test_cookiecloud_manager(self):
        """测试 CookieCloud 管理器"""
        print("\n🔧 测试 CookieCloud 管理器...")
        
        try:
            # 测试管理器初始化
            print(f"   ✓ 管理器初始化成功")
            print(f"   - 启用状态: {self.manager.enabled}")
            print(f"   - 服务器URL: {self.manager.server_url}")
            print(f"   - 缓存TTL: {self.manager.cache_ttl}秒")
            print(f"   - 支持平台: {list(self.manager.domain_mapping.keys())}")
            
            # 测试连接（如果启用）
            if self.manager.enabled and self.manager.client:
                print("   🔗 测试连接...")
                data = self.manager.client.get_decrypted_data()
                if data:
                    total_cookies = sum(len(cookies) for domain, cookies in data.items() 
                                      if domain != 'update_time' and isinstance(cookies, list))
                    print(f"   ✓ 连接成功，获取到 {total_cookies} 个cookie")
                    self.test_results['connection'] = True
                else:
                    print("   ❌ 连接失败：未获取到数据")
                    self.test_results['connection'] = False
            else:
                print("   ⚠️  CookieCloud 未启用或未配置")
                self.test_results['connection'] = None
            
            self.test_results['manager'] = True
            
        except Exception as e:
            print(f"   ❌ 管理器测试失败: {e}")
            self.test_results['manager'] = False
    
    def test_cookie_retrieval(self):
        """测试 Cookie 获取"""
        print("\n🍪 测试 Cookie 获取...")
        
        platforms = ['douyin', 'tiktok', 'bilibili']
        
        for platform in platforms:
            try:
                print(f"   📱 测试 {platform} cookie...")
                
                # 获取 cookie
                cookie = self.manager.get_cookies(platform)
                
                if cookie:
                    # 显示 cookie 预览
                    preview = cookie[:50] + "..." if len(cookie) > 50 else cookie
                    print(f"   ✓ {platform} cookie 获取成功")
                    print(f"     预览: {preview}")
                    self.test_results[f'{platform}_cookie'] = True
                else:
                    print(f"   ⚠️  {platform} cookie 未获取到（可能使用回退cookie）")
                    self.test_results[f'{platform}_cookie'] = False
                    
            except Exception as e:
                print(f"   ❌ {platform} cookie 获取失败: {e}")
                self.test_results[f'{platform}_cookie'] = False
    
    async def test_crawler_integration(self):
        """测试爬虫集成"""
        print("\n🕷️  测试爬虫集成...")
        
        # 测试抖音爬虫
        try:
            print("   📱 测试抖音爬虫...")
            douyin_crawler = DouyinWebCrawler()
            headers = await douyin_crawler.get_douyin_headers()
            
            if headers and headers.get('headers', {}).get('Cookie'):
                print("   ✓ 抖音爬虫 headers 获取成功")
                cookie_preview = headers['headers']['Cookie'][:50] + "..."
                print(f"     Cookie预览: {cookie_preview}")
                self.test_results['douyin_crawler'] = True
            else:
                print("   ❌ 抖音爬虫 headers 获取失败")
                self.test_results['douyin_crawler'] = False
                
        except Exception as e:
            print(f"   ❌ 抖音爬虫测试失败: {e}")
            self.test_results['douyin_crawler'] = False
        
        # 测试 TikTok 爬虫
        try:
            print("   📱 测试 TikTok 爬虫...")
            tiktok_crawler = TikTokWebCrawler()
            headers = await tiktok_crawler.get_tiktok_headers()
            
            if headers and headers.get('headers', {}).get('Cookie'):
                print("   ✓ TikTok 爬虫 headers 获取成功")
                cookie_preview = headers['headers']['Cookie'][:50] + "..."
                print(f"     Cookie预览: {cookie_preview}")
                self.test_results['tiktok_crawler'] = True
            else:
                print("   ❌ TikTok 爬虫 headers 获取失败")
                self.test_results['tiktok_crawler'] = False
                
        except Exception as e:
            print(f"   ❌ TikTok 爬虫测试失败: {e}")
            self.test_results['tiktok_crawler'] = False
        
        # 测试 B站 爬虫
        try:
            print("   📱 测试 B站 爬虫...")
            bilibili_crawler = BilibiliWebCrawler()
            headers = await bilibili_crawler.get_bilibili_headers()
            
            if headers and headers.get('headers', {}).get('cookie'):
                print("   ✓ B站 爬虫 headers 获取成功")
                cookie_preview = headers['headers']['cookie'][:50] + "..."
                print(f"     Cookie预览: {cookie_preview}")
                self.test_results['bilibili_crawler'] = True
            else:
                print("   ❌ B站 爬虫 headers 获取失败")
                self.test_results['bilibili_crawler'] = False
                
        except Exception as e:
            print(f"   ❌ B站 爬虫测试失败: {e}")
            self.test_results['bilibili_crawler'] = False
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n💾 测试缓存功能...")
        
        try:
            # 获取缓存状态
            cache_status = self.manager.get_cache_status()
            
            print("   📊 缓存状态:")
            for platform, status in cache_status.items():
                if status['cached']:
                    print(f"     {platform}: ✓ 已缓存 (剩余 {status['remaining_seconds']}秒)")
                else:
                    print(f"     {platform}: ❌ 未缓存")
            
            self.test_results['cache'] = True
            
        except Exception as e:
            print(f"   ❌ 缓存测试失败: {e}")
            self.test_results['cache'] = False
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📋 测试结果总结")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result is True)
        failed_tests = sum(1 for result in self.test_results.values() if result is False)
        skipped_tests = sum(1 for result in self.test_results.values() if result is None)
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✓")
        print(f"失败: {failed_tests} ❌")
        print(f"跳过: {skipped_tests} ⚠️")
        
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            if result is True:
                status = "✓ 通过"
            elif result is False:
                status = "❌ 失败"
            else:
                status = "⚠️  跳过"
            
            print(f"  {test_name}: {status}")
        
        # 总体评估
        if failed_tests == 0:
            if skipped_tests == 0:
                print(f"\n🎉 所有测试通过！CookieCloud 集成工作正常。")
                return True
            else:
                print(f"\n✅ 核心功能正常，部分功能被跳过（通常是因为 CookieCloud 未配置）。")
                return True
        else:
            print(f"\n⚠️  发现 {failed_tests} 个问题，请检查配置和日志。")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.print_banner()
        
        print("开始 CookieCloud 集成测试...")
        
        # 运行测试
        self.test_cookiecloud_manager()
        self.test_cookie_retrieval()
        await self.test_crawler_integration()
        self.test_cache_functionality()
        
        # 打印总结
        success = self.print_summary()
        
        return success


async def main():
    """主函数"""
    test_suite = CookieCloudIntegrationTest()
    
    try:
        success = await test_suite.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        logger.error(f"集成测试错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
