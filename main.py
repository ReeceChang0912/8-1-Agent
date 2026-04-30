"""
家庭智能管家 - Streamlit Web界面
"""

import streamlit as st
from family_agent.core import FamilyAgentCore
from family_agent.role_manager import FamilyMember, InteractionStyle, PermissionLevel
import datetime


# 自定义CSS样式
st.markdown("""
<style>
    /* 全局样式 - 白色背景 */
    .stApp {
        background-color: #ffffff;
    }
    
    /* 主容器 */
    .main > div {
        background-color: rgba(255, 255, 255, 0.98);
        border-radius: 15px;
        padding: 2rem;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #2d3748 !important;
        font-weight: 700 !important;
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    .sidebar .sidebar-content {
        background: transparent;
    }
    
    /* 聊天消息样式 */
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* 卡片样式 */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
    
    /* 警告框样式 */
    .stAlert {
        border-radius: 10px;
        border: none;
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    /* 成功提示 */
    .success-box {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #2d3748;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# 页面配置
st.set_page_config(
    page_title="🏡 家庭智能管家",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化Agent
@st.cache_resource
def init_agent():
    return FamilyAgentCore(data_dir="data")


def main():
    agent = init_agent()
    
    # 侧边栏
    with st.sidebar:
        st.markdown("## 🏡 家庭智能管家")
        st.markdown("---")
        
        # 用户选择
        users = ["👤 未登录"] + [f"{name}" for name in agent.members.keys()]
        selected_user = st.selectbox("当前用户", users, label_visibility="collapsed")
        
        if selected_user != "👤 未登录":
            user_name = selected_user
            agent.role_manager.set_current_user(user_name)
            st.success(f"✨ 欢迎，{user_name}！")
        
        st.markdown("---")
        
        # 功能导航
        menu_options = {
            "💬 智能对话": "chat",
            "👨‍👩‍👧‍👦 家庭成员": "members",
            "📅 日程管理": "schedule",
            "🛒 购物清单": "shopping",
            "📸 照片记忆": "photos",
            "📚 知识库": "knowledge",
            "🏠 智能家居": "smarthome",
            "💬 微信集成": "wechat",
            "🔌 MCP协议": "mcp",
            "📊 统计信息": "stats"
        }
        
        menu = st.radio(
            "功能菜单",
            list(menu_options.keys()),
            label_visibility="collapsed"
        )
    
    # 主内容区
    if "💬 智能对话" in menu:
        user_id = None if selected_user == "👤 未登录" else selected_user.replace("👤 ", "")
        chat_interface(agent, user_id)
    elif "👨‍👩‍👧‍👦 家庭成员" in menu:
        member_management(agent)
    elif "📅 日程管理" in menu:
        schedule_management(agent)
    elif "🛒 购物清单" in menu:
        shopping_list_interface(agent)
    elif "📸 照片记忆" in menu:
        photo_memory_interface(agent)
    elif "📚 知识库" in menu:
        knowledge_base_interface(agent)
    elif "🏠 智能家居" in menu:
        smart_home_interface(agent)
    elif "💬 微信集成" in menu:
        wechat_interface(agent)
    elif "🔌 MCP协议" in menu:
        mcp_interface(agent)
    elif "📊 统计信息" in menu:
        statistics_view(agent)


def chat_interface(agent, current_user):
    """聊天界面"""
    st.markdown("## 💬 智能对话")
    st.markdown("与家庭智能助手进行自然交流")
    st.markdown("---")
    
    # 显示情绪状态
    if 'last_emotion' in st.session_state:
        emotion = st.session_state.last_emotion
        emotion_map = {
            'anger': ('😠', '检测到您有些生气，我会耐心倾听'),
            'sadness': ('😢', '感受到您的难过，我在这里陪伴您'),
            'anxiety': ('😰', '察觉到您的焦虑，让我们一起放松'),
            'joy': ('😊', '感受到您的快乐，真棒！'),
            'calm': ('😌', '平和的状态很好')
        }
        if emotion in emotion_map:
            icon, message = emotion_map[emotion]
            if emotion in ['anger', 'sadness', 'anxiety']:
                st.warning(f"{icon} {message}")
            else:
                st.info(f"{icon} {message}")
    
    # 聊天历史
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
    
    # 输入框
    if prompt := st.chat_input("💭 你想说什么？", key="chat_input"):
        # 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 调用Agent
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = agent.chat(prompt, user_id=current_user if current_user != "未登录" else None)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # 检测情绪
                emotion_result = agent.emotion_engine.detect_emotion(prompt)
                st.session_state.last_emotion = emotion_result['primary_emotion'].value


def member_management(agent):
    """家庭成员管理"""
    st.markdown("## 👨‍👩‍👧‍👦 家庭成员管理")
    st.markdown("管理家庭成员信息和偏好设置")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.markdown("### ➕ 添加成员")
        st.markdown("<div style='background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
        
        name = st.text_input("姓名")
        role = st.selectbox("角色", ["爸爸", "妈妈", "爷爷", "奶奶", "孩子", "其他"])
        age = st.number_input("年龄", min_value=1, max_value=120, value=30)
        side = st.selectbox("家庭方", ["core", "husband_side", "wife_side"])
        
        style_options = {
            "平等交流": InteractionStyle.PEER,
            "童趣模式": InteractionStyle.CHILD,
            "长辈模式": InteractionStyle.ELDER,
            "正式模式": InteractionStyle.FORMAL
        }
        style_name = st.selectbox("交互风格", list(style_options.keys()))
        
        permission_options = {
            "管理员": PermissionLevel.ADMIN,
            "普通成员": PermissionLevel.MEMBER,
            "访客": PermissionLevel.GUEST,
            "儿童": PermissionLevel.CHILD
        }
        perm_name = st.selectbox("权限等级", list(permission_options.keys()))
        
        if st.button("➕ 添加成员", use_container_width=True, key="add_member_btn"):
            if name:
                member = FamilyMember(
                    name=name,
                    role=role,
                    age=age,
                    side=side,
                    interaction_style=style_options[style_name],
                    permission=permission_options[perm_name]
                )
                agent.add_member(member)
                st.success(f"✅ 已添加成员：{name}")
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 成员列表")
        
        if agent.members:
            for name, member in agent.members.items():
                role_icons = {
                    "爸爸": "👨",
                    "妈妈": "👩",
                    "爷爷": "👴",
                    "奶奶": "👵",
                    "孩子": "👶",
                    "其他": "👤"
                }
                icon = role_icons.get(member.role, "👤")
                
                with st.expander(f"{icon} {name} ({member.role})"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**🎂 年龄**: {member.age}")
                        st.markdown(f"**🏠 家庭方**: {member.side}")
                    with col_b:
                        st.markdown(f"**💬 交互风格**: {member.interaction_style.value}")
                        st.markdown(f"**🔐 权限**: {member.permission.value}")
                    
                    if member.preferences:
                        st.markdown(f"**❤️ 喜好**: {', '.join(member.preferences)}")
        else:
            st.info("📝 暂无成员，请在左侧添加")


def schedule_management(agent):
    """日程管理"""
    st.markdown("## 📅 日程管理")
    st.markdown("管理家庭日程和提醒事项")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["➕ 添加提醒", "📋 查看提醒"])
    
    with tab1:
        st.markdown("### 设置新提醒")
        
        col_a, col_b = st.columns(2)
        with col_a:
            event_title = st.text_input("📌 事件标题")
            event_date = st.date_input("📆 日期", datetime.date.today())
        with col_b:
            event_time = st.time_input("⏰ 时间", datetime.time(9, 0))
        
        if st.button("✅ 设置提醒", use_container_width=True):
            if event_title:
                datetime_str = f"{event_date} {event_time}"
                agent.add_reminder(datetime_str, event_title)
                st.success(f"✅ 已设置提醒：{event_title}")
    
    with tab2:
        st.markdown("### 即将到来的事件")
        
        if agent.reminders:
            for i, reminder in enumerate(agent.reminders[-10:], 1):
                priority_color = "🔴" if i <= 3 else "🟡" if i <= 6 else "🟢"
                st.info(f"{priority_color} **{reminder['event']}** - {reminder['date']}")
        else:
            st.info("📝 暂无提醒")


def knowledge_base_interface(agent):
    """知识库界面"""
    st.markdown("## 📚 知识库")
    st.markdown("存储和检索家庭知识和经验")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔍 搜索知识", "➕ 添加文档"])
    
    with tab1:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            query = st.text_input("🔎 搜索问题", placeholder="输入你想查询的内容...")
        with col_b:
            category = st.selectbox("📁 分类", ["全部"] + list(agent.knowledge_base.CATEGORIES.keys()))
        
        if st.button("🔍 搜索", use_container_width=True):
            if query:
                cat = None if category == "全部" else category
                results = agent.knowledge_base.search(query, category=cat, n_results=5)
                
                if results:
                    st.markdown("### 📊 搜索结果")
                    for i, result in enumerate(results, 1):
                        with st.expander(f"📄 结果 {i}"):
                            st.write(result['content'])
                            st.caption(f"📁 来源: {result['metadata'].get('source', '未知')}")
                else:
                    st.info("🔍 未找到相关知识")
    
    with tab2:
        st.markdown("### 添加文本文档")
        
        title = st.text_input("📝 标题")
        text_content = st.text_area("📄 内容", height=200, placeholder="在此输入文档内容...")
        kb_category = st.selectbox("📁 分类", list(agent.knowledge_base.CATEGORIES.keys()))
        
        if st.button("💾 添加到知识库", use_container_width=True):
            if title and text_content:
                doc_id = agent.knowledge_base.add_text(
                    text=text_content,
                    title=title,
                    category=kb_category
                )
                st.success(f"✅ 已添加文档 ID: {doc_id}")


def statistics_view(agent):
    """统计信息"""
    st.markdown("## 📊 系统统计")
    st.markdown("查看家庭智能管家的运行状态")
    st.markdown("---")
    
    memory_stats = agent.memory_manager.get_memory_stats()
    kb_stats = agent.knowledge_base.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style='margin: 0; color: #667eea;'>👨‍👩‍👧‍👦</h3>
            <h2 style='margin: 10px 0;'>{}</h2>
            <p style='margin: 0; color: #718096;'>家庭成员</p>
        </div>
        """.format(len(agent.members)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style='margin: 0; color: #667eea;'>💭</h3>
            <h2 style='margin: 10px 0;'>{}</h2>
            <p style='margin: 0; color: #718096;'>短期记忆</p>
        </div>
        """.format(memory_stats['short_term_count']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style='margin: 0; color: #667eea;'>📚</h3>
            <h2 style='margin: 10px 0;'>{}</h2>
            <p style='margin: 0; color: #718096;'>知识文档</p>
        </div>
        """.format(kb_stats['total_documents']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style='margin: 0; color: #667eea;'>📅</h3>
            <h2 style='margin: 10px 0;'>{}</h2>
            <p style='margin: 0; color: #718096;'>日程提醒</p>
        </div>
        """.format(len(agent.reminders)), unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 💭 记忆统计详情")
        st.json(memory_stats)
    
    with col_b:
        st.markdown("### 📚 知识库统计详情")
        st.json(kb_stats)


def shopping_list_interface(agent):
    """购物清单界面"""
    st.markdown("## 🛒 购物清单管理")
    st.markdown("智能管理家庭购物需求")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["➕ 添加物品", "📋 查看清单", "📊 统计分析"])
    
    with tab1:
        st.markdown("### 添加购物物品")
        
        col_a, col_b = st.columns(2)
        with col_a:
            item_name = st.text_input("🛍️ 物品名称", placeholder="例如：牛奶、鸡蛋")
            quantity = st.text_input("🔢 数量", value="1")
        with col_b:
            category = st.selectbox("📁 分类", [
                "food", "daily", "health", "home", "clothing", "electronics", "other"
            ], format_func=lambda x: {
                "food": "🍎 食品",
                "daily": "🧻 日用品",
                "health": "💊 健康",
                "home": "🏠 家居",
                "clothing": "👕 服装",
                "electronics": "📱 电子",
                "other": "📦 其他"
            }[x])
            priority = st.selectbox("⚡ 优先级", ["high", "medium", "low"], 
                                   format_func=lambda x: {"high": "🔴 高", "medium": "🟡 中", "low": "🟢 低"}[x])
        
        notes = st.text_area("📝 备注", placeholder="可选的备注信息...")
        
        if st.button("✅ 添加到清单", use_container_width=True):
            if item_name:
                agent.shopping_list.add_item(
                    name=item_name,
                    quantity=quantity,
                    category=category,
                    priority=priority,
                    notes=notes
                )
                st.success(f"✅ 已添加：{item_name}")
                st.rerun()
    
    with tab2:
        st.markdown("### 当前购物清单")
        
        items = agent.shopping_list.get_items()
        
        if items:
            # 按分类显示
            categories = {}
            for item in items:
                cat = item.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            category_names = {
                "food": "🍎 食品",
                "daily": "🧻 日用品",
                "health": "💊 健康",
                "home": "🏠 家居",
                "clothing": "👕 服装",
                "electronics": "📱 电子",
                "other": "📦 其他"
            }
            
            for cat, cat_items in categories.items():
                with st.expander(f"{category_names.get(cat, cat)} ({len(cat_items)}项)", expanded=True):
                    for i, item in enumerate(cat_items):
                        col_x, col_y, col_z = st.columns([4, 2, 1])
                        with col_x:
                            priority_icon = "🔴" if item.priority == "high" else "🟡" if item.priority == "medium" else "🟢"
                            st.markdown(f"{priority_icon} **{item.name}** × {item.quantity}")
                            if item.notes:
                                st.caption(f"📝 {item.notes}")
                        with col_y:
                            status = "✅" if item.purchased else "⬜"
                            st.markdown(status)
                        with col_z:
                            if st.button("删除", key=f"del_{i}_{item.name}"):
                                agent.shopping_list.remove_item(item.name)
                                st.rerun()
        else:
            st.info("📝 购物清单为空，请添加物品")
        
        # 批量操作
        if items:
            st.markdown("---")
            col_op1, col_op2 = st.columns(2)
            with col_op1:
                if st.button("🛒 生成采购路线", use_container_width=True):
                    route = agent.shopping_list.generate_shopping_route()
                    st.success("采购路线已生成！")
                    for i, step in enumerate(route, 1):
                        st.markdown(f"{i}. {step}")
            with col_op2:
                if st.button("🗑️ 清空已购", use_container_width=True):
                    agent.shopping_list.clear_purchased()
                    st.success("已清空已购物品")
                    st.rerun()
    
    with tab3:
        st.markdown("### 购物统计")
        
        stats = agent.shopping_list.get_shopping_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style='margin: 0; color: #667eea;'>📦</h3>
                <h2 style='margin: 10px 0;'>{stats['total_items']}</h2>
                <p style='margin: 0; color: #718096;'>总物品数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style='margin: 0; color: #667eea;'>✅</h3>
                <h2 style='margin: 10px 0;'>{stats['purchased']}</h2>
                <p style='margin: 0; color: #718096;'>已购买</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3 style='margin: 0; color: #667eea;'>⏳</h3>
                <h2 style='margin: 10px 0;'>{stats['unpurchased']}</h2>
                <p style='margin: 0; color: #718096;'>待购买</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            completion_rate = stats['completion_rate'] * 100
            st.markdown(f"""
            <div class="metric-card">
                <h3 style='margin: 0; color: #667eea;'>📊</h3>
                <h2 style='margin: 10px 0;'>{completion_rate:.1f}%</h2>
                <p style='margin: 0; color: #718096;'>完成率</p>
            </div>
            """, unsafe_allow_html=True)


def photo_memory_interface(agent):
    """照片记忆界面"""
    st.markdown("## 📸 照片记忆")
    st.markdown("记录和管理家庭美好时光")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📤 上传照片", "🔍 浏览回忆", "📅 那年今天"])
    
    with tab1:
        st.markdown("### 上传新照片")
        
        uploaded_file = st.file_uploader("选择照片", type=['jpg', 'jpeg', 'png', 'gif'])
        
        if uploaded_file:
            col_a, col_b = st.columns(2)
            with col_a:
                description = st.text_area("📝 描述", placeholder="这张照片的故事...")
                tags_input = st.text_input("🏷️ 标签", placeholder="用逗号分隔，例如：生日,聚会,家庭")
            with col_b:
                people = st.text_input("👥 人物", placeholder="照片中的人物")
                location = st.text_input("📍 地点", placeholder="拍摄地点")
            
            if st.button("💾 保存照片", use_container_width=True):
                import tempfile
                import os
                
                # 保存上传的文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                try:
                    # 解析标签和人物（转换为列表）
                    tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
                    people_list = [p.strip() for p in people.split(',') if p.strip()] if people else []
                    
                    # 添加到照片记忆
                    photo_id = agent.photo_memory.add_photo(
                        file_path=tmp_path,
                        description=description,
                        people=people_list,
                        location=location,
                        tags=tags
                    )
                    
                    st.success(f"✅ 照片已保存！ID: {photo_id}")
                    
                    # 清理临时文件
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    with tab2:
        st.markdown("### 浏览照片")
        
        # 搜索功能
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search_query = st.text_input("🔎 搜索照片", placeholder="输入关键词、人物或地点...")
        with col_filter:
            filter_type = st.selectbox("筛选", ["全部", "标签", "人物", "地点"])
        
        if st.button("🔍 搜索", use_container_width=True):
            if search_query:
                results = agent.photo_memory.search_photos(search_query)
                st.markdown(f"#### 找到 {len(results)} 张照片")
                
                if results:
                    cols = st.columns(3)
                    for i, photo in enumerate(results[:9]):  # 最多显示9张
                        with cols[i % 3]:
                            st.markdown(f"**{photo.description or '无描述'}**")
                            st.caption(f"📅 {photo.upload_date[:10]}")
                            if photo.people:
                                st.caption(f"👥 {', '.join(photo.people)}")
                            if photo.location:
                                st.caption(f"📍 {photo.location}")
                            if photo.tags:
                                st.caption(f"🏷️ {', '.join(photo.tags[:3])}")
                            st.markdown("---")
            else:
                st.info("请输入搜索关键词")
        
        # 显示所有照片
        all_photos = agent.photo_memory.get_all_photos()
        if all_photos and not search_query:
            st.markdown(f"#### 所有照片 ({len(all_photos)}张)")
            cols = st.columns(3)
            for i, photo in enumerate(all_photos[:9]):
                with cols[i % 3]:
                    st.markdown(f"**{photo.description or '无描述'}**")
                    st.caption(f"📅 {photo.upload_date[:10]}")
                    st.markdown("---")
    
    with tab3:
        st.markdown("### 📅 那年今天")
        
        today = datetime.date.today()
        st.markdown(f"**今天的日期**: {today.month}月{today.day}日")
        
        if st.button("🔍 查找去年的今天", use_container_width=True):
            memories = agent.photo_memory.get_memories_on_date(today.month, today.day)
            
            if memories:
                st.success(f"找到 {len(memories)} 个回忆！")
                
                for photo in memories:
                    with st.expander(f"📸 {photo.description or '未命名照片'} - {photo.upload_date[:10]}"):
                        st.markdown(f"**人物**: {', '.join(photo.people) if photo.people else '未知'}")
                        st.markdown(f"**地点**: {photo.location or '未知'}")
                        if photo.tags:
                            st.markdown(f"**标签**: {', '.join(photo.tags)}")
                        if photo.description:
                            st.markdown(f"**描述**: {photo.description}")
            else:
                st.info("📝 去年的今天没有照片记录")
        
        # 生成回忆故事
        st.markdown("---")
        st.markdown("### ✨ 生成回忆故事")
        
        if st.button("📖 生成本周回忆故事", use_container_width=True):
            story = agent.photo_memory.generate_memory_story(days=7)
            st.markdown(story)


def smart_home_interface(agent):
    """智能家居界面"""
    st.markdown("## 🏠 智能家居控制")
    st.markdown("连接和控制家庭智能设备")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🔌 连接设置", "💡 设备控制", "🎭 场景模式"])
    
    with tab1:
        st.markdown("### Home Assistant 连接配置")
        
        hass_url = st.text_input("🌐 Home Assistant URL", value="http://localhost:8123")
        api_token = st.text_input("🔑 API Token", type="password", placeholder="输入Long-lived Access Token")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 测试连接", use_container_width=True):
                agent.smart_home.hass_url = hass_url
                agent.smart_home.api_token = api_token
                agent.smart_home.headers = {
                    "Authorization": f"Bearer {api_token}" if api_token else "",
                    "Content-Type": "application/json"
                }
                
                success = agent.smart_home.test_connection()
                if success:
                    st.success("✅ 连接成功！")
                else:
                    st.error("❌ 连接失败，请检查URL和Token")
        
        with col2:
            status = agent.smart_home.get_devices_by_type("light")
            st.metric("已发现设备", len(status) if status else 0)
    
    with tab2:
        st.markdown("### 设备控制")
        
        # 自然语言控制
        command = st.text_input("💬 语音命令", placeholder="例如：打开客厅灯、设置温度25度")
        
        if st.button("🚀 执行命令", use_container_width=True):
            if command:
                result = agent.smart_home.execute_command(command)
                if "✅" in result:
                    st.success(result)
                else:
                    st.warning(result)
        
        st.markdown("---")
        st.markdown("### 快速控制")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💡 打开所有灯", use_container_width=True):
                lights = agent.smart_home.get_devices_by_type("light")
                for light in lights:
                    agent.smart_home.turn_on(light['entity_id'])
                st.success(f"已打开 {len(lights)} 个灯")
        
        with col2:
            if st.button("🌙 关闭所有灯", use_container_width=True):
                lights = agent.smart_home.get_devices_by_type("light")
                for light in lights:
                    agent.smart_home.turn_off(light['entity_id'])
                st.success(f"已关闭 {len(lights)} 个灯")
        
        with col3:
            if st.button("❄️ 舒适模式", use_container_width=True):
                climates = agent.smart_home.get_devices_by_type("climate")
                for climate in climates:
                    agent.smart_home.set_temperature(climate['entity_id'], 25)
                st.success("已设置为舒适温度")
    
    with tab3:
        st.markdown("### 场景模式")
        
        scenes = [
            {"id": "scene.movie_night", "name": "🎬 电影模式", "desc": "调暗灯光，营造观影氛围"},
            {"id": "scene.dinner_time", "name": "🍽️ 晚餐模式", "desc": "温馨的餐厅灯光"},
            {"id": "scene.bedtime", "name": "😴 睡眠模式", "desc": "关闭所有灯光，调整温度"},
            {"id": "scene.morning", "name": "☀️ 起床模式", "desc": "缓慢亮起灯光，播放音乐"}
        ]
        
        for scene in scenes:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{scene['name']}**")
                st.caption(scene['desc'])
            with col_b:
                if st.button("触发", key=f"scene_{scene['id']}"):
                    success = agent.smart_home.trigger_scene(scene['id'])
                    if success:
                        st.success("✅ 场景已触发")
                    else:
                        st.info("ℹ️ 场景未配置（需要Home Assistant）")


def wechat_interface(agent):
    """微信集成界面"""
    st.markdown("## 💬 微信集成")
    st.markdown("将家庭管家连接到微信")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📱 微信机器人", "📨 消息管理"])
    
    with tab1:
        st.markdown("### 微信机器人状态")
        
        status = agent.wechat.get_status()
        
        col1, col2 = st.columns(2)
        with col1:
            if status['is_running']:
                st.success("✅ 机器人运行中")
            else:
                st.warning("⚠️ 机器人未启动")
        
        with col2:
            st.metric("好友数", status['friends_count'])
        
        st.markdown("---")
        st.markdown("### 控制")
        
        col1, col2 = st.columns(2)
        with col1:
            if not status['is_running']:
                if st.button("🚀 启动机器人", use_container_width=True):
                    success = agent.wechat.start(auto_reply=True)
                    if success:
                        st.success("✅ 微信机器人已启动！请使用手机扫码登录")
                        st.info("💡 提示：首次使用需要扫描二维码登录微信")
                    else:
                        st.error("❌ 启动失败，请检查是否安装了 itchat-uos")
            else:
                st.info("机器人已在运行")
        
        with col2:
            if status['is_running']:
                if st.button("🛑 停止机器人", use_container_width=True):
                    agent.wechat.stop()
                    st.success("微信机器人已停止")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📦 安装依赖")
        st.code("pip install itchat-uos", language="bash")
        st.caption("注意：需要使用支持网页版微信的账号")
    
    with tab2:
        st.markdown("### 发送消息")
        
        user_name = st.text_input("👤 接收人昵称")
        message = st.text_area("📝 消息内容", placeholder="输入要发送的消息...")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📨 发送私聊", use_container_width=True):
                if user_name and message:
                    success = agent.wechat.send_reminder(user_name, message)
                    if success:
                        st.success(f"✅ 消息已发送给 {user_name}")
                    else:
                        st.error("❌ 发送失败，请检查机器人是否运行")
        
        with col2:
            group_name = st.text_input("👥 群聊名称")
            if st.button("📢 发送群消息", use_container_width=True):
                if group_name and message:
                    success = agent.wechat.send_to_group(group_name, message)
                    if success:
                        st.success(f"✅ 消息已发送到 {group_name}")
                    else:
                        st.error("❌ 发送失败")


def mcp_interface(agent):
    """MCP协议界面"""
    st.markdown("## 🔌 MCP协议 (Model Context Protocol)")
    st.markdown("标准化的AI工具调用接口")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🛠️ 可用工具", "🧪 工具测试", "📡 服务器信息"])
    
    with tab1:
        st.markdown("### 已注册的MCP工具")
        
        tools = agent.mcp.list_tools()
        
        for tool in tools:
            with st.expander(f"🔧 {tool['name']}"):
                st.markdown(f"**描述**: {tool['description']}")
                st.json(tool['parameters'])
    
    with tab2:
        st.markdown("### 工具调用测试")
        
        tool_name = st.selectbox(
            "选择工具",
            [t['name'] for t in agent.mcp.list_tools()]
        )
        
        # 根据不同工具显示不同参数
        if tool_name == "get_family_info":
            member_name = st.text_input("成员姓名（留空查询全部）")
            args = {"member_name": member_name} if member_name else {}
        
        elif tool_name == "get_schedule":
            import datetime
            date = st.date_input("日期", datetime.date.today())
            args = {"date": str(date)}
        
        elif tool_name == "manage_shopping_list":
            col_a, col_b = st.columns(2)
            with col_a:
                action = st.selectbox("操作", ["add", "remove", "list"])
            with col_b:
                item = st.text_input("物品名称") if action != "list" else ""
            args = {"action": action, "item": item} if item else {"action": action}
        
        elif tool_name == "search_memory":
            query = st.text_input("搜索关键词")
            args = {"query": query}
        
        else:
            args = {}
        
        if st.button("🚀 调用工具", use_container_width=True):
            result = agent.mcp.call_tool(tool_name, args)
            
            if result['success']:
                st.success("✅ 调用成功")
                st.json(result['result'])
            else:
                st.error(f"❌ 调用失败: {result.get('error')}")
    
    with tab3:
        st.markdown("### MCP服务器信息")
        
        server_info = agent.mcp.get_mcp_server_info()
        st.json(server_info)
        
        st.markdown("---")
        st.markdown("### 📚 什么是MCP？")
        st.markdown("""
        **Model Context Protocol (MCP)** 是一个开放协议，用于标准化AI模型与外部工具和数据的集成。
        
        **优势**：
        - 🔄 标准化工具调用接口
        - 🔌 即插即用的工具生态
        - 🛡️ 安全的权限控制
        - 📊 统一的错误处理
        
        **应用场景**：
        - AI助手调用外部API
        - 自动化工具编排
        - 多模型协作
        """)


if __name__ == "__main__":
    main()
