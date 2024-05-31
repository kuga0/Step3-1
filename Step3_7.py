import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import streamlit_authenticator as stauth
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from openai import OpenAI

# データベースのパス
db_path = 'user_data.db'

# データベースの初期化
def initialize_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            gender TEXT,
            age INTEGER,
            income INTEGER,
            spouse TEXT,
            children INTEGER,
            hobby TEXT,
            motto TEXT,
            user_values TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ユーザーデータベースに接続してユーザーを作成
def create_user(username, password, gender, age, income, spouse, children, hobby, motto, user_values):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # パスワードをハッシュ化
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # ユーザーデータを挿入
    c.execute('''
        INSERT INTO users (username, password, gender, age, income, spouse, children, hobby, motto, user_values)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, hashed_password, gender, age, income, spouse, children, hobby, motto, user_values))
    
    conn.commit()
    conn.close()

# データベースから全てのユーザー情報を取得
def get_all_users():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT username, password FROM users")
    users = c.fetchall()
    conn.close()
    return users

# データベースから特定のユーザー情報を取得
def get_user_info(username):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user_info = c.fetchone()
    conn.close()
    return user_info

# データベースの初期化を実行
initialize_db()

# ページの選択
page = st.sidebar.selectbox("ページを選択", ["アカウント登録", "メインページ"])

if page == "アカウント登録":
    st.title("アカウント登録")

    username = st.text_input("ユーザーネーム")
    password = st.text_input("パスワード", type="password")
    gender = st.selectbox("性別", ["男性", "女性", "その他"])
    age = st.number_input("年齢", min_value=0, max_value=120, step=1)
    income = st.number_input("年収（万円）", min_value=0, step=1)
    spouse = st.selectbox("配偶者の有無", ["有", "無"])
    children = st.number_input("子供の数", min_value=0, step=1)
    hobby = st.text_input("趣味")
    motto = st.text_input("座右の銘")
    user_values = st.text_input("価値観")

    if st.button("登録"):
        if username and password:
            create_user(username, password, gender, age, income, spouse, children, hobby, motto, user_values)
            st.success("アカウントが登録されました")
        else:
            st.error("ユーザーネームとパスワードを入力してください")

elif page == "メインページ":
    # データベースから全ユーザー情報を取得し、認証情報を設定
    all_users = get_all_users()
    credentials = {"usernames": {}}
    for user in all_users:
        username, password = user
        credentials["usernames"][username] = {"name": username, "password": password}

    cookie = {
        "name": "some_cookie_name",
        "key": "some_signature_key",
        "expiry_days": 30
    }

    authenticator = stauth.Authenticate(credentials, cookie["name"], cookie["key"], cookie["expiry_days"])

    # サイドバーにログイン情報
    with st.sidebar:
        name, authentication_status, username = authenticator.login("main", fields=["ユーザー名", "パスワード"])

    if authentication_status:
        authenticator.logout("ログアウト", "sidebar")
        
        # メインのタイトル
        st.title(f"{name}様への物件提案")

        # データベースから特定のユーザー情報を取得
        def get_user_info(username):
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                #st.write(f"デバッグ: データベースに接続しました。ユーザー名: {username}")
                #c.execute("SELECT * FROM users WHERE username=?", (username,))
                user_info = c.fetchone()
                conn.close()
                #st.write(f"デバッグ: SQLクエリを実行しました。結果: {user_info}")
                return user_info
            except Exception as e:
                #st.write(f"デバッグ: データベースからのユーザー情報取得に失敗しました。エラー: {e}")
                return None

        # ログインユーザーの情報をデータベースから取得
        user_info = get_user_info(username)
        if user_info:
            gender = user_info[2]
            age = user_info[3]
            income = user_info[4]
            spouse = user_info[5]
            children = user_info[6]
            hobby = user_info[7]
            motto = user_info[8]
            user_values = user_info[9]
        else:
            st.error("ユーザー情報の取得に失敗しました。")

        # ユーザー情報の入力
        st.subheader("ユーザー情報入力")
        gender = st.selectbox("性別", ["男性", "女性", "その他"], index=["男性", "女性", "その他"].index(gender))
        age = st.number_input("年齢", min_value=0, max_value=120, step=1, value=age)
        income = st.number_input("年収（万円）", min_value=0, step=1, value=income)
        spouse = st.selectbox("配偶者の有無", ["有", "無"], index=["有", "無"].index(spouse))
        children = st.number_input("子供の数", min_value=0, step=1, value=children)
        hobby = st.text_input("趣味", value=hobby)
        motto = st.text_input("座右の銘", value=motto)
        user_values = st.text_input("価値観", value=user_values)

        # データベースのパス
        real_estate_db_path = 'real_estate.db'
        
        # SQLiteデータベースに接続
        try:
            conn = sqlite3.connect(real_estate_db_path)
            #st.write("データベースに接続しました。")
        except Exception as e:
            st.write(f"データベース接続エラー: {e}")

        # SQLクエリでデータを取得
        try:
            query = "SELECT 名称, カテゴリ, アドレス, アクセス, 築年数, 構造, 階数, 家賃, 管理費, 敷金, 礼金, 間取り, 面積, 物件詳細URL, 物件画像URL, 区 FROM properties"
            df = pd.read_sql_query(query, conn)
            #st.write("データの取得に成功しました。")
        except Exception as e:
            st.write(f"データ取得エラー: {e}")

        # カラム名の余分な空白や特殊文字を削除
        df.columns = df.columns.str.strip().str.replace('\u3000', '')

        # 家賃のデータを数値に変換
        df['家賃'] = df['家賃'].str.replace('万円', '').astype(float)

        # ユニークな区のリストを取得
        unique_districts = df['区'].dropna().unique()

        # 間取りの選択肢を取得
        unique_layouts = df['間取り'].dropna().unique()

        # サイドバーに検索条件を設定
        with st.sidebar:
            st.subheader("検索条件")
            
            # エリアの選択
            areas = st.multiselect("エリア", unique_districts, default=[unique_districts[0]])
            
            # 家賃の範囲入力
            rent_input = st.number_input("家賃 (万円くらい)", min_value=1, max_value=100, step=1, value=12)
            
            # 間取りの選択
            layouts = st.multiselect("間取り", unique_layouts, default=[unique_layouts[0]])
            
            # 検索ボタン
            search = st.button("検索")

        def search_properties(layouts, yachin, areas):
            # ±20％の範囲を計算
            lower_bound = yachin * 0.8
            upper_bound = yachin * 1.2
            
            # 指定されたエリア、間取り、家賃範囲の物件をフィルタリング
            result = df[(df['区'].isin(areas)) & (df['間取り'].isin(layouts)) & (df['家賃'] >= lower_bound) & (df['家賃'] <= upper_bound)]
            
            if result.empty:
                return "条件に合う物件は見つかりませんでした。"
            else:
                return result[['名称', 'カテゴリ', 'アドレス', 'アクセス', '築年数', '構造', '階数', '家賃', '管理費', '敷金', '礼金', '間取り', '面積', '物件詳細URL', '物件画像URL']]

        if search:
            # 検索結果の表示
            result = search_properties(layouts, rent_input, areas)
            
            if isinstance(result, str):
                st.write(result)
            else:
                # ランダムに1件抽出
                selected_property = result.sample(n=1).iloc[0]

                # 画像とセリフを追加
                st.subheader("Professional Recommendation")
                st.image("Character.jpg", width=200)
                st.write(f"不動産のプロである私が{name}様に最適な物件を紹介します！")

                client = OpenAI()

                # メッセージを送信
                prompt = f"私の名前は{name}、性別は{gender}で、年齢は{age}、年収は{income}万円、配偶者は{spouse}、子供の数は{children}、趣味は{hobby}、座右の銘は{motto}、価値観は{user_values}です。{selected_property['名称']}という物件を紹介してください。なお間取りは{selected_property['間取り']}で、家賃は{selected_property['家賃']}万円で、アクセスは{selected_property['アクセス']}で、築年数は{selected_property['築年数']}です。その他詳細として({selected_property['物件詳細URL']})をリンクとして最後に提示してください。。"
                
                # ChatGPTの応答を取得して表示
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは不動産のプロフェッショナルです。私に指定した物件を熱烈に、しかし短い文章ですすめてください。私の情報と物件情報をできるだけ多く絡めるようにし、特に物件名称と間取り、家賃、アクセスは必ず文章に含めてください。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                st.write(response.choices[0].message.content)

                # 地図の作成
                geolocator = Nominatim(user_agent="real_estate_app")
                location = geolocator.geocode(selected_property['アドレス'])
                if location:
                    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=15)
                    popup_content = f"""
                    <b>{selected_property['名称']}</b><br>
                    家賃: {selected_property['家賃']}万円<br>
                    間取り: {selected_property['間取り']}<br>
                    アクセス: {selected_property['アクセス']}<br>
                    <img src="{selected_property['物件画像URL']}" alt="物件画像" width="150"><br>
                    <a href='{selected_property['物件詳細URL']}' target='_blank'>詳細</a>
                    """
                    folium.Marker(location=[location.latitude, location.longitude], popup=popup_content).add_to(m)
                    folium_static(m)
                else:
                    st.write("選択した物件の位置情報が取得できませんでした。")
    elif authentication_status == False:
        st.error("ユーザー名またはパスワードが正しくありません")
    elif authentication_status == None:
        st.warning("認証情報を入力してください")

