# 📊 Sell-Out Dashboard

Streamlit dashboard για ανάλυση sell-out δεδομένων ανά χρονική περίοδο και έτος.

## Δομή repo

```
sell-out-dashboard/
├── sell_out_dashboard.py   ← Το Streamlit app
├── requirements.txt        ← Εξαρτήσεις Python
└── README.md
```

## Τοπική εκτέλεση

```bash
pip install -r requirements.txt
streamlit run sell_out_dashboard.py
```

## Deploy στο Streamlit Cloud

1. Κάνε fork / push το repo στο GitHub
2. Πήγαινε στο [share.streamlit.io](https://share.streamlit.io)
3. Επέλεξε το repo, branch `main`, και αρχείο `sell_out_dashboard.py`
4. Πάτα **Deploy**

Το app ανεβαίνει σε ~1 λεπτό.

## Χρήση

- Ανέβασε το Excel αρχείο μέσω του **file uploader** στο sidebar
- Το αρχείο πρέπει να έχει sheet με όνομα **`data`** και header στη **2η γραμμή**
- Η περίοδος (π.χ. `ΙΑΝ-ΜΑΡ`, `ΙΑΝ-ΙΟΥΝ`) διαβάζεται αυτόματα από τη στήλη **Διάστημα**

## Φίλτρα

Τα φίλτρα **Οικογένεια → Ομάδα → Κατηγορία** λειτουργούν αλυσιδωτά:  
η επιλογή Οικογένειας περιορίζει τις διαθέσιμες Ομάδες, και η Ομάδα τις Κατηγορίες.  
Όλα τα γραφήματα και KPIs ενημερώνονται αυτόματα.

## KPIs

| KPI | Περιγραφή |
|-----|-----------|
| Τζίρος L/L | Τζίρος μόνο L/L καταστημάτων |
| Τζίρος Συνόλου Δικτύου | Συνολικός τζίρος όλων των καναλιών |
| Μέση Τιμή Πώλησης | Τζίρος / Τεμάχια |

Τα δέλτα % υπολογίζονται vs το αμέσως προηγούμενο έτος στα δεδομένα.
