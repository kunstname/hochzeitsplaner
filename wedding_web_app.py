import streamlit as st
import pandas as pd
import sqlite3

# --- KONFIGURATION & STYLES ---
st.set_page_config(page_title="Hochzeit", page_icon="💍", layout="wide")

st.markdown("""
    <style>
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.3rem !important;
        padding-right: 0.3rem !important;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Spalte 2 (👥 Anzahl): extrem schmal (28px) */
    [data-testid="stDataFrame"] th:nth-child(2),
    [data-testid="stDataFrame"] td:nth-child(2),
    [data-testid="stDataEditor"] th:nth-child(2),
    [data-testid="stDataEditor"] td:nth-child(2) {
        width: 28px !important;
        max-width: 28px !important;
        min-width: 28px !important;
        text-align: center !important;
    }

    /* Spalte 3 (Kategorie): passend für Klartext */
    [data-testid="stDataFrame"] th:nth-child(3),
    [data-testid="stDataFrame"] td:nth-child(3),
    [data-testid="stDataEditor"] th:nth-child(3),
    [data-testid="stDataEditor"] td:nth-child(3) {
        width: 100px !important;
        max-width: 110px !important;
        min-width: 90px !important;
    }

    /* Spalte 4 (Anw.): kompakt */
    [data-testid="stDataFrame"] th:nth-child(4),
    [data-testid="stDataFrame"] td:nth-child(4),
    [data-testid="stDataEditor"] th:nth-child(4),
    [data-testid="stDataEditor"] td:nth-child(4) {
        width: 85px !important;
        max-width: 95px !important;
        min-width: 75px !important;
    }

    /* Namen umbrechen statt horizontal scrollen */
    [data-testid="stDataFrame"] td:first-child,
    [data-testid="stDataEditor"] td:first-child {
        white-space: normal !important;
        line-height: 1.1 !important;
    }

    .metric-container {
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        gap: 4px;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #1e222d;
        border: 1px solid #2e3440;
        border-radius: 6px;
        padding: 6px 8px;
        text-align: center;
        flex: 1;
        min-width: 0;
    }
    .metric-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #8892b0;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: bold;
        color: #ffffff;
    }
    .metric-sub {
        font-size: 0.7rem;
        font-weight: 500;
        color: #d8dee9;
        background-color: #2e3440;
        border-radius: 3px;
        padding: 1px 4px;
        display: inline-block;
        margin-top: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONSTANTEN & MAPPINGS ---
DB_FILE = "hochzeit.db"

CATEGORIES = ["Familie", "Verwandte", "Freunde", "Arbeit", "Nachbarn", "Sonstige"]
EVENT_OPTIONS = ["Trauung", "Wirt"]
STATUS_OPTIONS = ["⚪ Offen", "📩 Verschickt", "✅ Abgegeben"]
RSVP_OPTIONS = ["🟠 Ausstehend", "🟢 Zugesagt", "🔴 Abgesagt"]

ANW_TO_DISPLAY = {
    "Trauung": "💍 Trauung",
    "Wirt": "🍻 Wirt"
}
DISPLAY_TO_ANW = {v: k for k, v in ANW_TO_DISPLAY.items()}

# --- DATENBANK FUNKTIONEN ---
def get_db_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(gaeste)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Kategorie" not in columns:
            cursor.execute("ALTER TABLE gaeste ADD COLUMN Kategorie TEXT DEFAULT 'Freunde'")
            conn.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gaeste (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Haushalt_ID INTEGER,
                Vorname TEXT,
                Nachname TEXT,
                Anwesenheit TEXT,
                Status TEXT,
                RSVP TEXT,
                Kategorie TEXT
            )
        """)
        conn.commit()
        
        cursor.execute("UPDATE gaeste SET RSVP = '🟢 Zugesagt' WHERE RSVP = 'Zugesagt'")
        cursor.execute("UPDATE gaeste SET RSVP = '🔴 Abgesagt' WHERE RSVP = 'Abgesagt'")
        cursor.execute("UPDATE gaeste SET RSVP = '🟠 Ausstehend' WHERE RSVP IN ('Ausstehend', 'Offen')")
        cursor.execute("UPDATE gaeste SET Status = '✅ Abgegeben' WHERE Status = 'Abgegeben'")
        cursor.execute("UPDATE gaeste SET Status = '📩 Verschickt' WHERE Status = 'Verschickt'")
        cursor.execute("UPDATE gaeste SET Status = '⚪ Offen' WHERE Status = 'Offen'")
        cursor.execute("UPDATE gaeste SET Kategorie = 'Freunde' WHERE Kategorie IS NULL OR Kategorie = ''")
        
        cursor.execute("SELECT MAX(Haushalt_ID) FROM gaeste")
        max_h = cursor.fetchone()[0] or 39
        new_h_id = max(max_h + 1, 40)
        cursor.execute("UPDATE gaeste SET Haushalt_ID = ? WHERE Haushalt_ID = 9 AND Vorname IN ('Lisa', 'Lisa Freund')", (new_h_id,))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM gaeste")
        if cursor.fetchone()[0] == 0:
            initial_data = [
                (1, "Chris", "Angerer", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (2, "Gerhard", "Angerer", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (2, "Karin", "Angerer", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (3, "Christine", "Bauernhansl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (3, "Markus", "Bauernhansl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (4, "Karin", "Brandl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (4, "Hannes", "Brandl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (5, "Stefi", "Buchberger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (6, "Benji", "Diethard", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (6, "Nadine", "Diethard", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (7, "Manuel", "Döllerer", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (8, "Maria", "Döllerer", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (7, "Nicky", "Döllerer", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (9, "Elisabeth", "Dürnberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (9, "Wolfgang", "Dürnberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (40, "Lisa", "Dürnberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (40, "Lisa Freund", "Dürnberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (10, "Andreas", "Fink", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (10, "Meli", "Fink", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (11, "Hias", "Grössinger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (11, "Olga", "Grössinger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (12, "Alexandra", "Gschaider", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (12, "Carina", "Gschaider", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (12, "Franz", "Gschaider", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (12, "Lisa", "Gschaider", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (12, "Michi", "Gschaider", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (12, "Mirijam", "Gschaider", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (13, "Steffi", "Hauser", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (13, "Thomas", "Hauser", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (14, "Bernd", "Hillerzeder", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (14, "Steffi", "Hillerzeder", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (15, "Christer", "Hofer", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (15, "Hans", "Hofer", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (16, "Georg", "Huber", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (16, "Kathrin", "Huber", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (17, "Sandra", "Kemetinger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (17, "Gerald", "Kemetinger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (17, "Sabine", "Kemetinger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (18, "Julia", "Kranzinger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (18, "Patrik", "Kranzinger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (19, "Eva", "Landrichtinger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (20, "Claudia", "Leberer", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (21, "Julia", "Lehner", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (21, "Michi", "Lehner", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (22, "Sonja", "Luginger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (22, "Thomas", "Luginger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (23, "Melli", "Maier", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (23, "Robert", "Maier", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (24, "Andi", "Mangelberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (24, "Kathi", "Mangelberger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (25, "Dittlinde", "Mantl", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (25, "Helmut", "Mantl", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (26, "Dominik", "Moser", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (27, "Johannes", "Niedermüller", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (27, "Tanja", "Niedermüller", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (28, "Ingrid", "Pfaff", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (29, "Maria", "Pommwenger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (29, "Seppi", "Pommwenger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (29, "Waltdruad", "Pommwenger", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (30, "Dani", "Radauer", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (31, "Maria", "Rehrl", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (31, "Franz", "Rehrl", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Adelheit", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Heidi", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Marianne", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Otto", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Thomas", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (32, "Willi", "Reichl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Verwandte"),
                (33, "Matthias", "Rosenegger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (33, "Theresa", "Rosenegger", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (34, "David", "Schober", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (35, "Bea", "Schwarzenbacher", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (35, "Dani", "Schwarzenbacher", "Wirt", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (36, "Alex", "Schweitl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (36, "Sarah", "Schweitl", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (37, "Caro", "Voith", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (37, "Franziska", "Voith", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (37, "Markus", "Voith", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (37, "Philipp", "Voith", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (38, "Andi", "Walcher", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (38, "Melli", "Walcher", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Freunde"),
                (39, "Lisa", "Wörgötter", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (39, "Peter", "Wörgötter", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (39, "Sabrina", "Wörgötter", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (39, "Franziska", "Wörgötter", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie"),
                (39, "Hias", "Wörgötter", "Trauung", "⚪ Offen", "🟠 Ausstehend", "Familie")
            ]
            cursor.executemany("INSERT INTO gaeste (Haushalt_ID, Vorname, Nachname, Anwesenheit, Status, RSVP, Kategorie) VALUES (?, ?, ?, ?, ?, ?, ?)", initial_data)
            conn.commit()

def load_data():
    with get_db_connection() as conn:
        return pd.read_sql("SELECT id, Haushalt_ID, Vorname, Nachname, Anwesenheit, Status, RSVP, Kategorie FROM gaeste", conn)

def save_haushalt_planung(h_id, kategorie, anwesenheit):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE gaeste SET Kategorie = ?, Anwesenheit = ? WHERE Haushalt_ID = ?", (kategorie, anwesenheit, h_id))
        conn.commit()

def save_haushalt_status(h_id, status, zugesagt_anzahl, abgesagt_anzahl):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM gaeste WHERE Haushalt_ID = ?", (h_id,))
        p_ids = [r[0] for r in cursor.fetchall()]
        
        for p_id in p_ids:
            cursor.execute("UPDATE gaeste SET Status = ? WHERE id = ?", (status, p_id))
        
        for i, p_id in enumerate(p_ids):
            if i < zugesagt_anzahl:
                rsvp_val = "🟢 Zugesagt"
            elif i < (zugesagt_anzahl + abgesagt_anzahl):
                rsvp_val = "🔴 Abgesagt"
            else:
                rsvp_val = "🟠 Ausstehend"
            cursor.execute("UPDATE gaeste SET RSVP = ? WHERE id = ?", (rsvp_val, p_id))
            
        conn.commit()

def add_new_guest(h_id, vorname, nachname, anwesenheit, status, rsvp, kategorie):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO gaeste (Haushalt_ID, Vorname, Nachname, Anwesenheit, Status, RSVP, Kategorie)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (h_id, vorname, nachname, anwesenheit, status, rsvp, kategorie))
        conn.commit()

def move_person_to_haushalt(person_id, new_h_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE gaeste SET Haushalt_ID = ? WHERE id = ?", (new_h_id, person_id))
        conn.commit()

# --- INITIALISIERUNG & DATEN LADEN ---
init_db()
df = load_data()

# Statistische Kennzahlen
total_guests = len(df)
trauung_guests = len(df[df["Anwesenheit"] == "Trauung"])
wirt_guests = len(df[df["Anwesenheit"] == "Wirt"])

total_inv = df["Haushalt_ID"].nunique() if not df.empty else 0
inv_trauung = df[df["Anwesenheit"] == "Trauung"]["Haushalt_ID"].nunique() if not df.empty else 0
inv_wirt = df[df["Anwesenheit"] == "Wirt"]["Haushalt_ID"].nunique() if not df.empty else 0

distributed_inv = df[df["Status"].isin(["📩 Verschickt", "✅ Abgegeben"])]["Haushalt_ID"].nunique() if not df.empty else 0

rsvp_yes = len(df[df["RSVP"] == "🟢 Zugesagt"])
rsvp_no = len(df[df["RSVP"] == "🔴 Abgesagt"])
rsvp_pending = len(df[df["RSVP"] == "🟠 Ausstehend"])

# --- TITEL ---
st.title("💍 Hochzeitsplaner")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Filter & Verwaltung")
filter_event = st.sidebar.selectbox("Event-Filter:", ["Alle"] + EVENT_OPTIONS)

categories_filter = ["Alle"] + sorted(list(df["Kategorie"].dropna().unique())) if not df.empty else ["Alle"]
filter_kat = st.sidebar.selectbox("Kategorie-Filter:", categories_filter)

st.sidebar.divider()
st.sidebar.subheader("🔀 Person umziehen")

selected_person_id_from_click = st.session_state.get("clicked_person_id", None)

if not df.empty:
    with st.sidebar.expander("Person in anderen Haushalt", expanded=False):
        p_dict = {}
        default_index = 0
        
        df_sorted = df.sort_values(by=["Vorname", "Nachname"])
        for idx, (_, r) in enumerate(df_sorted.iterrows()):
            label = f"{r['Vorname']} {r['Nachname']}"
            p_dict[label] = (r["id"], r["Haushalt_ID"])
            if selected_person_id_from_click and r["id"] == selected_person_id_from_click:
                default_index = idx
                
        selected_p_str = st.selectbox("1. Person:", list(p_dict.keys()), index=default_index)
        selected_p_id, current_h_id = p_dict[selected_p_str]
        
        h_names_dict = {}
        for h_id_val, group_df in df.groupby("Haushalt_ID"):
            if h_id_val != current_h_id:
                nachnamen = group_df["Nachname"].unique()
                if len(nachnamen) == 1:
                    v_str = " & ".join(group_df["Vorname"].tolist())
                    h_label = f"{v_str} {nachnamen[0]}"
                else:
                    p_n = [f"{r['Vorname']} {r['Nachname']}" for _, r in group_df.iterrows()]
                    h_label = " & ".join(p_n)
                h_names_dict[h_label] = h_id_val

        if h_names_dict:
            target_h_label = st.selectbox("2. Ziel-Haushalt:", sorted(list(h_names_dict.keys())))
            if st.button("Zu diesem Haushalt umziehen"):
                move_person_to_haushalt(selected_p_id, h_names_dict[target_h_label])
                st.session_state["clicked_person_id"] = None
                st.success("Erfolgreich umgezogen!")
                st.rerun()

        if st.button("➕ In neuen eigenen Haushalt"):
            max_h_val = int(df["Haushalt_ID"].max()) + 1 if not df.empty else 1
            move_person_to_haushalt(selected_p_id, max_h_val)
            st.session_state["clicked_person_id"] = None
            st.success("In neuen Haushalt verschoben!")
            st.rerun()

st.sidebar.divider()
st.sidebar.subheader("➕ Neuen Gast hinzufügen")
with st.sidebar.form("add_guest_form"):
    max_id = int(df["Haushalt_ID"].max()) if not df.empty else 1
    new_id = st.number_input("Haushalt-ID", min_value=1, step=1, value=max_id + 1)
    new_vorname = st.text_input("Vorname")
    new_nachname = st.text_input("Nachname")
    new_anwesenheit = st.selectbox("Anwesenheit", EVENT_OPTIONS)
    new_kategorie = st.selectbox("Kategorie", CATEGORIES)
    new_status = st.selectbox("Status", STATUS_OPTIONS)
    new_rsvp = st.selectbox("Rückmeldung", RSVP_OPTIONS)
    
    submit_btn = st.form_submit_button("Gast speichern")
    if submit_btn:
        if new_vorname and new_nachname:
            add_new_guest(int(new_id), new_vorname, new_nachname, new_anwesenheit, new_status, new_rsvp, new_kategorie)
            st.success("Gast hinzugefügt!")
            st.rerun()
        else:
            st.error("Vor- & Nachname eingeben.")

# Filter anwenden
df_filtered = df.copy()
if filter_event != "Alle":
    df_filtered = df_filtered[df_filtered["Anwesenheit"] == filter_event]
if filter_kat != "Alle":
    df_filtered = df_filtered[df_filtered["Kategorie"] == filter_kat]

def get_haushalte_dataframe(df_source):
    haushalte_list = []
    for h_id, group in df_source.groupby("Haushalt_ID"):
        anzahl_p = len(group)
        nachnamen = group["Nachname"].unique()
        if len(nachnamen) == 1:
            vornamen_str = " & ".join(group["Vorname"].tolist())
            display_name = f"{vornamen_str} {nachnamen[0]}"
        else:
            p_names = [f"{r['Vorname']} {r['Nachname']}" for _, r in group.iterrows()]
            display_name = " & ".join(p_names)
            
        cur_kat = group["Kategorie"].iloc[0] if not group["Kategorie"].empty else "Freunde"
        cur_anw = group["Anwesenheit"].iloc[0] if not group["Anwesenheit"].empty else "Trauung"
        cur_status = group["Status"].iloc[0] if not group["Status"].empty else "⚪ Offen"
        cur_yes = len(group[group["RSVP"] == "🟢 Zugesagt"])
        cur_no = len(group[group["RSVP"] == "🔴 Abgesagt"])
        
        haushalte_list.append({
            "Haushalt_ID": h_id,
            "Haushalt / Namen": display_name,
            "👥": anzahl_p,
            "Kategorie": cur_kat,
            "Anw.": ANW_TO_DISPLAY.get(cur_anw, cur_anw),
            "Status": cur_status,
            "🟢 Ja": cur_yes,
            "🔴 Nein": cur_no
        })
    return pd.DataFrame(haushalte_list)

# --- TABS ---
tab_planung, tab_status = st.tabs(["📋 1. Planung", "✉️ 2. Status"])

# --- TAB 1: PLANUNG ---
with tab_planung:
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-label">👥 Gesamt</div>
                <div class="metric-value">{total_guests}</div>
                <div class="metric-sub">Karten: {total_inv}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">💍 Trauung</div>
                <div class="metric-value">{trauung_guests}</div>
                <div class="metric-sub">Karten: {inv_trauung}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🍻 Wirt</div>
                <div class="metric-value">{wirt_guests}</div>
                <div class="metric-sub">Karten: {inv_wirt}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_h_planung = get_haushalte_dataframe(df_filtered)
    
    if not df_h_planung.empty:
        edited_h_planung = st.data_editor(
            df_h_planung[["Haushalt / Namen", "👥", "Kategorie", "Anw."]],
            column_config={
                "Haushalt / Namen": st.column_config.TextColumn("Haushalt / Namen", disabled=True),
                "👥": st.column_config.NumberColumn("👥", disabled=True, width="small"),
                "Kategorie": st.column_config.SelectboxColumn("Kategorie", options=CATEGORIES, required=True),
                "Anw.": st.column_config.SelectboxColumn("Anw.", options=list(ANW_TO_DISPLAY.values()), required=True)
            },
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            key="editor_h_planung"
        )
        
        if st.session_state.get("editor_h_planung") and st.session_state["editor_h_planung"].get("edited_rows"):
            for idx, changes in st.session_state["editor_h_planung"]["edited_rows"].items():
                row_data = df_h_planung.iloc[idx]
                h_id = int(row_data["Haushalt_ID"])
                
                new_kat = changes.get("Kategorie", row_data["Kategorie"])
                
                new_anw_text = changes.get("Anw.", row_data["Anw."])
                new_anw = DISPLAY_TO_ANW.get(new_anw_text, "Trauung")
                
                save_haushalt_planung(h_id, new_kat, new_anw)
            st.rerun()

    with st.expander("🔍 Einzelne Personen anzeigen"):
        df_single_display = df_filtered.sort_values(by=["Vorname", "Nachname"])[["Vorname", "Nachname", "Anwesenheit", "Kategorie"]].reset_index(drop=True)
        
        event_single = st.dataframe(
            df_single_display,
            on_select="rerun",
            selection_mode="single-row",
            hide_index=True,
            use_container_width=True
        )
        
        if event_single and event_single.get("selection") and event_single["selection"].get("rows"):
            clicked_row_idx = event_single["selection"]["rows"][0]
            sel_row = df_single_display.iloc[clicked_row_idx]
            matching_p = df_filtered[(df_filtered["Vorname"] == sel_row["Vorname"]) & (df_filtered["Nachname"] == sel_row["Nachname"])]
            if not matching_p.empty:
                clicked_p_id = int(matching_p.iloc[0]["id"])
                st.session_state["clicked_person_id"] = clicked_p_id
                st.toast(f"Ausgewählt: {sel_row['Vorname']} {sel_row['Nachname']}! Siehe Sidebar 👈")

# --- TAB 2: STATUS & RÜCKMELDUNGEN JE HAUSHALT ---
with tab_status:
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <div class="metric-label">📩 Verteilt</div>
                <div class="metric-value">{distributed_inv}/{total_inv}</div>
                <div class="metric-sub">Karten</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🟢 Zugesagt</div>
                <div class="metric-value">{rsvp_yes}</div>
                <div class="metric-sub">Gäste</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🔴 Abgesagt</div>
                <div class="metric-value">{rsvp_no}</div>
                <div class="metric-sub">Gäste</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">🟠 Offen</div>
                <div class="metric-value">{rsvp_pending}</div>
                <div class="metric-sub">Gäste</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_haushalte = get_haushalte_dataframe(df_filtered)
    
    if not df_haushalte.empty:
        max_persons = int(df_haushalte["👥"].max()) if not df_haushalte.empty else 10
        count_options = list(range(max_persons + 1))
        
        edited_haushalte = st.data_editor(
            df_haushalte[["Haushalt / Namen", "👥", "Status", "🟢 Ja", "🔴 Nein"]],
            column_config={
                "Haushalt / Namen": st.column_config.TextColumn("Haushalt / Namen", disabled=True),
                "👥": st.column_config.NumberColumn("👥", disabled=True, width="small"),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=STATUS_OPTIONS,
                    required=True
                ),
                "🟢 Ja": st.column_config.SelectboxColumn(
                    "🟢 Ja",
                    options=count_options,
                    required=True
                ),
                "🔴 Nein": st.column_config.SelectboxColumn(
                    "🔴 Nein",
                    options=count_options,
                    required=True
                )
            },
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            key="editor_haushalte"
        )
        
        if st.session_state.get("editor_haushalte") and st.session_state["editor_haushalte"].get("edited_rows"):
            for idx, changes in st.session_state["editor_haushalte"]["edited_rows"].items():
                row_data = df_haushalte.iloc[idx]
                h_id = int(row_data["Haushalt_ID"])
                st_val = changes.get("Status", row_data["Status"])
                yes_val = int(changes.get("🟢 Ja", row_data["🟢 Ja"]))
                no_val = int(changes.get("🔴 Nein", row_data["🔴 Nein"]))
                save_haushalt_status(h_id, st_val, yes_val, no_val)
            st.rerun()

st.divider()

csv_data = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="📥 CSV exportieren",
    data=csv_data,
    file_name="hochzeitsliste_db.csv",
    mime="text/csv"
)