import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ================= 1. 版面與防遮擋 CSS 設定 =================
st.set_page_config(page_title="Lin Yun-Ju 戰術情蒐", layout="centered", initial_sidebar_state="collapsed")

# 🟢 修正：增加 padding-top (4rem) 防止頂部工具列擋住標題，並強制展開面板為白底黑字
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    
    .block-container { padding-top: 4rem; padding-bottom: 2rem; padding-left: 0.5rem; padding-right: 0.5rem; }
    h1 { font-size: 1.6rem !important; text-align: center; color: #1e293b; font-weight: 900; margin-bottom: 0.5rem; }
    
    .kpi-container { display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px; }
    .kpi-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .kpi-card { background: #1e293b; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #334155;}
    .kpi-card.highlight { background: linear-gradient(135deg, #0f172a, #1e3a8a); border: 1px solid #3b82f6; }
    .kpi-title { font-size: 0.8rem; color: #94a3b8; font-weight: 700; }
    .kpi-value { font-size: 1.3rem; font-weight: 900; margin-top: 5px; color: #38bdf8; }
    .kpi-value.killer { color: #facc15; font-size: 1.6rem; }
    
    button[data-baseweb="tab"] p { color: #64748b !important; font-weight: 700 !important; font-size: 14px !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #2563eb !important; font-weight: 900 !important; }
    
    /* 🟢 強制白底黑字，確保展開面板絕對清晰 */
    div[data-testid="stExpander"] { background-color: #f8fafc !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important; }
    div[data-testid="stExpander"] p, div[data-testid="stExpander"] li { color: #0f172a !important; font-size: 14.5px !important; line-height: 1.6 !important; font-weight: 500 !important; }
    div[data-testid="stExpander"] strong { color: #dc2626 !important; font-weight: 900 !important;}
    </style>
""", unsafe_allow_html=True)

# ================= 2. 數據引擎與翻譯 =================
@st.cache_data(ttl=600)
def load_scout_data():
    df = pd.read_csv('Lin_data260426.csv')
    if df['x'].max() > 1000: df['x'], df['y'] = df['x'] / 1000, df['y'] / 1000
    def parse_time(t_str):
        try:
            p = str(t_str).split(':')
            return int(p[1])*60 + int(p[2]) + int(p[3])/100 if len(p)==4 else 0.0
        except: return 0.0
    df['time_sec'] = df['time'].apply(parse_time)
    if 'rally_id' not in df.columns: df['rally_id'] = 1
    df['tempo_sec'] = df.groupby('rally_id')['time_sec'].diff().abs()
    return df

df = load_scout_data()
lin_base = df[df['player'] == 'Lin_Yun_Ju']
all_opps = sorted(list(lin_base['opponent'].dropna().unique()))
all_matches = sorted(list(lin_base['match'].dropna().unique()))
all_games = sorted(list(lin_base['games'].dropna().unique()))

skill_map = {'side-spin drive': '反手擰拉', 'drive': '相持', 'serve': '發球', 'push': '劈長/擺短', 'block': '防守借力', 'filp': '挑打', 'chop': '削球'}

st.title("🛡️ 林昀儒戰術情蒐報告")
st.title("114-2 運動大數據與視覺化分析專題研究/羅主文")
# ================= 3. 側邊欄過濾 =================
st.sidebar.header("🎛️ 動態情蒐過濾")
if 'scout_mode' not in st.session_state: st.session_state.scout_mode = 'all'

if st.session_state.scout_mode == 'all':
    if st.sidebar.button("🔄 啟用自定義多選"): st.session_state.scout_mode = 'custom'; st.rerun()
else:
    if st.sidebar.button("🌐 一鍵全選大數據"): st.session_state.scout_mode = 'all'; st.rerun()

if st.session_state.scout_mode == 'all':
    selected_opps = st.sidebar.multiselect("🎯 對手", all_opps, default=all_opps)
    selected_matches = st.sidebar.multiselect("🏆 賽事", all_matches, default=all_matches)
    selected_games = st.sidebar.multiselect("⏱️ 局數", all_games, default=all_games)
else:
    selected_opps = st.sidebar.multiselect("🎯 對手", all_opps, default=[all_opps[0]] if all_opps else [])
    selected_matches = st.sidebar.multiselect("🏆 賽事", all_matches, default=all_matches)
    selected_games = st.sidebar.multiselect("⏱️ 局數", all_games, default=all_games)

valid_rallies = df[(df['player'] == 'Lin_Yun_Ju') & (df['opponent'].isin(selected_opps)) & (df['match'].isin(selected_matches)) & (df['games'].isin(selected_games))]['rally_id'].unique()
match_data = df[df['rally_id'].isin(valid_rallies)].copy()
match_data['skill_zh'] = match_data['skill'].map(skill_map).fillna(match_data['skill'])

scout_df = match_data[match_data['player'] == 'Lin_Yun_Ju'].copy()
won_df = scout_df[scout_df['results'] == 'won'].copy()
opp_won_df = match_data[(match_data['player'] != 'Lin_Yun_Ju') & (match_data['results'] == 'won')].copy()

# ================= 4. 林昀儒專屬殺招 KPI =================
total_decided = len(won_df) + len(opp_won_df)
win_rate = (len(won_df) / total_decided * 100) if total_decided > 0 else 0

side_won_count = len(won_df[won_df['skill'] == 'side-spin drive'])
side_total_count = len(scout_df[scout_df['skill'] == 'side-spin drive'])
side_win_rate = (side_won_count / side_total_count * 100) if side_total_count > 0 else 0

st.markdown(f"""
    <div class='kpi-container'>
        <div class='kpi-card highlight'>
            <div class='kpi-title'>⚔️ 昀儒最強殺招</div>
            <div class='kpi-value killer'>反手擰拉</div>
            <div style='color:#cbd5e1; font-size:0.95rem; margin-top:12px; line-height:1.6;'>
                本局得分: <b style='color:#10b981;'>{side_won_count} 分</b><br>
                該技術實戰勝率: <b style='color:#10b981;'>{side_win_rate:.1f}%</b>
            </div>
        </div>
        <div class='kpi-row'>
            <div class='kpi-card'><div class='kpi-title'>當前戰局勝率</div><div class='kpi-value' style='color:{"#10b981" if win_rate>=50 else "#fb7185"};'>{win_rate:.1f}%</div></div>
            <div class='kpi-card'><div class='kpi-title'>分析樣本數</div><div class='kpi-value' style='color:#f8fafc;'>{len(scout_df)} 球</div></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ================= 5. 圖表分頁 =================
tab1, tab2, tab3 = st.tabs(["🎯 戰術解剖", "⚡ 節奏流速", "🏓 空間落點"])

# ----------------- TAB 1: 戰術解剖 (旭日/螺旋圖) -----------------
with tab1:
    if not won_df.empty and 'stroke' in won_df.columns:
        tact_df = won_df[won_df['stroke'].isin([2, 3, 4, 5])].groupby(['stroke', 'style', 'skill_zh']).size().reset_index(name='次數')
        tact_df['stroke_name'] = "第 " + tact_df['stroke'].astype(str) + " 板"
        tact_df['style_zh'] = tact_df['style'].map({'backhand':'反手', 'forehand':'正手'})
        
        fig_sun = px.sunburst(
            tact_df, path=['stroke_name', 'style_zh', 'skill_zh'], values='次數',
            color='stroke_name', color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sun.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
        fig_sun.update_traces(textinfo="label+percent parent", insidetextfont=dict(size=14, weight='bold'))
        st.plotly_chart(fig_sun, use_container_width=True)
        
        best_stroke = tact_df.groupby('stroke_name')['次數'].sum().idxmax()
        st.caption("第一板是發球\第二板是接發球\第三板為發球搶攻")
        with st.expander("🗣️ 教練動態戰術解讀（點此展開）", expanded=False):
            st.markdown(f"""
            **✅ 戰術決策樹判讀（點擊圓環可放大）：**
            * 📊 **數據顯示：** 內圈代表板數，外圈代表得分技術。您目前在 **「{best_stroke}」** 拿下了最多的分數！
            * 🎯 **教練建議：** 既然 **{best_stroke}** 是絕對優勢，請**刻意製造能過渡到該板數的落點**。若第2板優勢大，接發球請果斷擰拉；若第5板優勢大，前三板請耐心控短，主動拖入相持！
            """)
    else:
        st.info("💡 數據不足以繪製板數分佈。")

# ----------------- TAB 2: 戰術流速 -----------------
with tab2:
    v_tempo = match_data[match_data['tempo_sec'].between(0.2, 1.2)].copy()
    if not v_tempo.empty:
        v_tempo['results_zh'] = v_tempo['results'].map({'won': '得分', 'lost': '失誤', 'continue': '相持'})
        v_tempo['style_zh'] = v_tempo['style'].map({'backhand': '反手', 'forehand': '正手'})
        
        won_tempo = v_tempo[v_tempo['results'] == 'won']['tempo_sec'].median()
        lost_tempo = v_tempo[v_tempo['results'] == 'lost']['tempo_sec'].median()
        
        fig_tempo = px.box(
            v_tempo, x="tempo_sec", y="results_zh", color="style_zh",
            color_discrete_map={'反手': '#3b82f6', '正手': '#ef4444'}
        )
        fig_tempo.update_layout(
            height=300, margin=dict(l=10, r=10, t=10, b=60), 
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, title=""),
            xaxis=dict(title='⏱️ 擊球間隔秒數 (越靠左邊代表球速越快)')
        )
        fig_tempo.update_yaxes(title="")
        st.plotly_chart(fig_tempo, use_container_width=True)
        
        with st.expander("🗣️ 教練動態節奏解讀（點此展開）", expanded=False):
            st.markdown(f"""
            **✅ 擊球流速與戰鬥節奏：**
            * ⚡ **您的黃金快攻區：** 得分球的平均擊球間隔為 **{won_tempo:.2f} 秒**。
            * ⚠️ **您的失誤危險區：** 當擊球間隔被拖慢至0.65秒附近時，失誤率急遽攀升。
            * 🎯 **教練建議：** 記住 **{won_tempo:.2f} 秒** 的肌肉反應。如果對手把球速拖慢（速度條往右側延伸），請**千萬不要跟著退台**，立刻迎前借力，把球速強行帶回你的快攻甜區！
            """)

# ----------------- TAB 3: 空間落點 -----------------
with tab3:
    sub1, sub2 = st.tabs(["🎯 昀儒得分落點", "🚨 對手破防弱點"])
    
    x_min, x_max, y_min, y_max, y_net, x_mid = 100, 252, 100, 374, 237, 176
    
    def draw_premium_table(fig):
        # 🟢 修復核心：加上 layer="below" 保證桌子墊在落點球的「下層」，絕對不擋球！
        fig.add_shape(type="rect", x0=x_min, y0=y_min, x1=x_max, y1=y_max, 
                      line=dict(color="#ffffff", width=2), fillcolor="#1e3a8a", opacity=1.0, layer="below")
        fig.add_shape(type="line", x0=x_min-5, y0=y_net, x1=x_max+5, y1=y_net, 
                      line=dict(color="#f8fafc", width=3), layer="below")
        fig.add_shape(type="line", x0=x_mid, y0=y_min, x1=x_mid, y1=y_max, 
                      line=dict(color="#f8fafc", width=1, dash="dot"), layer="below")
        
        # 點的能見度設定
        fig.update_traces(marker=dict(size=12, opacity=1.0, line=dict(width=1.5, color='#ffffff')))
        
        # 畫布範圍擴大，容納大角度落點
        fig.update_layout(
            width=320, height=450, margin=dict(l=0, r=0, t=10, b=60), 
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False, range=[60, 292]), 
            yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[60, 414]),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, title="", font=dict(size=13, weight="bold"))
        )
        return fig

    # [1] 林昀儒得分點
    with sub1:
        if not won_df.empty:
            fig1 = px.scatter(won_df, x="x", y="y", color="skill_zh", color_discrete_sequence=px.colors.qualitative.Set1)
            st.plotly_chart(draw_premium_table(fig1), use_container_width=False)
            with st.expander("🗣️ 教練落點解讀（點此展開）", expanded=False):
                st.markdown("""
                **✅ 幾何壓迫分析：**
                * **深遠底線：** 點位逼近底線代表您的球具備極佳的頂人壓迫力。
                * **大角度邊線：** 落在兩側代表您成功調動對手，下一局請大膽複製這些空間落點！
                """)
        else: st.warning("無得分落點數據")

    # [2] 對手破防點
    with sub2:
        if not opp_won_df.empty:
            fig3 = px.scatter(opp_won_df, x="x", y="y", color="skill_zh", color_discrete_sequence=['#facc15', '#f87171', '#38bdf8'])
            st.plotly_chart(draw_premium_table(fig3), use_container_width=False)
            
            top_s = opp_won_df['skill_zh'].value_counts().head(2)
            st.error("🚨 對手最強殺招預警")
            for r, (s, c) in enumerate(top_s.items(), 1):
                st.markdown(f"> **Top {r}：** 對手使用 `{s}` 成功破防 **{c}** 次")
                
            with st.expander("🗣️ 教練防禦解讀（點此展開）", expanded=False):
                st.markdown("""
                **🚨 破防幾何學與防禦預警：**
                * 這些是**對手打穿你的致命落點**。如果點位落在您的**正手大位**，代表您在反手發力（如擰拉）後的「重心還原」太慢，被對手快撕直線抓到空檔。
                * **教練建議：** 下一板擊球後，腳步必須立刻啟動微調，護住這些亮起警戒燈的區域！
                """)
        else: st.success("目前局勢未偵測到對手得分，防守極其嚴密！")
