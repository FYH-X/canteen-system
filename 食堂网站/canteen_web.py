import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 防止GUI错误
import matplotlib.pyplot as plt

# 设置页面
st.set_page_config(
    page_title="食堂菜品推荐系统",
    page_icon="🍽️",
    layout="wide"
)

# 禁用matplotlib的交互模式
plt.ioff()

class CanteenRecommendationSystem:
    def __init__(self):
        self.dishes_data = None
        self.user_ratings = pd.DataFrame(columns=['用户ID', '菜品名称', '评分'])
        self.user_reviews = pd.DataFrame(columns=['用户ID', '菜品名称', '评价内容', '情感得分', '评价时间'])
        self.current_user = "游客"
        self.load_dishes_data()
    
    def load_dishes_data(self):
        """加载菜品数据"""
        try:
            # 检查文件是否存在
            if os.path.exists("data.csv"):
                filename = "data.csv"
            elif os.path.exists("食堂菜品数据.csv"):
                filename = "食堂菜品数据.csv"
            else:
                st.error("❌ 找不到数据文件！请确保有 data.csv 或 食堂菜品数据.csv")
                return False
            
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb18030', 'latin1']
            for encoding in encodings:
                try:
                    self.dishes_data = pd.read_csv(filename, encoding=encoding)
                    break
                except:
                    continue
            
            if self.dishes_data is None:
                st.error("❌ 无法读取数据文件")
                return False
            
            # 修复列名
            if len(self.dishes_data.columns) >= 6:
                self.dishes_data.columns = ['菜品名称', '口味得分', '营养得分', '热度得分', '性价比得分', '关键词']
            
            # 确保数值列是数字
            score_cols = ['口味得分', '营养得分', '热度得分', '性价比得分']
            for col in score_cols:
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
            st.error(f"加载数据失败: {str(e)}")
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
    
    def add_rating(self, dish_name, rating):
        """添加用户评分"""
        new_rating = pd.DataFrame({
            '用户ID': [self.current_user],
            '菜品名称': [dish_name],
            '评分': [rating]
        })
        self.user_ratings = pd.concat([self.user_ratings, new_rating], ignore_index=True)
        self.user_ratings.to_csv("用户评分记录.csv", index=False, encoding='utf-8')
        return True
    
    def add_review(self, dish_name, review_text):
        """添加用户评价并进行情感分析"""
        # 情感分析
        positive_words = ['好吃', '美味', '喜欢', '不错', '推荐', '赞', '棒', '满意', '好', '香', '鲜', '爽']
        negative_words = ['难吃', '不好', '太咸', '太油', '贵', '失望', '差', '冷', '硬', '腻', '少']
        
        text_lower = review_text.lower()
        sentiment_score = 5.0
        
        for word in positive_words:
            if word in text_lower:
                sentiment_score += 0.3
        
        for word in negative_words:
            if word in text_lower:
                sentiment_score -= 0.5
        
        sentiment_score = max(1.0, min(10.0, sentiment_score))
        
        # 添加评价
        new_review = pd.DataFrame({
            '用户ID': [self.current_user],
            '菜品名称': [dish_name],
            '评价内容': [review_text],
            '情感得分': [sentiment_score],
            '评价时间': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        self.user_reviews = pd.concat([self.user_reviews, new_review], ignore_index=True)
        self.user_reviews.to_csv("用户评价记录.csv", index=False, encoding='utf-8')
        
        return sentiment_score
    
    def recommend_by_keywords(self, keywords):
        """根据关键词推荐"""
        recommendations = []
        
        for _, dish in self.dishes_data.iterrows():
            dish_keywords = []
            if pd.notna(dish.get('关键词', '')):
                dish_keywords = [k.strip().lower() for k in str(dish['关键词']).split(',')]
            
            match_count = 0
            for kw in keywords:
                if kw.lower() in dish_keywords:
                    match_count += 1
            
            if match_count > 0:
                match_score = match_count / len(keywords)
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
        return recommendations[:5]

# ==================== 创建系统实例 ====================
system = CanteenRecommendationSystem()

# ==================== 网站标题 ====================
st.title("🍽️ 食堂菜品评分与推荐系统")
st.markdown("---")

# ==================== 侧边栏 ====================
with st.sidebar:
    st.header("👤 用户登录")
    user_id = st.text_input("输入用户ID", value="游客")
    if st.button("登录"):
        system.current_user = user_id
        st.success(f"欢迎 {user_id}!")
    
    st.markdown("---")
    st.header("📊 快速查看")

# ==================== 主界面 ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 首页", "🔍 查询菜品", "⭐ 推荐", "📝 评分评价", "📊 数据分析"])

with tab1:
    st.header("欢迎使用食堂菜品推荐系统")
    st.write(f"当前用户：**{system.current_user}**")
    
    if system.dishes_data is not None:
        st.success(f"✅ 系统中共有 **{len(system.dishes_data)}** 个菜品")
        
        # 显示TOP5菜品
        st.subheader("🏆 TOP 5 菜品")
        top5 = system.dishes_data.sort_values('综合得分', ascending=False).head(5)
        
        for i, (_, dish) in enumerate(top5.iterrows(), 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{i}. **{dish['菜品名称']}**")
            with col2:
                st.metric("", f"{dish['综合得分']}")
        
        # 显示部分菜品
        st.subheader("🍲 菜品展示")
        cols = st.columns(3)
        for i, (_, dish) in enumerate(system.dishes_data.head(9).iterrows()):
            with cols[i % 3]:
                with st.container():
                    st.write(f"**{dish['菜品名称']}**")
                    st.write(f"综合得分：{dish['综合得分']}")
                    st.progress(dish['综合得分'] / 5)

with tab2:
    st.header("菜品查询")
    
    if system.dishes_data is not None:
        dish_name = st.selectbox(
            "选择菜品",
            system.dishes_data['菜品名称'].tolist()
        )
        
        if dish_name:
            dish_info = system.dishes_data[system.dishes_data['菜品名称'] == dish_name].iloc[0]
            
            st.subheader(f"📋 {dish_name}")
            
            # 显示得分
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("口味", dish_info['口味得分'])
            with col2:
                st.metric("营养", dish_info['营养得分'])
            with col3:
                st.metric("热度", dish_info['热度得分'])
            with col4:
                st.metric("性价比", dish_info['性价比得分'])
            with col5:
                st.metric("综合", dish_info['综合得分'])
            
            # 进度条显示
            st.write("**各维度评分：**")
            cols = st.columns(4)
            with cols[0]:
                st.write("口味")
                st.progress(dish_info['口味得分'] / 5)
            with cols[1]:
                st.write("营养")
                st.progress(dish_info['营养得分'] / 5)
            with cols[2]:
                st.write("热度")
                st.progress(dish_info['热度得分'] / 5)
            with cols[3]:
                st.write("性价比")
                st.progress(dish_info['性价比得分'] / 5)
            
            st.write(f"**关键词：** {dish_info['关键词']}")

with tab3:
    st.header("个性化推荐")
    
    if system.dishes_data is not None:
        # 提取所有关键词
        all_keywords = []
        for keywords in system.dishes_data['关键词']:
            if pd.isna(keywords):
                continue
            for kw in str(keywords).split(','):
                all_keywords.append(kw.strip())
        
        unique_keywords = sorted(set(all_keywords))
        
        selected_keywords = st.multiselect(
            "选择你感兴趣的关键词（可多选）",
            unique_keywords[:30]
        )
        
        if st.button("开始推荐") and selected_keywords:
            recommendations = system.recommend_by_keywords(selected_keywords)
            
            if recommendations:
                st.subheader(f"为你推荐（匹配关键词：{', '.join(selected_keywords)}）")
                
                for i, rec in enumerate(recommendations, 1):
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
    
    if system.dishes_data is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⭐ 为菜品评分")
            rate_dish = st.selectbox(
                "选择要评分的菜品",
                system.dishes_data['菜品名称'].tolist(),
                key="rate_select"
            )
            rating = st.slider("评分", 1.0, 5.0, 3.0, 0.5)
            
            if st.button("提交评分", key="submit_rating"):
                if system.add_rating(rate_dish, rating):
                    st.success(f"✅ 已为 '{rate_dish}' 评分 {rating} 分")
        
        with col2:
            st.subheader("📝 评价菜品")
            review_dish = st.selectbox(
                "选择要评价的菜品",
                system.dishes_data['菜品名称'].tolist(),
                key="review_select"
            )
            review_text = st.text_area("写下你的评价（我们会自动分析情感）")
            
            if st.button("提交评价", key="submit_review"):
                if review_text:
                    sentiment_score = system.add_review(review_dish, review_text)
                    sentiment_desc = "好评" if sentiment_score > 5 else "差评" if sentiment_score < 5 else "中评"
                    st.success(f"✅ 评价已提交！情感分析：{sentiment_desc}（得分：{sentiment_score:.1f}）")
                else:
                    st.warning("请先输入评价内容")

with tab5:
    st.header("数据分析")
    
    if system.dishes_data is not None:
        # 方法1：使用表格和进度条代替图表
        option = st.selectbox("选择分析类型", ["TOP10菜品", "得分统计", "维度对比"])
        
        if option == "TOP10菜品":
            st.subheader("🏆 TOP10菜品排名")
            
            top10 = system.dishes_data.sort_values('综合得分', ascending=False).head(10)
            
            for i, (_, dish) in enumerate(top10.iterrows(), 1):
                with st.container():
                    col1, col2, col3 = st.columns([2, 3, 1])
                    with col1:
                        st.write(f"{i}. **{dish['菜品名称']}**")
                    with col2:
                        st.progress(dish['综合得分'] / 5)
                    with col3:
                        st.write(f"{dish['综合得分']}")
                    st.write(f"口味:{dish['口味得分']} 营养:{dish['营养得分']} 热度:{dish['热度得分']} 性价比:{dish['性价比得分']}")
                    st.markdown("---")
        
        elif option == "得分统计":
            st.subheader("📊 各维度统计")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("平均口味", f"{system.dishes_data['口味得分'].mean():.1f}")
                st.write(f"最高: {system.dishes_data['口味得分'].max():.1f}")
                st.write(f"最低: {system.dishes_data['口味得分'].min():.1f}")
            
            with col2:
                st.metric("平均营养", f"{system.dishes_data['营养得分'].mean():.1f}")
                st.write(f"最高: {system.dishes_data['营养得分'].max():.1f}")
                st.write(f"最低: {system.dishes_data['营养得分'].min():.1f}")
            
            with col3:
                st.metric("平均热度", f"{system.dishes_data['热度得分'].mean():.1f}")
                st.write(f"最高: {system.dishes_data['热度得分'].max():.1f}")
                st.write(f"最低: {system.dishes_data['热度得分'].min():.1f}")
            
            with col4:
                st.metric("平均性价比", f"{system.dishes_data['性价比得分'].mean():.1f}")
                st.write(f"最高: {system.dishes_data['性价比得分'].max():.1f}")
                st.write(f"最低: {system.dishes_data['性价比得分'].min():.1f}")
        
        elif option == "维度对比":
            st.subheader("📈 维度对比")
            
            selected_dish = st.selectbox(
                "选择菜品",
                system.dishes_data['菜品名称'].tolist()
            )
            
            if selected_dish:
                dish = system.dishes_data[system.dishes_data['菜品名称'] == selected_dish].iloc[0]
                
                # 使用简单的条形显示
                st.write("**各维度评分：**")
                
                metrics = ['口味得分', '营养得分', '热度得分', '性价比得分']
                colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                
                for metric, color in zip(metrics, colors):
                    score = dish[metric]
                    col1, col2, col3 = st.columns([2, 5, 1])
                    with col1:
                        st.write(metric.replace('得分', ''))
                    with col2:
                        st.progress(score / 5)
                    with col3:
                        st.write(f"{score}")

# ==================== 页脚 ====================
st.markdown("---")
st.caption("© 2025 食堂菜品推荐系统 | 数据更新于每日营业后")