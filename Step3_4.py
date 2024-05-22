import streamlit as st
import pandas as pd
import sqlite3
import streamlit_authenticator as stauth
import bcrypt
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
import random

# ユーザー認証情報の設定（簡単なものに変更）
names = ["User1", "User2"]
usernames = ["user1", "user2"]
passwords = ["test1", "test2"]

# パスワードをハッシュ化
hashed_passwords = [bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') for password in passwords]

# Streamlit-Authenticatorの設定
credentials = {
    "usernames": {
        usernames[0]: {
            "name": names[0],
            "password": hashed_passwords[0]
        },
        usernames[1]: {
            "name": names[1],
            "password": hashed_passwords[1]
        }
    }
}

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
    # メインのタイトル
    st.title("不動産検索")

    # ユーザー情報の入力
    st.subheader("ユーザー情報入力")
    gender = st.selectbox("性別", ["男性", "女性", "その他"], index=0)
    age = st.number_input("年齢", min_value=0, max_value=120, step=1, value=28)
    income = st.number_input("年収（万円）", min_value=0, step=1, value=1000)
    spouse = st.selectbox("配偶者の有無", ["有", "無"], index=0)
    children = st.number_input("子供の数", min_value=0, step=1, value=0)
    hobby = st.text_input("趣味", value="フットサル")
    motto = st.text_input("座右の銘", value="PKを外すことができるのはPKを蹴る勇気を持ったものだけだ。")

    # データベースのパス
    db_path = 'Step3-test.db'
    
    # SQLiteデータベースに接続
    try:
        conn = sqlite3.connect(db_path)
        st.write("データベースに接続しました。")
    except Exception as e:
        st.write(f"データベース接続エラー: {e}")

    # SQLクエリでデータを取得
    try:
        query = "SELECT * FROM properties"
        df = pd.read_sql_query(query, conn)
        st.write("データの取得に成功しました。")
    except Exception as e:
        st.write(f"データ取得エラー: {e}")

    # カラム名の余分な空白や特殊文字を削除
    df.columns = df.columns.str.strip().str.replace('\u3000', '')

    # 家賃のデータを数値に変換
    df['家賃'] = df['家賃'].str.replace('万円', '').astype(float)

    # アドレスから区の部分を抽出する関数
    def extract_district(address):
        import re
        match = re.search(r'東京都(.+?区)', address)
        return match.group(1) if match else None

    # アドレスから区の部分を抽出
    df['区'] = df['アドレス'].apply(extract_district)

    # 間取りの選択肢を取得
    unique_layouts = df['間取り'].dropna().unique()

    # サイドバーに検索条件を設定
    with st.sidebar:
        st.subheader("検索条件")
        
        # エリアの選択
        area = st.radio("エリア", ('新宿区', '渋谷区', '中央区'))
        
        # 家賃の範囲入力
        rent_input = st.number_input("家賃 (万円くらい)", min_value=1, max_value=100, step=1, value=12)
        
        # 間取りの選択
        layout = st.selectbox("間取り", unique_layouts)
        
        # 検索ボタン
        search = st.button("検索")

    def search_properties(madori, yachin, area):
        # ±10％の範囲を計算
        lower_bound = yachin * 0.8
        upper_bound = yachin * 1.2
        
        # 指定されたエリア、間取り、家賃範囲の物件をフィルタリング
        result = df[(df['区'] == area) & (df['間取り'] == madori) & (df['家賃'] >= lower_bound) & (df['家賃'] <= upper_bound)]
        
        if result.empty:
            return "条件に合う物件は見つかりませんでした。"
        else:
            return result[['名称', 'カテゴリ', 'アドレス', 'アクセス', '築年数', '構造', '階数', '家賃', '管理費', '敷金', '礼金', '間取り', '面積', '物件詳細URL']]


    if search:
        # 検索結果の表示
        result = search_properties(layout, rent_input, area)
        
        if isinstance(result, str):
            st.write(result)
        else:
            #st.write(result)

            # ランダムに1件抽出
            selected_property = result.sample(n=1).iloc[0]

            # 画像とセリフを追加
            st.subheader("おすすめ物件")
            st.image("Character.jpg", width=200)
            st.write("不動産のプロである私があなたに最適な物件を紹介します！")

            st.write(f"あなたの性別は{gender}で、年齢は{age}、年収は{income}万円、配偶者は{spouse}、子供の数は{children}、趣味は{hobby}とのことですね。")
            st.write(f"そんなあなたには{selected_property['名称']}という物件を紹介します。間取りは{selected_property['間取り']}で、家賃は{selected_property['家賃']}万円です。{selected_property['築年数']}です。その他詳細は [こちら]({selected_property['物件詳細URL']})をご参照ください。あなたの座右の銘『{motto}』に照らし合わせてもぴったりな物件です。")


            # Geolocatorオブジェクトの作成
            geolocator = Nominatim(user_agent="real_estate_app")

            # 住所から緯度・経度を取得する関数
            def get_location(address):
                location = geolocator.geocode(address)
                if location:
                    return (location.latitude, location.longitude)
                else:
                    return None

            # 地図の作成
            m = folium.Map(location=[35.6895, 139.6917], zoom_start=12)  # 東京の中心に設定

            # 検索結果の住所にピンを刺す
            location = get_location(selected_property['アドレス'])
            if location:
                folium.Marker(location, popup=f"{selected_property['名称']}<br><a href='{selected_property['物件詳細URL']}' target='_blank'>詳細</a>").add_to(m)

            # 地図の表示
            folium_static(m)

            # 「違う物件を見たい」ボタンの追加
            if st.button("違う物件を見たい"):
                selected_property = result.sample(n=1).iloc[0]
                st.write(f"新しいおすすめ物件: {selected_property['名称']}、間取り: {selected_property['間取り']}、家賃: {selected_property['家賃']}万円")
                st.write(f"詳細は [こちら]({selected_property['物件詳細URL']})")
                
                # 再度地図を更新
                location = get_location(selected_property['アドレス'])
                if location:
                    folium.Marker(location, popup=f"{selected_property['名称']}<br><a href='{selected_property['物件詳細URL']}' target='_blank'>詳細</a>").add_to(m)
                folium_static(m)


elif authentication_status == False:
    st.error("ユーザー名またはパスワードが正しくありません")
elif authentication_status == None:
    st.warning("認証情報を入力してください")

