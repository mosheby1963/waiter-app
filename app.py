import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול משמרות - בן יאיר", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="0")

df = get_data()

st.title("💰 ניהול משמרות אישי")

# --- בחירת משתמש ---
user = st.selectbox("בחר שם:", ["ליהיא בן יאיר", "משה בן יאיר"])

tab1, tab2 = st.tabs(["➕ הזנה חדשה", "📝 עריכת משמרת"])

with tab1:
    with st.form("new_entry"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("תאריך", datetime.now())
            start_time = st.text_input("התחלה", "17:00")
            end_time = st.text_input("סיום", "23:00")
        with col2:
            cash = st.number_input("מזומן", min_value=0.0)
            credit = st.number_input("אשראי", min_value=0.0)
            total_input = st.number_input("סכום כללי", min_value=0.0)
        
        if st.form_submit_button("שמור משמרת"):
            try:
                fmt = '%H:%M'
                t1 = datetime.strptime(start_time, fmt)
                t2 = datetime.strptime(end_time, fmt)
                if t2 < t1: t2 += timedelta(days=1)
                hours = (t2 - t1).total_seconds() / 3600
                tips_sum = total_input if total_input > 0 else (cash + credit)
                top_up = max(0, (hours * 36) - tips_sum)
                day_name = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"][date.weekday()]
                
                new_id = datetime.now().strftime("%Y%m%d%H%M%S")

                new_row = {
                    "שם המלצר": user, "תאריך": date.strftime("%d/%m/%Y"), "יום": day_name,
                    "התחלה": start_time, "סיום": end_time, "שעות": round(hours, 2),
                    "מזומן": cash, "אשראי": credit, "סכום כללי": total_input,
                    "השלמה": round(top_up, 2), "סה\"כ": round(tips_sum + top_up, 2), "ID": new_id
                }
                
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(data=updated_df)
                st.success("המשמרת נשמרה!")
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה: {e}")

with tab2:
    if not df.empty and "שם המלצר" in df.columns:
        user_rows = df[df["שם המלצר"] == user]
        if not user_rows.empty:
            selection = st.selectbox("בחר משמרת לעדכון:", 
                                     user_rows.index, 
                                     format_func=lambda x: f"{user_rows.loc[x, 'תאריך']} - {user_rows.loc[x, 'סה\"כ']}₪")
            
            selected_row = user_rows.loc[selection]
            
            with st.form("edit_form"):
                new_cash = st.number_input("מזומן", value=float(selected_row['מזומן']))
                new_credit = st.number_input("אשראי", value=float(selected_row['אשראי']))
                new_total = st.number_input("סכום כללי", value=float(selected_row['סכום כללי']))
                
                if st.form_submit_button("עדכן נתונים"):
                    df.at[selection, "מזומן"] = new_cash
                    df.at[selection, "אשראי"] = new_credit
                    df.at[selection, "סכום כללי"] = new_total
                    
                    hours = selected_row['שעות']
                    tips_sum = new_total if new_total > 0 else (new_cash + new_credit)
                    top_up = max(0, (hours * 36) - tips_sum)
                    df.at[selection, "השלמה"] = round(top_up, 2)
                    df.at[selection, "סה\"כ"] = round(tips_sum + top_up, 2)
                    
                    conn.update(data=df)
                    st.success("עודכן בהצלחה!")
                    st.rerun()
        else:
            st.write("אין משמרות לעריכה.")

# --- תצוגת נתונים עם ספירה אישית ---
st.divider()
st.subheader(f"📋 היסטוריה אישית: {user}")

if not df.empty and "שם המלצר" in df.columns:
    user_df = df[df["שם המלצר"] == user].copy()
    
    if not user_df.empty:
        # כאן קורה הקסם: הוספת עמודת מספר סידורי רץ לפי המשתמש
        user_df.insert(0, "#", range(1, len(user_df) + 1))
        
        # מציגים את הטבלה ללא עמודת ה-ID הטכנית
        st.dataframe(user_df.drop(columns=["ID"]), hide_index=True, use_container_width=True)
        
        c1, c2 = st.columns(2)
        c1.metric("סה\"כ רווח שלך", f"₪{user_df['סה\"כ'].sum():,.2f}")
        c2.metric("משמרות שבוצעו", len(user_df))
    else:
        st.info("עדיין אין משמרות רשומות.")
