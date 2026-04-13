import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth

# --- 1. VERİTABANI FONKSİYONLARI ---
def tablo_olustur():
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS harcamalar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  kullanici TEXT,
                  miktar REAL, 
                  kategori TEXT, 
                  tarih DATE, 
                  aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT)''')
    conn.commit()
    conn.close()

def kullanici_ekle(username, name, password):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    # Şifreyi hashleyerek kaydediyoruz
    hashed_pw = stauth.Hasher([password]).generate()[0]
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

def harcama_sil(id):
    conn = sqlite3.connect('finans.db')
    c = conn.cursor()
    c.execute("DELETE FROM harcamalar WHERE id=?", (id,))
    conn.commit()
    conn.close()

def verileri_getir(kullanici):
    conn = sqlite3.connect('finans.db')
    query = f"SELECT * FROM harcamalar WHERE kullanici = '{kullanici}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if not df.empty:
        df['tarih'] = pd.to_datetime(df['tarih'])
        ay_map = {1:'Ocak', 2:'Şubat', 3:'Mart', 4:'Nisan', 5:'Mayıs', 6:'Haziran',
                  7:'Temmuz', 8:'Ağustos', 9:'Eylül', 10:'Ekim', 11:'Kasım', 12:'Aralık'}
        df['Ay_Adi'] = df['tarih'].dt.month.map(ay_map)
        df['Yil'] = df['tarih'].dt.year
    return df

# --- 2. BAŞLATMA VE AUTH AYARLARI ---
st.set_page_config(page_title="Pro Finans Portalı", layout="wide")
tablo_olustur()

# Kullanıcıları yükle
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
    "finans_takip_cerez",
    "anahtar_kelime",
    cookie_expiry_days=30
)

# --- 3. ARAYÜZ (TABS) ---
tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Yeni Kayıt"])

with tab2:
    st.subheader("Yeni Hesap Oluştur")
    with st.form("kayit_formu"):
        new_user = st.text_input("Kullanıcı Adı")
        new_name = st.text_input("İsim Soyisim")
        new_pw = st.text_input("Şifre", type="password")
        if st.form_submit_button("Kaydol"):
            if new_user and new_name and new_pw:
                if kullanici_ekle(new_user, new_name, new_pw):
                    st.success("Kayıt başarılı! Giriş sekmesine gidiniz.")
                else:
                    st.error("Bu kullanıcı adı alınmış veya bir hata oluştu.")
            else:
                st.warning("Lütfen tüm alanları doldurun.")

with tab1:
    # Hata aldığın kritik satırın düzeltilmiş hali:
    authenticator.login(location='main')

    if st.session_state["authentication_status"]:
        # GİRİŞ BAŞARILI
        username = st.session_state["username"]
        name = st.session_state["name"]
        
        st.sidebar.title(f"Hoş geldin, {name}")
        authenticator.logout("Çıkış Yap", "sidebar")
        
        st.title("💸 Kişisel Finans Panelim")
        
        # VERİ GİRİŞİ
        st.sidebar.header("➕ Harcama Ekle")
        with st.sidebar.form("ekle_form", clear_on_submit=True):
            miktar = st.number_input("Miktar (TL)", min_value=0.0)
            kat = st.selectbox("Kategori", ["Market", "Kira", "Eğlence", "Ulaşım", "Sağlık", "Eğitim", "Diğer"])
            tarih = st.date_input("Tarih")
            not_ = st.text_input("Not/Açıklama")
            if st.form_submit_button("Veritabanına İşle"):
                if miktar > 0:
                    harcama_ekle(username, miktar, kat, tarih, not_)
                    st.rerun()

        # RAPORLAMA
        df = verileri_getir(username)
        if not df.empty:
            st.subheader("📊 Harcama Özetiniz")
            st.metric("Toplam Harcama", f"{df['miktar'].sum():,.2f} TL")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📋 Son İşlemler")
                st.dataframe(df.sort_values(by='tarih', ascending=False)[['tarih', 'kategori', 'miktar', 'aciklama']], use_container_width=True)
            
            with c2:
                st.subheader("🍕 Kategori Dağılımı")
                kat_ozet = df.groupby("kategori")["miktar"].sum()
                fig, ax = plt.subplots()
                ax.pie(kat_ozet, labels=kat_ozet.index, autopct='%1.1f%%', startangle=140)
                st.pyplot(fig)

            # SİLME BÖLÜMÜ
            st.markdown("---")
            st.subheader("🗑️ Kayıt Sil")
            silinecek = st.selectbox("Silinecek harcamayı seçin:", options=df.index,
                                    format_func=lambda x: f"{df.loc[x,'tarih'].date()} - {df.loc[x,'kategori']} - {df.loc[x,'miktar']} TL")
            if st.button("Seçili Kaydı Sil", type="primary"):
                harcama_sil(df.loc[silinecek, 'id'])
                st.success("Silindi!")
                st.rerun()
        else:
            st.info("Henüz harcama kaydınız yok. Sol menüden ekleyebilirsiniz.")

    elif st.session_state["authentication_status"] is False:
        st.error("Kullanıcı adı veya şifre yanlış.")
    elif st.session_state["authentication_status"] is None:
        st.warning("Uygulamaya erişmek için giriş yapın.")