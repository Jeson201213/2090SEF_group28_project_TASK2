# data_service.py
import sqlite3
import pandas as pd
import datetime
from typing import List, Dict, Optional

# 初始化数据库（首次运行自动创建表）
def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    
    # 1. 账户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,  # 账户名（如：微信、银行卡）
        balance FLOAT DEFAULT 0,  # 账户余额
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. 收支记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,  # 类型：income/expense
        amount FLOAT NOT NULL,  # 金额
        category TEXT NOT NULL,  # 分类（餐饮/工资等）
        account_id INTEGER,  # 关联账户ID
        remark TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )
    ''')
    
    # 3. 预算表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,  # 预算分类
        amount FLOAT NOT NULL,  # 预算金额
        month TEXT NOT NULL,  # 月份（如：2026-03）
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# ========== 基础CRUD（供后端1调用） ==========
def add_account(name: str, balance: float = 0) -> bool:
    """新增账户"""
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO accounts (name, balance) VALUES (?, ?)', (name, balance))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"新增账户失败：{e}")
        return False

def add_record(record_type: str, amount: float, category: str, account_id: int, remark: str = "") -> bool:
    """新增收支记录"""
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO records (type, amount, category, account_id, remark)
        VALUES (?, ?, ?, ?, ?)
        ''', (record_type, amount, category, account_id, remark))
        # 更新账户余额
        cursor.execute('''
        UPDATE accounts SET balance = CASE 
            WHEN ? = 'income' THEN balance + ? 
            ELSE balance - ? 
        END WHERE id = ?
        ''', (record_type, amount, amount, account_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"新增记录失败：{e}")
        return False

# ========== 报表计算（核心拓展） ==========
def get_monthly_trend(year: int) -> List[Dict]:
    """获取年度月度收支趋势（供前端可视化）"""
    conn = sqlite3.connect('finance.db')
    # 查询全年12个月的收支数据
    trend_data = []
    for month in range(1, 13):
        month_str = f"{year}-{month:02d}"
        # 计算收入
        income_sql = f'''
        SELECT COALESCE(SUM(amount), 0) FROM records 
        WHERE type = 'income' AND strftime('%Y-%m', create_time) = '{month_str}'
        '''
        income = pd.read_sql(income_sql, conn).iloc[0, 0]
        
        # 计算支出
        expense_sql = f'''
        SELECT COALESCE(SUM(amount), 0) FROM records 
        WHERE type = 'expense' AND strftime('%Y-%m', create_time) = '{month_str}'
        '''
        expense = pd.read_sql(expense_sql, conn).iloc[0, 0]
        
        trend_data.append({
            "month": month,
            "income": round(income, 2),
            "expense": round(expense, 2)
        })
    conn.close()
    return trend_data

def get_category_ratio(month: str) -> Dict:
    """获取指定月份支出分类占比（供前端饼图）"""
    conn = sqlite3.connect('finance.db')
    sql = f'''
    SELECT category, SUM(amount) as total 
    FROM records 
    WHERE type = 'expense' AND strftime('%Y-%m', create_time) = '{month}'
    GROUP BY category
    '''
    df = pd.read_sql(sql, conn)
    conn.close()
    # 转换为字典（分类: 金额）
    ratio_data = df.set_index('category')['total'].to_dict()
    # 计算占比
    total = sum(ratio_data.values())
    ratio_data = {k: round(v/total*100, 2) for k, v in ratio_data.items()}
    return ratio_data

# ========== 数据备份（核心拓展） ==========
def backup_db() -> str:
    """备份数据库到本地文件"""
    backup_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"finance_backup_{backup_time}.db"
    # 复制数据库文件
    with open('finance.db', 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    return backup_path

# 初始化数据库（首次运行执行）
if __name__ == "__main__":
    init_db()
    # 测试数据
    add_account("微信", 1000)
    add_record("income", 5000, "工资", 1, "3月工资")
    add_record("expense", 200, "餐饮", 1, "午餐")
    print("月度趋势：", get_monthly_trend(2026))
    print("支出占比：", get_category_ratio("2026-03"))
    print("备份文件：", backup_db())
