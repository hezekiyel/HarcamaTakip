import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth

# --- 1. VERİTABANI FONKSİYONLARI ---
def tablo_olustur():
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    # Harcamalar tablosuna 'kullanici' kolonu ekledik
    c.execute('''CREATE TABLE IF NOT EXISTS harcamalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  kullanici TEXT,
                  miktar REAL, 
                  kategori TEXT, 
                  tarih DATE, 
                  aciklama TEXT)''')
    # Kullanıcılar tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def kullanici_ekle(username, name, password):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    # Şifreyi hashleyerek kaydediyoruz (Güvenlik!)
    hashed_pw = stauth.Hasher([password]).generate()[0]
    try:
        c.execute("INSERT INTO kullanicilar VALUES (?,?,?)", (username, name, hashed_pw))
        conn.commit()
    except:
        return False
    conn.close()
    return True

def harcama_ekle(kullanici, miktar, kategori, tarih, aciklama):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute("INSERT INTO harcamalar (kullanici, miktar, kategori, tarih, aciklama) VALUES (?,?,?,?,?)",
              (kullanici, miktar, kategori, tarih, aciklama))
    conn.commit()
    conn.close()

def verileri_getir(kullanici):
    conn = sqlite3.connect('finans.db')
    # SADECE giriş yapan kullanıcının verilerini getiriyoruz
    query = f"SELECT * FROM harcamalar WHERE kullanici = '{kullanici}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['tarih'] = pd.to_datetime(df['tarih'])
    return df

# --- 2. AUTHENTICATION AYARLARI ---
st.set_page_config(page_title="Finans Portalı", layout="wide")
tablo_olustur()

# Veritabanındaki kullanıcıları auth sistemine yükle
conn = sqlite3.connect('finans.db')
users_df = pd.read_sql_query("SELECT * FROM kullanicilar", conn)
conn.close()

credentials = {"usernames": {}}
for _, row in users_df.iterrows():
    credentials["usernames"][row['username']] = {
        "name": row['name'],
        "password": row['password']
    }

authenticator = stauth.Authenticate(
    credentials,
    "finans_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# --- 3. ARAYÜZ MANTIĞI ---
tab1, tab2 = st.tabs(["Giriş Yap", "Yeni Kayıt"])

with tab2:
    st.subheader("📝 Kayıt Ol")
    new_user = st.text_input("Kullanıcı Adı")
    new_name = st.text_input("İsim Soyisim")
    new_pw = st.text_input("Şifre", type="password")
    if st.button("Kaydol"):
        if kullanici_ekle(new_user, new_name, new_pw):
            st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
        else:
            st.error("Bu kullanıcı adı zaten alınmış.")

with tab1:
    name, authentication_status, username = authenticator.login("Giriş", "main")

    if authentication_status:
        # GİRİŞ BAŞARILIYSA ANA UYGULAMA BURADA ÇALIŞIR
        st.sidebar.title(f"Hoş geldin, {name}")
        authenticator.logout("Çıkış Yap", "sidebar")
        
        # --- ANA UYGULAMA KODLARI ---
        st.title("📊 Kişisel Finans Panelim")
        
        with st.sidebar.form("ekle_form"):
            miktar = st.number_input("Miktar", min_value=0.0)
            kat = st.selectbox("Kategori", ["Mutfak", "Kira", "Eğlence", "Diğer"])
            tarih = st.date_input("Tarih")
            not_ = st.text_input("Not")
            if st.form_submit_button("Ekle"):
                harcama_ekle(username, miktar, kat, tarih, not_)
                st.rerun()

        df = verileri_getir(username)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Buraya önceki grafik kodlarını ekleyebilirsin
        else:
            st.info("Henüz harcamanız yok.")

    elif authentication_status == False:
        st.error("Kullanıcı adı veya şifre hatalı.")
    elif authentication_status == None:
        st.warning("Lütfen giriş yapın veya kayıt olun.")