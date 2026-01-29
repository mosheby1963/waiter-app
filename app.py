import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# הגדרת כותרת ועיצוב הדף
st.set_page_config(page_title="מחשבון מלצרים - שמירה לענן", layout="centered")

# חיבור לגוגל שיטס (משתמש ב-Secrets שהגדרת)
conn = st.connection("gsheets", type=GSheetsConnection)

# פונקציה לקריאת הנתונים מהגיליון
def get_data():
    return conn.read(ttl="0") # ttl=0 מבטיח שהנתונים יתעדכנו מייד

df = get_data()

st.title("💰 מחשבון שכר ושמירה לענן")

# תיבה להזנת משמרת חדשה
with st.expander("➕ הזנת משמרת חדשה", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("תאריך", datetime.now())
        start_time = st.text_input("התחלה (HH:MM)", "17:00")
        end_time = st.text_input("סיום (HH:MM)", "23:00")
    with col2:
        cash = st.number_input("מזומן", min_value=0.0, step=1.0)
        credit = st.number_input("אשראי", min_value=0.0, step=1.0)

    if st.button("💾 שמור משמרת"):
        try:
            # חישוב שעות
            fmt = '%H:%M'
            t1 = datetime.strptime(start_time, fmt)
            t2 = datetime.strptime(end_time, fmt)
            if t2 < t1: t2 += timedelta(days=1)
            hours = (t2 - t1).total_seconds() / 3600
            
            # חישוב השלמה וסה"כ (לפי 36 ש"ח לשעה)
            top_up = max(0, (hours * 36) - (cash + credit))
            total = cash + credit + top_up
            day_name = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][date.weekday()]

            # יצירת שורה חדשה
            new_row = {
                "תאריך": date.strftime("%d/%m/%Y"),
                "יום": day_name,
                "התחלה": start_time,
                "סיום": end_time,
                "שעות": round(hours, 2),
                "מזומן": cash,
                "אשראי": credit,
                "השלמה": round(top_up, 2),
                "סה\"כ": round(total, 2)
            }
            
            # הוספת השורה לטבלה הקיימת ושמירה בחזרה לגוגל
            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("✅ המשמרת נשמרה בהצלחה בגוגל שיטס!")
            st.rerun() # רענון הדף כדי להציג את הנתון החדש
            
        except Exception as e:
            st.error(f"שגיאה בחישוב או בשמירה: {e}")

# תצוגת ההיסטוריה מהענן
st.divider()
st.subheader("📋 היסטוריית משמרות (מהגליון שלך)")

if not df.empty:
    # הצגת הטבלה
    st.dataframe(df, use_container_width=True)
    
    # סיכומים מהירים
    total_earned = df["סה\"כ"].sum()
    total_hours = df["שעות"].sum()
    st.metric("סה\"כ רווח מצטבר", f"₪{total_earned:,.2f}")
    st.info(f"עבדת בסה\"כ {total_hours:,.2f} שעות בתקופה המוצגת.")
else:
    st.write("אין עדיין נתונים בגיליון. הזן משמרת ראשונה!")
