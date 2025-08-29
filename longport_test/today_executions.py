from longport.openapi import TradeContext, Config
config = Config(
            app_key="fddd1f64ad477d0aea79928c749cc581",
            app_secret="d7873d6e17dbff6c0f1bb6ccf3f5a638f044ee9b6ba7f87e92399c8e8164357e",
            access_token="m_eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsb25nYnJpZGdlIiwic3ViIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNzU3ODM3MDAyLCJpYXQiOjE3NTAwNjEwMDIsImFrIjoiZmRkZDFmNjRhZDQ3N2QwYWVhNzk5MjhjNzQ5Y2M1ODEiLCJhYWlkIjoyMDUxMzYxNywiYWMiOiJsYl9wYXBlcnRyYWRpbmciLCJtaWQiOjEzNzY5MjY3LCJzaWQiOiJMVUZmbWlyREYrN0VHQzVwVmQvcGZRPT0iLCJibCI6MywidWwiOjAsImlrIjoibGJfcGFwZXJ0cmFkaW5nXzIwNTEzNjE3In0.O93MXh1QulHf-Y-OHxw6N5DhCNfzxXPPVifRFKNLnqOYnzw3C0bb4RAI80BbaxHSnlCdvBw4skQpaiphBa06Avhc0jfNopB8ZkZRuJPgowSuKHL28mxMwekYSlsU_Z204-pczXDoa1CENF1i4NSSZOuYf1UAxcgLRRDY8Py96qiYm0ng7V9N4puIEATrvEVgE05yGPmLhf9sCMTSK5Zf99svbGykngUFhLQrxZuHEe_b_HsKd1yletyDZ_xn0d_9vTHyXPXik2H_rsG-5Mni6gLYuyv5y9BtbwDonfR1OUMXGoQBqwWmq1Z0oX2lzTXurBljlkhiBW_GMalpS03ssOWZyIO6xtFlOdt0FGWtMybGVXWVexUxWcbGOskWPXrOyoof8XOnG9QUknFNj0hYLYdZAMpECkQ-un7jVoj-Bx5itJjb6Y3BP94BAuNK41mMHcxOhfwZLlGafImxX8PVkKzt6wpZjCzwN2MOB7YclWcn4uE3H1D4ierQl5Wh3mayCS2gLH6Pcpxz5OnuYEWctZ3N8B92yI7zTu5xysyEKIySYL4ZTMd_IrlYsrwHN_xYp2BOcRpt2XQB2sw7qFQCsaHQlNy1Jo6IfbgNAqeZLhhekcLOo4Wttei8cVG5hnlbQz-A7eQ64gjtbl_3aQkxgtkYHsYJ0v3b1Tez4HoG_LM",
            enable_overnight=True)
    
ctx = TradeContext(config)
stock_id = ["MSTZ.US","01810.HK"]
resp = ctx.today_executions(symbol="MSTZ.US")
print(resp)

# # 再找历史成交记录
# resp = self.trade_ctx.history_executions(
#     # symbol = "700.HK",
#     symbol=stock_id,
#     # start_at = datetime(2022, 5, 9),
#     start_at=start_date,
#     end_at=datetime.today(),
# )
# if resp:
#     last_trader_price = resp[len(resp) - 1].price
#     return last_trader_price

# return Decimal(0.0)