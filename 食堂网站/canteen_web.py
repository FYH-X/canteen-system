import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime

# 强制设置UTF-8编码
if hasattr(sys.stdout, 'encoding'):
    if sys.stdout.encoding != 'UTF-8':
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# 设置页面
st.set_page_config(
    page_title="食堂菜品推荐系统",
    page_icon="🍽️",
    layout="wide"
)

# 设置中文字体 - 简化为最通用的设置
try:
    # 尝试设置中文字体
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'Arial']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 12
except:
    # 如果失败，使用默认设置
    pass

class CanteenRecommendationSystem:
    def __init__(self):
        self.dishes_data = None
        self.user_ratings = pd.DataFrame(columns=['用户ID', '菜品名称', '评分'])
        self.user_reviews = pd.DataFrame(columns=['用户ID', '菜品名称', '评价内容', '情感得分', '评价时间'])
        self.current_user = "guest"
    
    def load_dishes_data(self):
        """加载菜品数据 - 简化版本"""
        try:
            import os
            
            # 显示调试信息
            st.info("正在搜索数据文件...")
            
            # 简化：只尝试根目录的data.csv，用最简单的方式读取
            if os.path.exists("data.csv"):
                try:
                    # 先尝试最简单的读取方式
                    self.dishes_data = pd.read_csv("data.csv")
                    st.success("✅ 成功读取 data.csv")
                except:
                    # 如果失败，尝试指定编码
                    try:
                        self.dishes_data = pd.read_csv("data.csv", encoding='utf-8')
                        st.success("✅ 成功读取 data.csv (UTF-8)")
                    except:
                        try:
                            self.dishes_data = pd.read_csv("data.csv", encoding='gbk')
                            st.success("✅ 成功读取 data.csv (GBK)")
                        except Exception as e:
                            st.error(f"❌ 读取失败: {str(e)}")
                            return False
            elif os.path.exists("食堂菜品数据.csv"):
                try:
                    self.dishes_data = pd.read_csv("食堂菜品数据.csv", encoding='gbk')
                    st.success("✅ 成功读取 食堂菜品数据.csv (GBK)")
                except:
                    try:
                        self.dishes_data = pd.read_csv("食堂菜品数据.csv", encoding='utf-8')
                        st.success("✅ 成功读取 食堂菜品数据.csv (UTF-8)")
                    except Exception as e:
                        st.error(f"❌ 读取失败: {str(e)}")
                        return False
            else:
                st.error("❌ 找不到数据文件！")
                st.write("请确保根目录有 data.csv 或 食堂菜品数据.csv 文件")
                return False
            
            # 简化：直接重命名列（假设格式正确）
            if len(self.dishes_data.columns) >= 6:
                self.dishes_data.columns = ['菜品名称', '口味', '营养', '热度', '性价比', '关键词']
            
            # 计算综合得分
            self.dishes_data['综合得分'] = (
                self.dishes_data['口味'] * 0.4 +
                self.dishes_data['营养'] * 0.2 +
                self.dishes_data['热度'] * 0.2 +
                self.dishes_data['性价比'] * 0.2
            ).round(2)
            
            return True
            
        except Exception as e:
            st.error(f"❌ 加载数据失败: {str(e)}")
            return False

# 创建系统实例
system = CanteenRecommendationSystem()

# 网站标题
st.title("🍽️ 食堂菜品推荐系统")
st.markdown("---")

# 先加载数据
with st.spinner("正在加载菜品数据..."):
    if not system.load_dishes_data():
        st.error("无法加载菜品数据！")
        st.stop()

# 显示成功信息
if system.dishes_data is not None:
    st.success(f"✅ 数据加载成功！共有 {len(system.dishes_data)} 个菜品")

# 侧边栏
with st.sidebar:
    st.header("👤 用户登录")
    user_id = st.text_input("用户ID", value="游客")
    if st.button("登录"):
        st.success(f"欢迎 {user_id}!")
    
    st.markdown("---")
    st.header("📊 功能菜单")

# 主界面
tab1, tab2, tab3, tab4 = st.tabs(["🏠 首页", "🔍 查询", "⭐ 推荐", "📊 图表"])

with tab1:
    st.header("菜品列表")
    st.dataframe(system.dishes_data[['菜品名称', '口味', '营养', '热度', '性价比', '综合得分']].head(10))
    
    st.header("TOP 5 菜品")
    top5 = system.dishes_data.sort_values('综合得分', ascending=False).head(5)
    for i, (_, dish) in enumerate(top5.iterrows(), 1):
        st.write(f"{i}. **{dish['菜品名称']}** - 综合得分: {dish['综合得分']}")

with tab2:
    st.header("菜品查询")
    dish_name = st.selectbox("选择菜品", system.dishes_data['菜品名称'].tolist())
    
    if dish_name:
        dish = system.dishes_data[system.dishes_data['菜品名称'] == dish_name].iloc[0]
        st.write(f"**{dish_name}**")
        st.write(f"口味: {dish['口味']} | 营养: {dish['营养']}")
        st.write(f"热度: {dish['热度']} | 性价比: {dish['性价比']}")
        st.write(f"综合得分: {dish['综合得分']}")
        st.write(f"关键词: {dish['关键词']}")

with tab3:
    st.header("个性化推荐")
    
    # 提取关键词
    all_keywords = []
    for keywords in system.dishes_data['关键词']:
        if pd.isna(keywords):
            continue
        for kw in str(keywords).split(','):
            all_keywords.append(kw.strip())
    
    unique_keywords = sorted(set(all_keywords))
    
    selected = st.multiselect("选择关键词", unique_keywords[:20])  # 只显示前20个
    
    if st.button("推荐") and selected:
        results = []
        for _, dish in system.dishes_data.iterrows():
            dish_keywords = str(dish['关键词']).split(',')
            match_count = sum(1 for kw in selected if kw in dish_keywords)
            if match_count > 0:
                results.append({
                    '菜品': dish['菜品名称'],
                    '综合得分': dish['综合得分'],
                    '匹配数': match_count
                })
        
        if results:
            results.sort(key=lambda x: (x['匹配数'], x['综合得分']), reverse=True)
            st.subheader("推荐结果")
            for i, res in enumerate(results[:5], 1):
                st.write(f"{i}. **{res['菜品']}** (匹配: {res['匹配数']}, 得分: {res['综合得分']})")
        else:
            st.warning("没有找到匹配的菜品")

with tab4:
    st.header("数据图表")
    
    # 使用英文图表避免字体问题
    option = st.selectbox("选择图表", ["TOP10排名", "得分分布"])
    
    if option == "TOP10排名":
        top10 = system.dishes_data.sort_values('综合得分', ascending=False).head(10)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = range(len(top10))
        bars = ax.barh(y_pos, top10['综合得分'], color='skyblue')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top10['菜品名称'])
        ax.set_xlabel('Score')
        ax.set_title('TOP 10 Dishes')
        ax.invert_yaxis()
        
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, f'{width:.1f}', 
                   ha='left', va='center')
        
        st.pyplot(fig)
    
    elif option == "得分分布":
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 使用英文标题
        axes[0, 0].hist(system.dishes_data['口味'], bins=5, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Taste')
        axes[0, 0].set_xlabel('Score')
        axes[0, 0].set_ylabel('Count')
        
        axes[0, 1].hist(system.dishes_data['营养'], bins=5, alpha=0.7, color='lightgreen')
        axes[0, 1].set_title('Nutrition')
        axes[0, 1].set_xlabel('Score')
        axes[0, 1].set_ylabel('Count')
        
        axes[1, 0].hist(system.dishes_data['热度'], bins=5, alpha=0.7, color='salmon')
        axes[1, 0].set_title('Popularity')
        axes[1, 0].set_xlabel('Score')
        axes[1, 0].set_ylabel('Count')
        
        axes[1, 1].hist(system.dishes_data['性价比'], bins=5, alpha=0.7, color='gold')
        axes[1, 1].set_title('Value for Money')
        axes[1, 1].set_xlabel('Score')
        axes[1, 1].set_ylabel('Count')
        
        plt.tight_layout()
        st.pyplot(fig)

# 页脚
st.markdown("---")
st.caption("© 2025 食堂菜品系统")