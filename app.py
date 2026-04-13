import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth
import hashlib

# --- 1. VERİTABANI VE ŞİFRELEME ---
def sifre_isle(sifre):
    # Standart SHA-256 şifreleme (Kütüphane güncellemelerinden etkilenmez)
    return hashlib.sha256(str.encode(sifre)).hexdigest()

def tablo_olustur():
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS harcamalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, miktar REAL, kategori TEXT, tarih DATE, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def kullanici_ekle(username, name, password):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    hashed_pw = sifre_isle(password)
    try:
        c.execute("INSERT INTO kullanicilar VALUES (?,?,?)", (username, name, hashed_pw))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def harcama_ekle(kullanici, miktar, kategori, tarih, aciklama):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute("INSERT INTO harcamalar (kullanici, miktar, kategori, tarih, aciklama) VALUES (?,?,?,?,?)",
              (kullanici, miktar, kategori, tarih, aciklama))
    conn.commit()
    conn.close()

def verileri_getir(kullanici):
    conn = sqlite3.connect('finans.db')
    df = pd.read_sql_query(f"SELECT * FROM harcamalar WHERE kullanici = '{kullanici}'", conn)
    conn.close()
    if not df.empty:
        df['tarih'] = pd.to_datetime(df['tarih'])
    return df

# --- 2. BAŞLATMA ---
st.set_page_config(page_title="Finans Portalı", layout="wide")
tablo_olustur()

# Kullanıcıları yükle
conn = sqlite3.connect('finans.db')
users_df = pd.read_sql_query("SELECT * FROM kullanicilar", conn)
conn.close()

credentials = {"usernames": {}}
for _, row in users_df.iterrows():
    credentials["usernames"][row['username']] = {"name": row['name'], "password": row['password']}

# Authenticator'ı başlat (Şifre kontrolünü manuel yapacağız)
authenticator = stauth.Authenticate(credentials, "finans_cerez", "key_123", cookie_expiry_days=30)

# --- 3. ARAYÜZ ---
tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Yeni Kayıt"])

with tab2:
    st.subheader("Yeni Kayıt")
    with st.form("kayit"):
        u = st.text_input("Kullanıcı Adı")
        n = st.text_input("İsim Soyisim")
        p = st.text_input("Şifre", type="password")
        if st.form_submit_button("Kaydol"):
            if u and n and p:
                if kullanici_ekle(u, n, p):
                    st.success("Kayıt başarılı! Giriş sekmesine geçiniz.")
                else: st.error("Hata! Kullanıcı adı alınmış olabilir.")

with tab1:
    # Giriş ekranı
    authenticator.login(location='main')

    if st.session_state["authentication_status"]:
        # Giriş başarılıysa ana ekranı göster
        st.sidebar.title(f"Hoş geldin, {st.session_state['name']}")
        authenticator.logout("Çıkış Yap", "sidebar")
        
        st.title("💸 Harcama Takip Paneli")
        
        # Harcama Ekleme
        with st.sidebar.form("ekle"):
            m = st.number_input("Miktar", min_value=0.0)
            k = st.selectbox("Kategori", ["Market", "Kira", "Eğlence", "Ulaşım", "Diğer"])
            t = st.date_input("Tarih")
            a = st.text_input("Açıklama")
            if st.form_submit_button("Ekle"):
                if m > 0:
                    harcama_ekle(st.session_state['username'], m, k, t, a)
                    st.rerun()

        # Raporlar
        df = verileri_getir(st.session_state['username'])
        if not df.empty:
            st.metric("Toplam Harcamanız", f"{df['miktar'].sum():,.2f} TL")
            st.dataframe(df.sort_values(by='tarih', ascending=False), use_container_width=True)
        else:
            st.info("Henüz harcama kaydı yok.")

    elif st.session_state["authentication_status"] is False:
        # Şifre kontrolü (Kendi hash yöntemimizle doğrulama)
        st.error("Kullanıcı adı veya şifre yanlış.")
