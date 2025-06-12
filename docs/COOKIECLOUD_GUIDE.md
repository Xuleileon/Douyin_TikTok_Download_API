# CookieCloud 集成指南

本项目已集成 CookieCloud 动态 Cookie 管理功能，支持自动从 CookieCloud 服务获取最新的 Cookie 并更新到爬虫配置中。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包括：
- `PyCookieCloud>=1.0.4` - CookieCloud 客户端库
- `python-dotenv>=0.19.0` - 环境变量管理

### 2. 配置 CookieCloud

#### 2.1 创建 .env 文件

复制 `.env.example` 文件并重命名为 `.env`：

```bash
cp .env.example .env
```

#### 2.2 配置 CookieCloud 信息

编辑 `.env` 文件，填入你的 CookieCloud 配置：

```env
# CookieCloud 配置
COOKIECLOUD_SERVER_URL=https://your-cookiecloud-server.com
COOKIECLOUD_UUID=your-uuid-here
COOKIECLOUD_PASSWORD=your-password-here

# 可选配置
DEFAULT_OUTPUT_FORMAT=json
COOKIECLOUD_CACHE_TTL=3600
COOKIECLOUD_DEBUG=false
```

#### 2.3 启用 CookieCloud 功能

在 `config.yaml` 中确认 CookieCloud 功能已启用：

```yaml
CookieCloud:
  Enable: true  # 启用 CookieCloud
  Cache_TTL: 3600  # 缓存时间（秒）
  Fallback_Enabled: true  # 启用回退到硬编码 Cookie
```

### 3. 测试连接

使用管理工具测试 CookieCloud 连接：

```bash
python manage_cookies.py test-connection
```

## 🛠️ 使用方法

### 命令行工具

#### 查看状态
```bash
python manage_cookies.py status
```

#### 刷新所有平台的 Cookie
```bash
python manage_cookies.py refresh --all
```

#### 刷新指定平台的 Cookie
```bash
python manage_cookies.py refresh --platform douyin
python manage_cookies.py refresh --platform douyin tiktok bilibili
```

### API 接口

项目提供了完整的 CookieCloud 管理 API：

#### 获取状态
```http
GET /api/cookiecloud/status
```

#### 测试连接
```http
POST /api/cookiecloud/test-connection
```

#### 刷新 Cookie
```http
POST /api/cookiecloud/refresh
Content-Type: application/json

{
  "platforms": ["douyin", "tiktok"],
  "force_refresh": false
}
```

#### 获取支持的平台
```http
GET /api/cookiecloud/platforms
```

#### 清除缓存
```http
DELETE /api/cookiecloud/cache
```

### 自动刷新服务

#### 持续运行（默认每小时刷新）
```bash
python scripts/auto_refresh_cookies.py
```

#### 自定义刷新间隔（每30分钟）
```bash
python scripts/auto_refresh_cookies.py --interval 1800
```

#### 执行一次性刷新
```bash
python scripts/auto_refresh_cookies.py --once
```

## 🔧 工作原理

### 1. Cookie 获取流程

1. **优先级**：CookieCloud > 配置文件硬编码 Cookie
2. **缓存机制**：获取的 Cookie 会缓存指定时间，避免频繁请求
3. **自动更新**：新获取的 Cookie 会自动更新到对应的配置文件中
4. **错误处理**：CookieCloud 失败时自动回退到硬编码 Cookie

### 2. 支持的平台

- **抖音** (douyin) - `douyin.com`
- **TikTok** (tiktok) - `tiktok.com`
- **哔哩哔哩** (bilibili) - `bilibili.com`

### 3. 配置文件映射

- 抖音：`crawlers/douyin/web/config.yaml`
- TikTok：`crawlers/tiktok/web/config.yaml`
- 哔哩哔哩：`crawlers/bilibili/web/config.yaml`

## 📊 监控和日志

### 查看日志

所有 CookieCloud 相关的操作都会记录到日志中：

```bash
# 查看实时日志
tail -f logs/app.log

# 搜索 CookieCloud 相关日志
grep "CookieCloud\|cookie" logs/app.log
```

### 状态监控

通过 API 或命令行工具可以实时监控：

- CookieCloud 连接状态
- 各平台 Cookie 缓存状态
- 最后更新时间
- 错误信息

## 🔒 安全注意事项

1. **保护 .env 文件**：确保 `.env` 文件不被提交到版本控制系统
2. **服务器安全**：确保 CookieCloud 服务器使用 HTTPS
3. **访问控制**：限制对 CookieCloud API 的访问权限
4. **定期更新**：定期更新 CookieCloud 服务器和客户端

## 🐛 故障排查

### 常见问题

#### 1. CookieCloud 连接失败
```
❌ 连接失败: 未获取到数据
```

**解决方案**：
- 检查 `.env` 文件中的配置是否正确
- 确认 CookieCloud 服务器是否正常运行
- 检查网络连接

#### 2. Cookie 获取失败
```
❌ 未找到 douyin(douyin.com) 的cookie
```

**解决方案**：
- 确认浏览器中已登录目标网站
- 检查 CookieCloud 是否已同步最新数据
- 验证域名映射配置是否正确

#### 3. 配置文件更新失败
```
❌ douyin cookie刷新失败（配置文件更新失败）
```

**解决方案**：
- 检查配置文件是否存在
- 确认程序有写入权限
- 验证配置文件格式是否正确

### 调试模式

启用调试模式获取更详细的日志：

```env
COOKIECLOUD_DEBUG=true
```

## 🔄 升级和迁移

### 从硬编码 Cookie 迁移

1. 备份现有配置文件
2. 配置 CookieCloud
3. 测试连接
4. 执行一次刷新
5. 验证功能正常

### 版本升级

更新依赖包：

```bash
pip install --upgrade PyCookieCloud python-dotenv
```

## 📚 相关链接

- [CookieCloud 官方项目](https://github.com/easychen/CookieCloud)
- [PyCookieCloud 库](https://github.com/lupohan44/PyCookieCloud)
- [项目 API 文档](/docs)

## 💡 最佳实践

1. **定期刷新**：建议每小时自动刷新一次 Cookie
2. **监控告警**：设置 Cookie 获取失败的告警机制
3. **备份策略**：定期备份有效的 Cookie 配置
4. **测试验证**：部署后及时测试各平台功能是否正常
