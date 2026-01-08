import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 设置页面
st.set_page_config(
    page_title="食堂菜品推荐系统",
    page_icon="🍽️",
    layout="wide"
)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class CanteenRecommendationSystem:
    def __init__(self):
        self.dishes_data = None
        self.user_ratings = pd.DataFrame(columns=['用户ID', '菜品名称', '评分'])
        self.user_reviews = pd.DataFrame(columns=['用户ID', '菜品名称', '评价内容', '情感得分', '评价时间'])
        self.current_user = "guest"
        # 不要在这里调用 load_dishes_data()   
  
  def load_dishes_data(self):
        """加载菜品数据"""
        try:
            import os
            
            # 显示当前目录和文件（调试用）
            st.write("当前目录：", os.getcwd())
            st.write("文件列表：", os.listdir("."))
            
            # 自动查找数据文件（支持多个名字）
            filenames_to_try = ["data.csv", "食堂菜品数据.csv", "dishes.csv"]
            encodings_to_try = ['utf-8', 'gbk', 'gb18030']
            
            file_found = False
            
            for filename in filenames_to_try:
                if os.path.exists(filename):
                    st.write(f"找到文件：{filename}")
                    for encoding in encodings_to_try:
                        try:
                            self.dishes_data = pd.read_csv(filename, encoding=encoding)
                            st.write(f"成功读取：{filename}，编码：{encoding}")
                            file_found = True
                            break
                        except Exception as e:
                            st.write(f"{encoding}编码失败：{str(e)}")
                            continue
                    if file_found:
                        break
            
            if not file_found:
                st.error("❌ 找不到数据文件！")
                # 显示所有文件详情
                for f in os.listdir("."):
                    st.write(f"- {f} (大小：{os.path.getsize(f)} bytes)")
                return False
            
            # 修复列名
            if len(self.dishes_data.columns) >= 6:
                self.dishes_data.columns = ['菜品名称', '口味得分', '营养得分', '热度得分', '性价比得分', '关键词']
            
            # 确保数值列是数字类型
            numeric_cols = ['口味得分', '营养得分', '热度得分', '性价比得分']
            for col in numeric_cols:
                if col in self.dishes_data.columns:
                    self.dishes_data[col] = pd.to_numeric(self.dishes_data[col], errors='coerce')
                else:
                    self.dishes_data[col] = 3.0
            
            # 计算综合得分
            self.dishes_data['综合得分'] = (
                self.dishes_data['口味得分'] * 0.4 +
                self.dishes_data['营养得分'] * 0.2 +
                self.dishes_data['热度得分'] * 0.2 +
                self.dishes_data['性价比得分'] * 0.2
            ).round(2)
            
            # 加载用户数据
            self.load_user_data()
            
            return True
            
        except Exception as e:
            st.error(f"加载数据失败：{str(e)}")
            return False    
    def load_user_data(self):
        """加载用户历史数据"""
        try:
            if os.path.exists("用户评分记录.csv"):
                self.user_ratings = pd.read_csv("用户评分记录.csv", encoding='utf-8')
            
            if os.path.exists("用户评价记录.csv"):
                self.user_reviews = pd.read_csv("用户评价记录.csv", encoding='utf-8')
                
        except:
            pass

# 创建系统实例
system = CanteenRecommendationSystem()

# 网站标题
st.title("🍽️ 食堂菜品评分与推荐系统")
st.markdown("---")

# 先加载数据
if system.dishes_data is None:
    if not system.load_dishes_data():
        st.error("无法加载菜品数据，请检查数据文件！")
        st.stop()  # 停止执行后面的代码

# 侧边栏 - 用户登录
with st.sidebar:
    st.header("👤 用户登录")
    user_id = st.text_input("输入用户ID", value="游客")
    if st.button("登录"):
        system.current_user = user_id
        st.success(f"欢迎 {user_id}!")
    
    st.markdown("---")
    st.header("📊 快速查看")
    if st.button("显示所有菜品"):
        st.session_state.show_all = True
    
    if st.button("显示TOP10菜品"):
        st.session_state.show_top10 = True
    
    st.markdown("---")
    st.header("📈 数据可视化")
    viz_option = st.selectbox(
        "选择图表类型",
        ["请选择", "TOP菜品排名", "得分分布", "菜品雷达图"]
    )

# 主界面
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 首页", "🔍 查询菜品", "⭐ 推荐", "📝 评分评价", "📊 数据分析"])

with tab1:
    st.header("欢迎使用食堂菜品推荐系统")
    st.write(f"当前用户：**{system.current_user}**")
    st.write(f"系统中共有 **{len(system.dishes_data)}** 个菜品")
    
    # 显示部分菜品
    st.subheader("🍲 部分菜品展示")
    cols = st.columns(3)
    for i, (_, dish) in enumerate(system.dishes_data.head(9).iterrows()):
        with cols[i % 3]:
            st.metric(
                label=dish['菜品名称'],
                value=f"综合得分：{dish['综合得分']}"
            )
            st.caption(f"关键词：{dish['关键词'][:30]}...")

with tab2:
    st.header("菜品查询")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        dish_name = st.selectbox(
            "选择菜品",
            system.dishes_data['菜品名称'].tolist()
        )
    
    if dish_name:
        dish_info = system.dishes_data[system.dishes_data['菜品名称'] == dish_name].iloc[0]
        
        with col2:
            st.subheader(f"📋 {dish_name}")
        
        # 显示得分
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        with col_a:
            st.metric("口味得分", dish_info['口味得分'])
        with col_b:
            st.metric("营养得分", dish_info['营养得分'])
        with col_c:
            st.metric("热度得分", dish_info['热度得分'])
        with col_d:
            st.metric("性价比得分", dish_info['性价比得分'])
        with col_e:
            st.metric("综合得分", dish_info['综合得分'])
        
        # 显示关键词
        st.write("**关键词：**", dish_info['关键词'])

with tab3:
    st.header("个性化推荐")
    
    # 显示所有关键词
    all_keywords = set()
    for keywords in system.dishes_data['关键词']:
        if pd.isna(keywords):
            continue
        for kw in str(keywords).split(','):
            all_keywords.add(kw.strip())
    all_keywords = sorted(list(all_keywords))
    
    st.write("**可用的关键词：**")
    keyword_cols = st.columns(4)
    for i, kw in enumerate(all_keywords):
        with keyword_cols[i % 4]:
            st.caption(f"• {kw}")
    
    # 关键词输入
    selected_keywords = st.multiselect(
        "选择你感兴趣的关键词（可多选）",
        all_keywords
    )
    
    if st.button("开始推荐") and selected_keywords:
        recommendations = []
        
        for _, dish in system.dishes_data.iterrows():
            dish_keywords = []
            if pd.notna(dish.get('关键词', '')):
                dish_keywords = [k.strip().lower() for k in str(dish['关键词']).split(',')]
            
            match_count = 0
            for kw in selected_keywords:
                if kw.lower() in dish_keywords:
                    match_count += 1
            
            if match_count > 0:
                match_score = match_count / len(selected_keywords)
                total_score = match_score * 0.6 + dish.get('综合得分', 0) * 0.4
                recommendations.append({
                    '菜品名称': dish['菜品名称'],
                    '综合得分': dish.get('综合得分', 0),
                    '推荐得分': round(total_score, 2),
                    '匹配关键词数': match_count,
                    '口味': dish.get('口味得分', 0),
                    '营养': dish.get('营养得分', 0),
                    '热度': dish.get('热度得分', 0),
                    '性价比': dish.get('性价比得分', 0),
                    '关键词': dish.get('关键词', '')
                })
        
        recommendations.sort(key=lambda x: (x['匹配关键词数'], x['推荐得分']), reverse=True)
        
        if recommendations:
            st.subheader(f"为你推荐（匹配关键词：{', '.join(selected_keywords)}）")
            
            for i, rec in enumerate(recommendations[:5], 1):
                with st.expander(f"{i}. {rec['菜品名称']} (推荐得分：{rec['推荐得分']:.2f})"):
                    cols = st.columns(4)
                    cols[0].metric("口味", rec['口味'])
                    cols[1].metric("营养", rec['营养'])
                    cols[2].metric("热度", rec['热度'])
                    cols[3].metric("性价比", rec['性价比'])
                    st.write(f"匹配关键词数：{rec['匹配关键词数']}")
                    st.write(f"关键词：{rec['关键词']}")
        else:
            st.warning("没有找到匹配的菜品")

with tab4:
    st.header("评分与评价")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⭐ 为菜品评分")
        rate_dish = st.selectbox(
            "选择要评分的菜品",
            system.dishes_data['菜品名称'].tolist(),
            key="rate_select"
        )
        rating = st.slider("评分", 1.0, 5.0, 3.0, 0.5)
        
        if st.button("提交评分"):
            # 添加评分
            new_rating = pd.DataFrame({
                '用户ID': [system.current_user],
                '菜品名称': [rate_dish],
                '评分': [rating]
            })
            system.user_ratings = pd.concat([system.user_ratings, new_rating], ignore_index=True)
            system.user_ratings.to_csv("用户评分记录.csv", index=False, encoding='utf-8')
            st.success(f"已为 '{rate_dish}' 评分 {rating} 分")
    
    with col2:
        st.subheader("📝 评价菜品")
        review_dish = st.selectbox(
            "选择要评价的菜品",
            system.dishes_data['菜品名称'].tolist(),
            key="review_select"
        )
        review_text = st.text_area("写下你的评价")
        
        if st.button("提交评价"):
            if review_text:
                # 简单的情感分析
                positive_words = ['好吃', '美味', '喜欢', '不错', '推荐', '赞', '棒', '满意']
                negative_words = ['难吃', '不好', '太咸', '太油', '贵', '失望', '差']
                
                text_lower = review_text.lower()
                sentiment_score = 5.0
                
                for word in positive_words:
                    if word in text_lower:
                        sentiment_score += 0.3
                
                for word in negative_words:
                    if word in text_lower:
                        sentiment_score -= 0.5
                
                sentiment_score = max(1.0, min(10.0, sentiment_score))
                sentiment_desc = "好评" if sentiment_score > 5 else "差评" if sentiment_score < 5 else "中评"
                
                # 添加评价
                new_review = pd.DataFrame({
                    '用户ID': [system.current_user],
                    '菜品名称': [review_dish],
                    '评价内容': [review_text],
                    '情感得分': [sentiment_score],
                    '评价时间': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                })
                system.user_reviews = pd.concat([system.user_reviews, new_review], ignore_index=True)
                system.user_reviews.to_csv("用户评价记录.csv", index=False, encoding='utf-8')
                
                st.success(f"评价已提交！情感分析：{sentiment_desc}（得分：{sentiment_score:.1f}）")
            else:
                st.warning("请先输入评价内容")

with tab5:
    st.header("数据分析")
    
    # TOP菜品排名
    if viz_option == "TOP菜品排名" or st.button("显示TOP菜品排名"):
        st.subheader("🏆 TOP10菜品综合得分排名")
        
        top_dishes = system.dishes_data.sort_values('综合得分', ascending=False).head(10)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = np.arange(len(top_dishes))
        bars = ax.barh(y_pos, top_dishes['综合得分'], color='steelblue', height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_dishes['菜品名称'])
        ax.set_xlabel('综合得分')
        ax.set_title('TOP10 菜品综合得分排名')
        ax.invert_yaxis()
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{width:.2f}', ha='left', va='center', fontsize=10)
        
        st.pyplot(fig)
    
    # 得分分布
    if viz_option == "得分分布" or st.button("显示得分分布"):
        st.subheader("📈 各维度得分分布")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 口味得分分布
        axes[0, 0].hist(system.dishes_data['口味得分'], bins=10, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('口味得分分布')
        axes[0, 0].set_xlabel('口味得分')
        axes[0, 0].set_ylabel('菜品数量')
        
        # 营养得分分布
        axes[0, 1].hist(system.dishes_data['营养得分'], bins=10, alpha=0.7, color='lightgreen')
        axes[0, 1].set_title('营养得分分布')
        axes[0, 1].set_xlabel('营养得分')
        axes[0, 1].set_ylabel('菜品数量')
        
        # 热度得分分布
        axes[1, 0].hist(system.dishes_data['热度得分'], bins=10, alpha=0.7, color='salmon')
        axes[1, 0].set_title('热度得分分布')
        axes[1, 0].set_xlabel('热度得分')
        axes[1, 0].set_ylabel('菜品数量')
        
        # 性价比得分分布
        axes[1, 1].hist(system.dishes_data['性价比得分'], bins=10, alpha=0.7, color='gold')
        axes[1, 1].set_title('性价比得分分布')
        axes[1, 1].set_xlabel('性价比得分')
        axes[1, 1].set_ylabel('菜品数量')
        
        plt.tight_layout()
        st.pyplot(fig)

# 页脚
st.markdown("---")
st.caption("© 2025 食堂菜品推荐系统 | 数据更新于每日营业后")