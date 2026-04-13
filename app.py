import streamlit as st
import sqlite3
import pandas as pd
import streamlit_authenticator as stauth
import hashlib

# 1. VERİTABANI
def tablo_olustur():
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS harcamalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, miktar REAL, kategori TEXT, tarih DATE, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def tabloyu_temizle():
    # Eğer yapı değişirse hata almamak için
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    conn.commit()
    conn.close()

def kullanici_ekle(username, name, password):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(str.encode(password)).hexdigest()
    try:
        c.execute("INSERT INTO kullanicilar VALUES (?,?,?)", (username, name, hashed_pw))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

# 2. AYARLAR
st.set_page_config(page_title="Finans Takip", layout="wide")
tablo_olustur()

# Kullanıcı yükleme
conn = sqlite3.connect('finans.db')
users_df = pd.read_sql_query("SELECT * FROM kullanicilar", conn)
conn.close()

credentials = {"usernames": {}}
for _, row in users_df.iterrows():
    credentials["usernames"][row['username']] = {"name": row['name'], "password": row['password']}

authenticator = stauth.Authenticate(credentials, "cerez_finans", "anahtar_123", cookie_expiry_days=0)

# 3. ARAYÜZ
tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

with tab2:
    with st.form("kayit"):
        u = st.text_input("Kullanıcı Adı")
        n = st.text_input("İsim")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Kaydol"):
            if u and n and p:
                if kullanici_ekle(u, n, p): st.success("Tamamdır, giriş yapabilirsin!")
                else: st.error("Kullanıcı adı kullanımda.")

with tab1:
    authenticator.login(location='main')
    if st.session_state["authentication_status"]:
        st.write(f"### Hoş geldin {st.session_state['name']}!")
        authenticator.logout("Çıkış", "sidebar")
        st.info("Harcama modülü aktif edildi. Veri girebilirsin.")
    elif st.session_state["authentication_status"] is False:
        st.error("Hatalı giriş.")
