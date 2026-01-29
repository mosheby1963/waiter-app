import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="מחשבון שכר אישי", layout="centered")

# חיבור לגוגל שיטס
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="0")

df = get_data()

st.title("💰 מחשבון שכר ושמירה לענן")

# --- בחירת משתמש ---
st.subheader("👤 מי המלצר/ית?")
user = st.selectbox("בחר שם מהרשימה:", ["ליהיא בן יאיר", "משה בן יאיר"])

st.info(f"מחובר/ת בתור: **{user}**")

# --- הזנת משמרת חדשה ---
with st.expander(f"➕ הזנת משמרת חדשה ל{user.split()[0]}", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("תאריך", datetime.now())
        start_time = st.text_input("התחלה (HH:MM)", "17:00")
        end_time = st.text_input("סיום (HH:MM)", "23:00")
    with col2:
        cash = st.number_input("מזומן", min_value=0.0, step=1.0)
        credit = st.number_input("אשראי", min_value=0.0, step=1.0)
        total_input = st.number_input("סכום כללי (אם ידוע)", min_value=0.0, step=1.0)

    if st.button("💾 שמור משמרת"):
        try:
            fmt = '%H:%M'
            t1 = datetime.strptime(start_time, fmt)
            t2 = datetime.strptime(end_time, fmt)
            if t2 < t1: t2 += timedelta(days=1)
            hours = (t2 - t1).total_seconds() / 3600
            
            # לוגיקת חישוב: אם הוזן סכום כללי, נשתמש בו. אחרת, נחבר מזומן ואשראי.
            tips_sum = total_input if total_input > 0 else (cash + credit)
            
            top_up = max(0, (hours * 36) - tips_sum)
            final_total = tips_sum + top_up
            day_name = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][date.weekday()]

            new_row = {
                "שם המלצר": user,
                "תאריך": date.strftime("%d/%m/%Y"),
                "יום": day_name,
                "התחלה": start_time,
                "סיום": end_time,
                "שעות": round(hours, 2),
                "מזומן": cash,
                "אשראי": credit,
                "סכום כללי": total_input,
                "השלמה": round(top_up, 2),
                "סה\"כ": round(final_total, 2)
            }
            
            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success(f"✅ המשמרת נשמרה בהצלחה!")
            st.rerun()
            
        except Exception as e:
            st.error(f"שגיאה: {e}")

# --- תצוגת נתונים אישית ---
st.divider()
st.subheader(f"📋 היסטוריה אישית: {user}")

if not df.empty and "שם המלצר" in df.columns:
    user_df = df[df["שם המלצר"] == user]
    
    if not user_df.empty:
        st.dataframe(user_df, use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("סה\"כ רווח שלך", f"₪{user_df['סה\"כ'].sum():,.2f}")
        c2.metric("שעות עבודה", f"{user_df['שעות'].sum():,.1f}")
    else:
        st.write("אין עדיין נתונים רשומים על שמך.")
else:
    st.warning("יש לוודא שקיימות כל העמודות בגוגל שיטס לפי הסדר החדש.")
