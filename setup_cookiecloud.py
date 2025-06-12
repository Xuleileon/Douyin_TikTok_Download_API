#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CookieCloud 快速配置脚本
帮助用户快速配置和测试CookieCloud功能

Usage:
    python setup_cookiecloud.py
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import set_key, load_dotenv

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                🍪 CookieCloud 快速配置                        ║
║              Douyin_TikTok_Download_API                      ║
║                   Setup Assistant                           ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    try:
        import PyCookieCloud
        print("   ✓ PyCookieCloud 已安装")
    except ImportError:
        print("   ❌ PyCookieCloud 未安装")
        print("   💡 请运行: pip install PyCookieCloud>=1.0.4")
        return False
    
    try:
        import dotenv
        print("   ✓ python-dotenv 已安装")
    except ImportError:
        print("   ❌ python-dotenv 未安装")
        print("   💡 请运行: pip install python-dotenv>=0.19.0")
        return False
    
    return True

def setup_env_file():
    """设置.env文件"""
    print("\n🔧 配置 .env 文件...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    # 如果.env不存在但.env.example存在，复制它
    if not env_path.exists() and env_example_path.exists():
        print("   📋 从 .env.example 创建 .env 文件...")
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("   ✓ .env 文件已创建")
    elif not env_path.exists():
        print("   📝 创建新的 .env 文件...")
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("""# CookieCloud Configuration
# CookieCloud服务器配置

# CookieCloud server URL | CookieCloud服务器地址
COOKIECLOUD_SERVER_URL=

# CookieCloud UUID | CookieCloud用户UUID
COOKIECLOUD_UUID=

# CookieCloud password | CookieCloud加密密码
COOKIECLOUD_PASSWORD=

# Default output format for cookie utility | Cookie工具默认输出格式
DEFAULT_OUTPUT_FORMAT=json

# Optional: Override cache TTL (seconds) | 可选：覆盖缓存生存时间（秒）
# COOKIECLOUD_CACHE_TTL=3600

# Optional: Enable debug logging | 可选：启用调试日志
# COOKIECLOUD_DEBUG=false
""")
        print("   ✓ .env 文件已创建")
    
    # 加载现有配置
    load_dotenv(env_path)
    
    # 获取用户输入
    print("\n   请输入CookieCloud配置信息:")
    
    current_url = os.getenv('COOKIECLOUD_SERVER_URL', '')
    server_url = input(f"   CookieCloud服务器地址 [{current_url}]: ").strip()
    if server_url:
        set_key(env_path, 'COOKIECLOUD_SERVER_URL', server_url)
    elif not current_url:
        print("   ⚠️  服务器地址为空，请稍后手动配置")
    
    current_uuid = os.getenv('COOKIECLOUD_UUID', '')
    uuid = input(f"   CookieCloud UUID [{current_uuid}]: ").strip()
    if uuid:
        set_key(env_path, 'COOKIECLOUD_UUID', uuid)
    elif not current_uuid:
        print("   ⚠️  UUID为空，请稍后手动配置")
    
    current_password = os.getenv('COOKIECLOUD_PASSWORD', '')
    password = input(f"   CookieCloud密码 [{'*' * len(current_password) if current_password else ''}]: ").strip()
    if password:
        set_key(env_path, 'COOKIECLOUD_PASSWORD', password)
    elif not current_password:
        print("   ⚠️  密码为空，请稍后手动配置")
    
    print("   ✓ .env 文件配置完成")

def setup_config_yaml():
    """设置config.yaml文件"""
    print("\n⚙️  配置 config.yaml...")
    
    config_path = Path("config.yaml")
    
    if not config_path.exists():
        print("   ❌ config.yaml 文件不存在")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查是否已有CookieCloud配置
        if 'CookieCloud' not in config:
            print("   📝 添加 CookieCloud 配置...")
            config['CookieCloud'] = {
                'Enable': True,
                'Cache_TTL': 3600,
                'Domain_Mapping': {
                    'douyin': 'douyin.com',
                    'tiktok': 'tiktok.com',
                    'bilibili': 'bilibili.com'
                },
                'Fallback_Enabled': True
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print("   ✓ CookieCloud 配置已添加到 config.yaml")
        else:
            print("   ✓ config.yaml 中已存在 CookieCloud 配置")
            
            # 询问是否启用
            current_enabled = config['CookieCloud'].get('Enable', False)
            enable_input = input(f"   是否启用 CookieCloud? (y/n) [{('y' if current_enabled else 'n')}]: ").strip().lower()
            
            if enable_input == 'y' or (enable_input == '' and current_enabled):
                config['CookieCloud']['Enable'] = True
                print("   ✓ CookieCloud 已启用")
            elif enable_input == 'n' or (enable_input == '' and not current_enabled):
                config['CookieCloud']['Enable'] = False
                print("   ⚠️  CookieCloud 已禁用")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置 config.yaml 失败: {e}")
        return False

def test_connection():
    """测试连接"""
    print("\n🔗 测试 CookieCloud 连接...")
    
    try:
        # 重新加载环境变量
        load_dotenv()
        
        server_url = os.getenv('COOKIECLOUD_SERVER_URL')
        uuid = os.getenv('COOKIECLOUD_UUID')
        password = os.getenv('COOKIECLOUD_PASSWORD')
        
        if not all([server_url, uuid, password]):
            print("   ❌ 配置信息不完整，跳过连接测试")
            return False
        
        from PyCookieCloud import PyCookieCloud
        
        client = PyCookieCloud(server_url, uuid, password)
        data = client.get_decrypted_data()
        
        if data:
            total_cookies = sum(len(cookies) for domain, cookies in data.items() 
                              if domain != 'update_time' and isinstance(cookies, list))
            domains = [domain for domain in data.keys() if domain != 'update_time']
            
            print("   ✅ 连接成功！")
            print(f"   📊 统计信息:")
            print(f"      - 域名数量: {len(domains)}")
            print(f"      - Cookie总数: {total_cookies}")
            
            if 'update_time' in data:
                print(f"      - 更新时间: {data['update_time']}")
            
            # 检查目标域名
            target_domains = ['douyin.com', 'tiktok.com', 'bilibili.com']
            found_domains = []
            
            for target in target_domains:
                for domain in domains:
                    if target in domain or domain.endswith(target):
                        found_domains.append(target)
                        break
            
            if found_domains:
                print(f"   🎯 找到目标域名: {', '.join(found_domains)}")
            else:
                print("   ⚠️  未找到目标域名的Cookie，请确保浏览器已登录相关网站")
            
            return True
        else:
            print("   ❌ 连接失败：未获取到数据")
            return False
            
    except ImportError:
        print("   ❌ PyCookieCloud 库未安装")
        return False
    except Exception as e:
        print(f"   ❌ 连接测试失败: {e}")
        return False

def run_integration_test():
    """运行集成测试"""
    print("\n🧪 运行集成测试...")
    
    test_script = Path("test_cookiecloud_integration.py")
    if test_script.exists():
        print("   🚀 启动集成测试脚本...")
        os.system(f"python {test_script}")
    else:
        print("   ⚠️  集成测试脚本不存在，跳过测试")

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "="*60)
    print("🎉 配置完成！后续步骤:")
    print("="*60)
    
    print("\n1. 🔧 管理Cookie:")
    print("   python manage_cookies.py status          # 查看状态")
    print("   python manage_cookies.py refresh --all   # 刷新所有Cookie")
    print("   python manage_cookies.py test-connection # 测试连接")
    
    print("\n2. 🚀 启动服务:")
    print("   python app/main.py                       # 启动API服务")
    
    print("\n3. 🧪 运行测试:")
    print("   python test_cookiecloud_integration.py  # 运行集成测试")
    
    print("\n4. 🔄 自动刷新:")
    print("   python scripts/auto_refresh_cookies.py  # 启动自动刷新服务")
    
    print("\n5. 📚 查看文档:")
    print("   docs/COOKIECLOUD_GUIDE.md               # 详细使用指南")
    
    print("\n6. 🌐 API接口:")
    print("   http://localhost/docs                   # API文档")
    print("   http://localhost/cookiecloud/status     # CookieCloud状态")

def main():
    """主函数"""
    print_banner()
    
    print("欢迎使用 CookieCloud 快速配置助手！")
    print("本工具将帮助您快速配置和测试 CookieCloud 功能。\n")
    
    try:
        # 检查依赖
        if not check_dependencies():
            print("\n❌ 依赖检查失败，请先安装必要的依赖包")
            sys.exit(1)
        
        # 设置.env文件
        setup_env_file()
        
        # 设置config.yaml
        if not setup_config_yaml():
            print("\n❌ 配置文件设置失败")
            sys.exit(1)
        
        # 测试连接
        connection_ok = test_connection()
        
        # 询问是否运行集成测试
        if connection_ok:
            run_test = input("\n🧪 是否运行集成测试? (y/n) [n]: ").strip().lower()
            if run_test == 'y':
                run_integration_test()
        
        # 显示后续步骤
        show_next_steps()
        
        print("\n✅ 配置完成！CookieCloud 功能已准备就绪。")
        
    except KeyboardInterrupt:
        print("\n⚠️  配置被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 配置过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
