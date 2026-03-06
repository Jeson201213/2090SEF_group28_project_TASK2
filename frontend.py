# frontend.py
import streamlit as st
import requests
import plotly.express as px
import pandas as pd

# 后端1接口地址
API_BASE = "http://127.0.0.1:8000"

# 页面配置
st.set_page_config(page_title="个人财务管理系统", layout="wide")
st.title("📊 个人财务管理系统")

# 侧边栏导航
menu = st.sidebar.selectbox("功能菜单", ["账户管理", "收支记账", "报表分析", "数据备份"])

# ========== 1. 账户管理 ==========
if menu == "账户管理":
    st.subheader("账户管理")
    # 新增账户
    with st.form("add_account_form"):
        account_name = st.text_input("账户名称")
        init_balance = st.number_input("初始余额", min_value=0.0, step=0.01)
        submit = st.form_submit_button("新增账户")
        if submit:
            if not account_name:
                st.error("账户名称不能为空")
            else:
                res = requests.post(f"{API_BASE}/accounts/add", params={"name": account_name, "balance": init_balance})
                if res.json()["code"] == 200:
                    st.success("账户新增成功！")
                else:
                    st.error("账户新增失败！")
    
    # 展示账户列表
    st.subheader("账户列表")
    res = requests.get(f"{API_BASE}/accounts/list")
    if res.json()["code"] == 200:
        accounts = pd.DataFrame(res.json()["data"])
        st.dataframe(accounts, use_container_width=True)

# ========== 2. 收支记账 ==========
elif menu == "收支记账":
    st.subheader("收支记账")
    with st.form("add_record_form"):
        record_type = st.selectbox("类型", ["income", "expense"])
        amount = st.number_input("金额", min_value=0.01, step=0.01)
        category = st.text_input("分类（如：餐饮/工资）")
        # 获取账户列表供选择
        res = requests.get(f"{API_BASE}/accounts/list")
        account_options = {}
        if res.json()["code"] == 200:
            accounts = res.json()["data"]
            account_options = {acc["id"]: acc["name"] for acc in accounts}
        account_id = st.selectbox("关联账户", list(account_options.keys()), format_func=lambda x: account_options[x])
        remark = st.text_input("备注（可选）")
        submit = st.form_submit_button("提交记账")
        
        if submit:
            if not category:
                st.error("分类不能为空")
            else:
                params = {
                    "record_type": record_type,
                    "amount": amount,
                    "category": category,
                    "account_id": account_id,
                    "remark": remark
                }
                res = requests.post(f"{API_BASE}/records/add", params=params)
                if res.json()["code"] == 200:
                    st.success("记账成功！")
                else:
                    st.error(f"记账失败：{res.json()['detail']}")

# ========== 3. 报表分析（可视化拓展） ==========
elif menu == "报表分析":
    st.subheader("报表分析")
    # 月度收支趋势图
    st.subheader("月度收支趋势")
    year = st.number_input("选择年份", min_value=2020, max_value=2030, value=2026)
    res = requests.get(f"{API_BASE}/report/trend", params={"year": year})
    if res.json()["code"] == 200:
        trend_data = pd.DataFrame(res.json()["data"])
        fig = px.line(trend_data, x="month", y=["income", "expense"], 
                      title=f"{year}年月度收支趋势", 
                      labels={"value": "金额（元）", "month": "月份"})
        st.plotly_chart(fig, use_container_width=True)
    
    # 支出分类占比饼图
    st.subheader("支出分类占比")
    month = st.text_input("选择月份（格式：2026-03）", value="2026-03")
    res = requests.get(f"{API_BASE}/report/category_ratio", params={"month": month})
    if res.json()["code"] == 200:
        ratio_data = res.json()["data"]
        if ratio_data:
            fig = px.pie(values=list(ratio_data.values()), names=list(ratio_data.keys()),
                          title=f"{month}支出分类占比")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无该月份支出数据")

# ========== 4. 数据备份 ==========
elif menu == "数据备份":
    st.subheader("数据备份")
    if st.button("立即备份数据库"):
        res = requests.get(f"{API_BASE}/data/backup")
        if res.json()["code"] == 200:
            st.success(f"备份成功！备份文件：{res.json()['data']['backup_path']}")
        else:
            st.error("备份失败！")
