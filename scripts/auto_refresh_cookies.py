#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动刷新Cookie脚本
定期从CookieCloud获取最新的cookie并更新配置文件

Usage:
    python scripts/auto_refresh_cookies.py
    python scripts/auto_refresh_cookies.py --interval 3600  # 每小时刷新一次
    python scripts/auto_refresh_cookies.py --once           # 只执行一次
"""

import sys
import time
import argparse
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from crawlers.utils.cookiecloud_manager import get_cookie_manager
from crawlers.utils.logger import logger


class AutoRefreshService:
    """自动刷新Cookie服务"""
    
    def __init__(self, interval: int = 3600):
        """
        初始化自动刷新服务
        
        Args:
            interval: 刷新间隔（秒），默认1小时
        """
        self.interval = interval
        self.manager = get_cookie_manager()
        self.running = False
    
    def refresh_all_cookies(self) -> bool:
        """
        刷新所有平台的cookie
        
        Returns:
            是否全部成功
        """
        if not self.manager.enabled:
            logger.warning("CookieCloud功能未启用，跳过刷新")
            return False
        
        logger.info("开始自动刷新所有平台的cookie...")
        
        results = self.manager.refresh_all_cookies()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info(f"✅ 所有平台cookie刷新成功 ({success_count}/{total_count})")
            return True
        else:
            failed_platforms = [platform for platform, success in results.items() if not success]
            logger.warning(f"⚠️  部分平台cookie刷新失败 ({success_count}/{total_count})，失败平台: {', '.join(failed_platforms)}")
            return False
    
    def run_once(self) -> bool:
        """
        执行一次刷新
        
        Returns:
            是否成功
        """
        try:
            return self.refresh_all_cookies()
        except Exception as e:
            logger.error(f"刷新cookie时发生错误: {e}")
            return False
    
    def run_continuous(self):
        """持续运行刷新服务"""
        self.running = True
        logger.info(f"🚀 启动自动刷新服务，刷新间隔: {self.interval}秒")
        
        # 启动时先执行一次刷新
        logger.info("执行启动时的初始刷新...")
        self.run_once()
        
        try:
            while self.running:
                logger.info(f"⏰ 等待 {self.interval} 秒后进行下次刷新...")
                time.sleep(self.interval)
                
                if self.running:  # 检查是否仍在运行
                    self.run_once()
                    
        except KeyboardInterrupt:
            logger.info("⚠️  收到中断信号，正在停止服务...")
            self.stop()
        except Exception as e:
            logger.error(f"自动刷新服务发生错误: {e}")
            self.stop()
    
    def stop(self):
        """停止刷新服务"""
        self.running = False
        logger.info("🛑 自动刷新服务已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='自动刷新Cookie服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  %(prog)s                    # 使用默认间隔(1小时)持续运行
  %(prog)s --interval 1800    # 每30分钟刷新一次
  %(prog)s --once             # 只执行一次刷新
  %(prog)s --test             # 测试连接但不刷新
        '''
    )
    
    parser.add_argument('--interval', '-i', type=int, default=3600,
                       help='刷新间隔（秒），默认3600秒（1小时）')
    parser.add_argument('--once', action='store_true',
                       help='只执行一次刷新，不持续运行')
    parser.add_argument('--test', action='store_true',
                       help='测试CookieCloud连接，不执行刷新')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细日志')
    
    args = parser.parse_args()
    
    # 显示横幅
    print("""
╔══════════════════════════════════════════════════════════════╗
║                🍪 自动Cookie刷新服务                          ║
║              Douyin_TikTok_Download_API                      ║
║                 Auto Cookie Refresh                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        service = AutoRefreshService(interval=args.interval)
        
        # 检查CookieCloud状态
        if not service.manager.enabled:
            print("❌ CookieCloud功能未启用")
            print("💡 请检查config.yaml中的CookieCloud.Enable设置和.env文件配置")
            sys.exit(1)
        
        if args.test:
            # 测试连接
            print("🔗 测试CookieCloud连接...")
            
            if not service.manager.client:
                print("❌ CookieCloud客户端未初始化")
                sys.exit(1)
            
            try:
                data = service.manager.client.get_decrypted_data()
                if data:
                    total_cookies = sum(len(cookies) for domain, cookies in data.items() 
                                      if domain != 'update_time' and isinstance(cookies, list))
                    print(f"✅ 连接成功！共获取到 {total_cookies} 个cookie")
                else:
                    print("❌ 连接失败：未获取到数据")
                    sys.exit(1)
            except Exception as e:
                print(f"❌ 连接失败: {e}")
                sys.exit(1)
        
        elif args.once:
            # 执行一次刷新
            print("🔄 执行一次性cookie刷新...")
            success = service.run_once()
            sys.exit(0 if success else 1)
        
        else:
            # 持续运行
            service.run_continuous()
    
    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        logger.error(f"自动刷新服务错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
