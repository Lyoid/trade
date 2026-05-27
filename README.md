# trade

基于长桥 OpenAPI 的量化交易与信号项目。当前默认策略为 **CallMacd**（自选股 MACD 扫描 + 飞书通知）。

更完整的架构说明见 [DESIGN.md](DESIGN.md)。

## 安装

使用本机 `python3` / `pip` 安装依赖（不创建虚拟环境）：

```bash
cd /Users/lyoid/code/trade   # 换成你的项目路径
./scripts/setup_venv.sh      # python3 -m pip install -r requirement.txt
./scripts/verify_env.sh      # 按 requirement.txt 检查依赖是否已安装
```

日常命令：

```bash
python3 main.py --once
./scripts/run_callmacd_once.sh
```

在项目根目录配置 `config.yaml`（长桥 `app_key` / `app_secret` / `access_token`，飞书 `app_id` / `app_secret` / `open_id`）。

`config.yaml` 中 `log_path` 请改为本机路径，例如：

```yaml
log_path: /Users/你的用户名/code/trade/log
```

## CallMacd 定时运行（系统 cron）

CallMacd 通过 **系统 cron** 每天两个时点各执行一次扫描，不使用 `main.py` 内置常驻调度（`config.yaml` 中 `scheduler.enabled: false`）。

| 时间（北京时间） | 说明 |
|------------------|------|
| **09:35** | 港股 / A 股开盘后扫描 |
| **21:35** | 美股盘中扫描（美东约 9:35） |

### 安装 cron

```bash
cd /path/to/trade
./scripts/install_callmacd_cron.sh
```

安装后 `crontab -l` 应包含：

```cron
# trade CallMacd
35 9 * * 1-5 /path/to/trade/scripts/run_callmacd_once.sh
35 21 * * 1-5 /path/to/trade/scripts/run_callmacd_once.sh
```

仅在工作日（周一～周五）触发。`config.yaml` 里 `scheduler.run_times` 与上述时间保持一致，仅作文档参考。

### 手动执行与查看日志

```bash
./scripts/run_callmacd_once.sh
tail -f log/cron.log
```

等价于：`python main.py --once`（单次扫描后退出）。

### 其他运行方式

```bash
# 常驻 + 每 10 秒轮询（不推荐用于 CallMacd，仅 NetTrader 等下单策略）
python main.py
```

---

## 注意事项

### 1. 配置文件与密钥

- `config.yaml` 含长桥、飞书等敏感信息，**不要提交到公开仓库**；建议使用 `.gitignore` 忽略本地配置，或单独维护 `config.local.yaml`。
- 长桥 `access_token` 有过期时间，过期后需重新获取并更新配置，否则 cron 任务会执行失败（错误见 `log/cron.log`）。

### 2. macOS 上 cron 可能不执行

macOS 对 `cron` 限制较严，若到点没有日志、任务未运行，请检查：

- **系统设置 → 隐私与安全性 → 完全磁盘访问**：为 `cron` 或执行脚本的终端应用授权（视系统版本而定）。
- 本机是否使用 **cron**；部分环境更推荐 `launchd`，可自行编写 plist 调用 `scripts/run_callmacd_once.sh`。
- 用 `crontab -l` 确认任务已安装；修改脚本路径后需重新执行 `./scripts/install_callmacd_cron.sh`。

### 3. 时区与夏令时

- **cron 使用系统本地时间**，与 `config.yaml` 中 `scheduler.timezone` 无自动关联；请保证 Mac 系统时区为 **Asia/Shanghai（北京时间）**，或自行把 crontab 里的 `9` / `21` 改成你需要的本地小时。
- **21:35** 对应美股盘中约美东 9:35；美国 **夏令时** 切换后，北京时间可能需要改为 **20:35** 或 **22:35**，改完后重新安装 cron：

  ```bash
  # 编辑 scripts/install_callmacd_cron.sh 中的 JOB_US 小时，或手动 crontab -e
  ./scripts/install_callmacd_cron.sh
  ```

### 4. 非交易日与节假日

- CallMacd 在 `is_tradings()` 为假时（周末、港美节假日等）会 **跳过本次扫描**，不会发飞书，也不会长时间阻塞。
- 若 cron 在节假日仍触发，属于正常：进程会快速退出，仅写一条日志。

### 5. 日志路径

- 默认 `config.yaml` 中 `log_path` 可能为服务器路径（如 `/root/code/trade/log`）。在本地 Mac 运行时请改为项目内路径，例如：

  ```yaml
  log_path: /Users/你的用户名/code/trade/log
  ```

- cron 专用追加日志：`log/cron.log`（由 `scripts/run_callmacd_once.sh` 写入）。

### 6. Python 环境

- 依赖安装：`./scripts/setup_venv.sh`（本机 `python3 -m pip install -r requirement.txt`，不建 venv）。
- 环境检查：`./scripts/verify_env.sh`（仅核对 `requirement.txt` 中的包是否已安装）。
- `run_callmacd_once.sh` 与 cron 使用 PATH 中的 `python3`。
- 自选股较多时，单次扫描可能需 **十余分钟**，可看 `log/cron.log` 与 `log/CallMacd.log` 确认进度。

### 7. CallMacd 与下单

- CallMacd **只发飞书信号，不下单**；`main.py --once` 不会初始化 `OrderBook`。
- 网格 / MACD 实盘下单策略请用 `python main.py` 常驻模式，并确认 `strategy.name` 与 `stock_id` 配置正确。

### 8. 修改定时时间

1. 修改 `config.yaml` 中 `scheduler.run_times`（文档用途）。
2. 修改 `scripts/install_callmacd_cron.sh` 里的 `JOB_HK` / `JOB_US`  cron 表达式，或 `scripts/callmacd.crontab.snippet`。
3. 执行 `./scripts/install_callmacd_cron.sh` 覆盖安装（脚本会去掉旧的 CallMacd 条目后重写）。

### 9. 内置调度（可选）

若不想用系统 cron，可将 `config.yaml` 中 `scheduler.enabled` 设为 `true`、`mode: daily`，然后长期运行：

```bash
python main.py
```

进程会按 `run_times` 等待到点再扫描。与系统 cron **二选一**，避免重复执行。

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `main.py` | 入口；`--once` 单次扫描 |
| `config.yaml` | 策略与 API 配置 |
| `scripts/run_callmacd_once.sh` | cron 调用的包装脚本 |
| `scripts/install_callmacd_cron.sh` | 安装/更新 crontab |
| `scripts/callmacd.crontab.snippet` | crontab 示例片段 |
| `DESIGN.md` | 设计文档 |
