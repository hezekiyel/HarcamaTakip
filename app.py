import streamlit as st
import sqlite3
import pandas as pd
import hashlib

# --- 1. FONKSİYONLAR ---
def sifre_isle(sifre):
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
        return True
    except: return False
    finally: conn.close()

def giris_kontrol(username, password):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    hashed_pw = sifre_isle(password)
    c.execute("SELECT * FROM kullanicilar WHERE username=? AND password=?", (username, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user

# --- 2. SAYFA AYARLARI ---
st.set_page_config(page_title="Finans Takip", layout="wide")
tablo_olustur()

# Oturum Durumu Başlatma
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# --- 3. GİRİŞ VE KAYIT EKRANI ---
if not st.session_state['logged_in']:
    st.title("🔐 Finans Takip Sistemi")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

    with tab2:
        with st.form("kayit_form"):
            new_u = st.text_input("Kullanıcı Adı")
            new_n = st.text_input("İsim Soyisim")
            new_p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Kaydol"):
                if new_u and new_p:
                    if kullanici_ekle(new_u, new_n, new_p):
                        st.success("Kayıt başarılı! Şimdi giriş yapabilirsin.")
                    else: st.error("Bu kullanıcı adı alınmış.")
                else: st.warning("Alanları doldur kanka.")

    with tab1:
        with st.form("giris_form"):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş"):
                user = giris_kontrol(u, p)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user[0]
                    st.session_state['display_name'] = user[1]
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre yanlış.")

# --- 4. ANA UYGULAMA (GİRİŞ YAPILDIYSA) ---
else:
    st.sidebar.success(f"Hoş geldin, {st.session_state['display_name']}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"📊 {st.session_state['display_name']} - Harcama Paneli")
    st.info("Sistemin tıkır tıkır çalışıyor. Buraya harcama kodlarını ekleyebilirsin!")
    
    # Buraya daha önce yazdığımız harcama ekleme ve listeleme kodlarını koyabiliriz.
    # Ama önce bu girişin çalıştığını bir görelim!
