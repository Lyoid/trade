# Trade 项目设计文档

## 1. 项目概述

Trade 是一个面向 **港股 / A 股 / 美股** 的量化交易与研究工作台。项目通过 [长桥 OpenAPI](https://open.longportapp.com/)（`longport` Python SDK）连接券商行情与交易接口，支持：

- **实盘/准实盘循环**：`main.py` 驱动策略轮询，生成订单并由订单簿模块提交；
- **信号通知模式**：`CallMacd` 策略仅通过飞书推送买卖信号，不返回下单指令；
- **历史回测**：基于 `backtrader` + 本地/在线 K 线数据验证策略；
- **研究与实验**：协整检验、配对交易、跨交易所加密货币套利脚本等独立模块。

当前默认运行配置为 **CallMacd**（自选股 + MACD 金叉/死叉 + 昨日涨跌幅过滤 + 飞书告警）。

---

## 2. 系统架构

### 2.1 总体分层

```
┌─────────────────────────────────────────────────────────────────┐
│                        config.yaml + config.py                   │
│                    （Borg 单例，全局配置）                          │
└─────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  dataloader/  │       │ online_trader/  │       │ strategy/       │
│  数据接入层    │◄──────│ 实盘交易子系统   │       │ factor/         │
│               │       │ strategy/       │       │ 回测与研究       │
│ LongPortOnline│       │ orderbook/      │       │ statistics/     │
│ LongPortTest  │       │ riskmanager/    │       │ bitcoin/        │
│ Yahoo/Tushare │       └────────┬────────┘       └─────────────────┘
└───────────────┘                │
        │                        ▼
        │               ┌─────────────────┐
        └──────────────►│ tools/          │
                        │ TimeCheck       │
                        │ FeiShu          │
                        └─────────────────┘
```

### 2.2 实盘主循环（`main.py`）

```
┌──────────┐    Run()     ┌──────────────────┐    submit()    ┌────────────┐
│ main.py  │─────────────►│ SelectStrategy   │───────────────►│ OrderBook  │
│ (10s)    │   order_list │ NetTrader/MACD/  │   限价日单      │ → LongPort │
└──────────┘              │ CallMacd         │                └────────────┘
       │                  └────────┬─────────┘
       │                           │ CallMacd: return None
       │                           ▼
       │                  ┌──────────────────┐
       └─────────────────►│ LongPortOnline   │ 行情/持仓/交易时段
                          │ (Borg 单例)       │
                          └──────────────────┘
```

**执行流程：**

1. 初始化 `LongPortOnline`、`OrderBook`、`SelectStrategy(config["strategy"]["name"])()`；
2. 无限循环，每 **10 秒** 调用一次 `strategy.Run()`；
3. 若返回非空 `order_list`，逐条调用 `OrderBook.submit(stock_id, price, amount, order_side)`；
4. `CallMacd` 的 `Run()` 恒为 `None`，主循环不触发下单，仅依赖策略内部的飞书通知。

### 2.3 回测入口（`test.py`）

```
LongPortTest.fetch_data() → backtrader.Cerebro
    → strategy.TraderSelect.SelectStrategy → 运行分析器（Sharpe、DrawDown）→ 绘图
```

与实盘共用 `config.yaml` 中的 `stock_id`、`strategy` 等字段，但策略类位于 `strategy/` 包（继承 `StrategySelfBase`），与 `online_trader/strategy/` 中的在线策略 **同名不同实现**。

---

## 3. 目录与模块职责

| 路径 | 职责 |
|------|------|
| `main.py` | 实盘主入口：策略轮询 + 下单 |
| `test.py` | Backtrader 回测入口 |
| `config.py` / `config.yaml` | YAML 配置加载（Borg 单例） |
| `log.py` | 按 `log_path` / `log_name` 写滚动日志 |
| **dataloader/** | |
| `LongPortOnline.py` | 在线行情、持仓、K 线、交易时段判断；模块级单例 `dataset` |
| `LongPortTest.py` | 拉取历史 K 线并转为 Backtrader `PandasData` |
| `Yahoo.py` | Yahoo Finance 历史数据 |
| `Tushare.py` | Tushare 数据源（可选） |
| **online_trader/** | |
| `strategy/TraderSelect.py` | 在线策略工厂：`NetTrader` / `MACD` / `CallMacd` |
| `strategy/TraderStrategy.py` | 在线策略 Protocol（约定 `Run()`） |
| `strategy/NetTrader.py` | 网格交易：按价差阈值买卖 |
| `strategy/MACD.py` | 单标的 MACD 实盘下单 |
| `strategy/CallMacd.py` | 自选股批量 MACD + 涨跌幅过滤 + 飞书 |
| `orderbook/OrderBook.py` | 订单提交、撤单、同标的挂单去重/改单 |
| `riskmanager/ABC.py` | 风控骨架（`RiskManager`，未接入主流程） |
| **strategy/**（回测） | `MACD`、`PairTrade`、`MeanReversion`、`RSI_SMA` 等 |
| **factor/** | |
| `MACDFactor.py` | MACD/信号线/柱状图、金叉死叉、顶底背离检测 |
| `FactorBase.py` | 因子基类 Protocol |
| **tools/** | |
| `TimeCheck.py` | 美东/北京时间、节假日、跨日判断 |
| `FeiShu.py` | 飞书 IM 文本消息（`lark_oapi`） |
| **statistics/** | 协整、ADF 等统计实验 |
| **bitcoin/** | Binance/OKX 跨所套利示例（独立，未接主流程） |
| **longport_test/** | LongPort API 联调脚本集合 |

---

## 4. 核心组件设计

### 4.1 配置管理（`config.py`）

- 使用 **Borg 模式**（共享 `__dict__`）保证全局唯一 `Config` 实例；
- 启动时读取 `./config.yaml`，暴露 `config` 字典供各模块直接索引；
- 典型配置项：

| 键 | 说明 |
|----|------|
| `log_path` / `log_name` | 日志目录与文件名 |
| `longport.app_key` / `app_secret` / `access_token` | 长桥鉴权（**勿提交仓库**） |
| `longport.candlestick_amount` | 拉取 K 线根数 |
| `feishu.*` | 飞书应用与接收人 `open_id` |
| `stock_id` | 单标的或列表（NetTrader / MACD 使用） |
| `strategy.name` | 策略名，对应 `TraderSelect` 工厂 |
| `strategy.*` | 策略参数（网格金额、MACD 周期、`delta` 涨跌幅阈值等） |

### 4.2 数据层（`LongPortOnline`）

**职责：**

- 维护 `TradeContext`、`QuoteContext`；
- `get_current_price`：按市场区分盘中 / 盘前 / 盘后报价；
- `get_history_candlesticks`：前复权日 K（默认 `Period.Day`）；
- `is_trading` / `is_on_market` / `is_tradings`：结合 `TimeCheck` 的工作日与时段；
- `watchlists_by_symbol`：从长桥自选股拉取 HK/US/SH/SZ 标的；
- `check_stock_positions`：是否持仓（NetTrader 空仓建仓逻辑）；
- `get_last_trade_price`：当日或历史成交的最后价格。

**设计特点：**

- Borg 单例 + 模块级 `dataset`，与 `OrderBook` 共用同一连接上下文；
- 美股时段划分含缓冲（如盘前 `04:05`–`09:30`），规避 API 在盘口切换返回 `None` 的问题。

### 4.3 订单簿（`OrderBook`）

| 方法 | 行为 |
|------|------|
| `submit_order` | `OrderType.LO` 限价单，`TimeInForceType.Day`，写入本地 `order_book` |
| `check_stockid` | 同 `symbol` 是否存在 `New` / `WaitToNew` 挂单 |
| `submit` | 有挂单则先 `cancel_order` 再下单（改单语义） |
| `check_order_status` | 后台线程每 2s 轮询，终态订单移出簿 |

初始化时同步当日未完结订单到内存字典。

### 4.4 因子层（`MACDFactor`）

- 参数来自 `config["strategy"]`：`period_1`（快 EMA）、`period_2`（慢 EMA）、`period_3`（信号线）；
- `algo(closes)`：pandas 计算 MACD、金叉/死叉索引、30 日窗口顶/底背离；
- `check()`：在最后一根 K 上判断金叉 → `1`（买）、死叉 → `2`（卖），否则 `0`；
- 在线 MACD 策略曾用 `delete_last_candlestick()` 避免重复消费当日 bar；CallMacd 使用纯历史 K 线检测。

### 4.5 在线策略

#### NetTrader（网格）

- 配置：`first_amount`（首仓）、`amount`（加减仓）、`delta_price`（价差阈值）、`stock_id`；
- 空仓 → 市价逻辑买入 `first_amount`；
- 有仓 → 相对 `last_trader_price` 涨跌超过 `delta_price` 则卖/买 `amount`；
- 返回 `[{ stock_id, price, amount, order_side }]` 供 `main.py` 下单。

#### MACD（单标的实盘）

- 交易时段内轮询；跨日 `TimeCheck.check_next_day()` 时重新 `init_strategy`；
- `macd_factor.check(candle)` 用当前价构造伪 K 线；
- 返回 `(price, amount, order_side)` 三元组（与 `main.py` 期望的 dict 列表 **接口不一致**，属历史遗留）。

#### CallMacd（当前默认）

- 标的：`watchlists_by_symbol()` 自选股全集；
- 每标的独立 `MACDFactor` + `start_call` / `recall` 控制每日/盘中只告警一次；
- **买入条件**：MACD 金叉（`result_1 == 1`）且 `OpenCloseDelta`（昨日 `(close-open)/open > delta`）；
- **卖出条件**：MACD 死叉；
- 非交易时段：`init_factor` 刷新 K 线，重置 call 标志；
- 非盘中：`recall` 置 true，待再次进入盘中可再推送；
- **仅** `feishu.message()`，不返回订单。

### 4.6 回测策略（`strategy/`）

- 基类 `StrategySelfBase(bt.Strategy)`：统一日志、订单/成交回调、多标的 `inds` 字典；
- `strategy/MACD.py`：Backtrader 仓位 + `MACDFactor.check`；
- 其他：双均线、RSI、均值回归、配对交易等，通过 `test.py` 切换 import；
- `strategy/net_trade.py` 为早期独立 `bt.Strategy`，未走 `StrategySelfBase` 工厂。

### 4.7 工具与通知

- **TimeCheck**：`holidays` 库判断美/港工作日；`get_us_time` / `get_beijing_time`；
- **FeiShu**：`lark_oapi` 向指定 `open_id` 发文本消息。

---

## 5. 数据流与接口约定

### 5.1 在线策略 `Run()` 返回值（约定）

`main.py` 期望：

```python
[
  {
    "stock_id": str,      # 如 "01810.HK"
    "price": Decimal,     # 限价
    "amount": int,        # 数量
    "order_side": OrderSide.Buy | OrderSide.Sell | None,
  },
  ...
]
```

| 策略 | 实际返回 | 与 main 兼容性 |
|------|----------|----------------|
| NetTrader | 上述 dict 列表 | ✅ |
| MACD | `(price, amount, order_side)` 元组 | ❌ 需适配 |
| CallMacd | `None` | ✅（不下单） |

### 5.2 共享单例依赖关系

```
config (Borg)
    ├── LongPortOnline → dataset
    ├── OrderBook → dataset.trade_ctx / quote_ctx
    ├── FeiShu
    └── TimeCheck (无状态静态方法为主)
```

策略模块内多次 `global data` / `LongPortOnline()` 实际指向同一 Borg 状态。

---

## 6. 部署与运行

### 6.1 依赖

见 `requirement.txt`：`longport`、`backtrader`、`pandas`、`yfinance`、`tushare`、`statsmodels`、`arch`、`ccxt`、`lark_oapi`、`holidays`、`pytz` 等。

```bash
pip install -r requirement.txt -i https://mirrors.aliyun.com/pypi/simple
```

### 6.2 运行方式

| 命令 | 用途 |
|------|------|
| `python main.py` | 实盘/信号循环（需有效 `config.yaml` 与长桥 token） |
| `python test.py` | Backtrader 回测 |
| `python longport_test/*.py` | 单项 API 调试（下单、行情、资产等） |

### 6.3 日志

- 路径：`config["log_path"]`；
- 文件：`{log_name}.log`，5MB × 5 轮转；
- 控制台 INFO，文件 DEBUG。

---

## 7. 扩展指南

### 7.1 新增在线策略

1. 在 `online_trader/strategy/` 实现类，提供 `Run()`；
2. 注册到 `online_trader/strategy/TraderSelect.py` 的 `localizers`；
3. 在 `config.yaml` 增加 `strategy` 段参数；
4. 若需下单，保证返回 dict 列表格式与 `main.py` 一致。

### 7.2 新增回测策略

1. 继承 `StrategySelfBase` 或 `bt.Strategy`；
2. 注册到 `strategy/TraderSelect.py`；
3. 在 `test.py` 中 `cerebro.addstrategy` 使用工厂。

### 7.3 新增因子

1. 继承/实现 `FactorBase`；
2. 在策略中实例化并在 `Run()` / `next()` 中调用 `check()` 或自定义接口。

### 7.4 接入风控

`online_trader/riskmanager/ABC.py` 已定义 `RiskManager` 骨架，可在 `main.py` 下单前插入校验（仓位上限、单日亏损、标的黑名单等），当前 **未接线**。

---

## 8. 已知限制与技术债

1. **双套策略命名空间**：`online_trader/strategy/MACD.py` 与 `strategy/MACD.py` 行为不同，易混淆。
2. **MACD 在线返回值** 与 `main.py` 订单 dict 格式不一致，实盘 MACD 路径可能无法正确下单。
3. **全局变量**：在线策略使用 `global data` / `order_book`，可测试性差。
4. **Borg 单例**：多进程/多配置场景不适用；`Config` 打印调试信息较多。
5. **CallMacd** 长休眠：`is_tradings()` 为假时 `sleep(8h)`，阻塞单线程主循环。
6. **敏感信息**：`config.yaml` 含 API 密钥与 token，应使用环境变量或本地未跟踪配置（当前仓库已暴露风险）。
7. **RiskManager**、**bitcoin/**、**statistics/** 与主交易链路解耦，需单独运维认知。
8. `OrderBook.check_order_status` 中状态更新逻辑 `self.order_book[order_id] = detail` 未使用新 `resp`，可能不影响终态删除但存在状态陈旧风险。

---

## 9. 附录：策略与配置对照示例

### NetTrader（网格）

```yaml
stock_id: ["MSTX.US"]
strategy:
  name: NetTrader
  first_amount: 60
  amount: 20
  delta_price: 0.5
```

### MACD（实盘单标的）

```yaml
stock_id: ["01810.HK"]
strategy:
  name: MACD
  period_1: 30
  period_2: 50
  period_3: 9
  amount: 600
```

### CallMacd（信号，当前默认）

```yaml
log_name: CallMacd
strategy:
  name: CallMacd
  period_1: 12
  period_2: 26
  period_3: 9
  delta: 0.03   # 昨日涨幅阈值 (close-open)/open
```

---

## 10. 文档修订

| 日期 | 说明 |
|------|------|
| 2026-05-27 | 初版：基于仓库现状整理架构与模块说明 |
