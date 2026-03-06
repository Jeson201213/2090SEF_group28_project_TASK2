# business_service.py
from fastapi import FastAPI, HTTPException
import uvicorn
from typing import List, Dict
import data_service  # 导入后端2的函数

# 初始化FastAPI应用
app = FastAPI(title="个人财务管理系统-业务接口")

# ========== 账户管理接口 ==========
@app.post("/accounts/add", response_model=Dict)
def add_account(name: str, balance: float = 0):
    """新增账户接口"""
    success = data_service.add_account(name, balance)
    if success:
        return {"code": 200, "msg": "账户新增成功", "data": None}
    raise HTTPException(status_code=500, detail="账户新增失败")

@app.get("/accounts/list", response_model=Dict)
def list_accounts():
    """获取账户列表"""
    conn = data_service.sqlite3.connect('finance.db')
    df = data_service.pd.read_sql("SELECT * FROM accounts", conn)
    conn.close()
    return {
        "code": 200,
        "msg": "查询成功",
        "data": df.to_dict('records')
    }

# ========== 收支记账接口（带业务规则校验） ==========
@app.post("/records/add", response_model=Dict)
def add_record(record_type: str, amount: float, category: str, account_id: int, remark: str = ""):
    """新增收支记录（含业务校验）"""
    # 规则1：金额必须大于0
    if amount <= 0:
        raise HTTPException(status_code=400, detail="金额必须大于0")
    # 规则2：校验账户是否存在
    conn = data_service.sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="账户不存在")
    conn.close()
    # 规则3：支出不能超过账户余额（可选）
    if record_type == "expense":
        conn = data_service.sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
        balance = cursor.fetchone()[0]
        conn.close()
        if amount > balance:
            raise HTTPException(status_code=400, detail="支出金额超过账户余额")
    
    # 调用后端2新增记录
    success = data_service.add_record(record_type, amount, category, account_id, remark)
    if success:
        return {"code": 200, "msg": "记账成功", "data": None}
    raise HTTPException(status_code=500, detail="记账失败")

# ========== 报表接口（转发后端2的计算结果） ==========
@app.get("/report/trend", response_model=Dict)
def get_trend(year: int = 2026):
    """获取年度月度收支趋势"""
    trend_data = data_service.get_monthly_trend(year)
    return {
        "code": 200,
        "msg": "查询成功",
        "data": trend_data
    }

@app.get("/report/category_ratio", response_model=Dict)
def get_category_ratio(month: str = "2026-03"):
    """获取月度支出分类占比"""
    ratio_data = data_service.get_category_ratio(month)
    return {
        "code": 200,
        "msg": "查询成功",
        "data": ratio_data
    }

# ========== 数据备份接口 ==========
@app.get("/data/backup", response_model=Dict)
def backup_data():
    """备份数据库"""
    backup_path = data_service.backup_db()
    return {
        "code": 200,
        "msg": "备份成功",
        "data": {"backup_path": backup_path}
    }

# 启动服务（默认端口8000）
if __name__ == "__main__":
    uvicorn.run("business_service:app", host="0.0.0.0", port=8000, reload=True)
