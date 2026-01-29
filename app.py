import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# הגדרות דף
st.set_page_config(page_title="מחשבון מלצרים", layout="centered")

st.title("💰 מחשבון שכר וטיפים")

# יצירת בסיס נתונים בזיכרון (או קובץ CSV)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=[
        "תאריך", "יום", "התחלה", "סיום", "שעות", "מזומן", "אשראי", "השלמה", "סה\"כ"
    ])

# --- אזור הזנה ---
with st.expander("➕ הזנת משמרת חדשה", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("תאריך", datetime.now())
        start_time = st.text_input("שעת התחלה (HH:MM)", "17:00")
        end_time = st.text_input("שעת סיום (HH:MM)", "23:00")
    with col2:
        cash = st.number_input("טיפ מזומן (ש\"ח)", min_value=0.0, step=1.0)
        credit = st.number_input("טיפ אשראי (ש\"ח)", min_value=0.0, step=1.0)

    if st.button("שמור משמרת"):
        try:
            # חישוב שעות
            fmt = '%H:%M'
            t1 = datetime.strptime(start_time, fmt)
            t2 = datetime.strptime(end_time, fmt)
            if t2 < t1: t2 += timedelta(days=1)
            hours = (t2 - t1).total_seconds() / 3600
            
            # חישובים
            top_up = max(0, (hours * 36) - (cash + credit))
            total = cash + credit + top_up
            day_name = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][date.weekday()]
            
            # הוספה לטבלה
            new_row = {
                "תאריך": date.strftime("%d/%m/%Y"), "יום": day_name, 
                "התחלה": start_time, "סיום": end_time, "שעות": round(hours, 2),
                "מזומן": cash, "אשראי": credit, "השלמה": round(top_up, 2), "סה\"כ": round(total, 2)
            }
            st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([new_row])], ignore_index=True)
            st.success("המשמרת נשמרה בהצלחה!")
        except:
            st.error("בדוק את פורמט השעות (HH:MM)")

# --- תצוגת דוחות ---
if not st.session_state.db.empty:
    st.subheader("📋 דוח משמרות")
    st.dataframe(st.session_state.db, use_container_width=True)

    # סיכומים
    st.divider()
    col_a, col_b = st.columns(2)
    
    total_all = st.session_state.db["סה\"כ"].sum()
    total_hours = st.session_state.db["שעות"].sum()
    
    col_a.metric("סה\"כ הכנסה (כללי)", f"{total_all:,.2f} ש\"ח")
    col_b.metric("סה\"כ שעות עבודה", f"{total_hours:,.2f}")

    # סיכום חודשי
    st.subheader("📅 סיכום לפי חודשים")
    df = st.session_state.db.copy()
    df['חודש'] = df['תאריך'].apply(lambda x: x[3:]) # חילוץ MM/YYYY
    monthly = df.groupby('חודש').agg({'שעות': 'sum', 'סה\"כ': 'sum'})
    st.table(monthly)

if st.sidebar.button("🗑️ איפוס כל הנתונים"):
    st.session_state.db = pd.DataFrame(columns=st.session_state.db.columns)
    st.rerun()
