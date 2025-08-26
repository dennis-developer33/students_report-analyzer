import pandas as pd

def process_csv(filepath, chunksize=50000):
    """
    Load CSV into a pandas DataFrame in chunks to avoid memory issues.
    Normalizes columns and validates required fields.
    """
    chunks = []
    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        # --- Normalize column names ---
        chunk.columns = chunk.columns.str.strip().str.replace(" ", "_")

        # --- Fix known variations ---
        column_mapping = {
            "Visits__to_Website": "Visits_to_Website",
            "Visits__To__Website": "Visits_to_Website",
            "Total_Visits_By_User": "Total_Visits"
        }
        chunk.rename(columns=column_mapping, inplace=True)

        # --- Ensure required columns exist ---
        required = [
            "Username_TRNO",
            "Student_FullName",
            "Student_Class",
            "Website_Address",
            "Visits_to_Website",
            "Last_Visit_Time",
            "Total_Visits"
        ]
        for col in required:
            if col not in chunk.columns:
                raise ValueError(f"Missing required column: {col}")

        # --- Data type normalization ---
        chunk["Last_Visit_Time"] = pd.to_datetime(chunk["Last_Visit_Time"], errors="coerce")
        chunk["Visits_to_Website"] = pd.to_numeric(chunk["Visits_to_Website"], errors="coerce").fillna(0).astype(int)
        chunk["Total_Visits"] = pd.to_numeric(chunk["Total_Visits"], errors="coerce").fillna(0).astype(int)

        for col in ["Username_TRNO", "Student_FullName", "Website_Address", "Student_Class"]:
            chunk[col] = chunk[col].astype(str).fillna("")

        chunks.append(chunk)

    # Combine all chunks into one DataFrame
    df = pd.concat(chunks, ignore_index=True)
    return df


def filter_data(df, username=None, class_name=None, start_date=None, end_date=None):
    """Filter DataFrame by username, class, and date range."""
    filtered = df.copy()

    if username:
        username_lower = username.lower().strip()
        filtered = filtered[
            filtered["Username_TRNO"].str.lower().str.contains(username_lower, na=False) |
            filtered["Student_FullName"].str.lower().str.contains(username_lower, na=False) |
            filtered["Website_Address"].str.lower().str.contains(username_lower, na=False)
        ]

    if class_name:
        filtered = filtered[filtered["Student_Class"].str.lower() == class_name.lower()]

    if start_date:
        try:
            start_dt = pd.to_datetime(start_date, errors="coerce")
            filtered = filtered[filtered["Last_Visit_Time"] >= start_dt]
        except Exception:
            pass

    if end_date:
        try:
            end_dt = pd.to_datetime(end_date, errors="coerce")
            filtered = filtered[filtered["Last_Visit_Time"] <= end_dt]
        except Exception:
            pass

    return filtered


def paginate_data(df, page=1, per_page=50):
    """Return a subset of the DataFrame for the requested page."""
    start = (page - 1) * per_page
    end = start + per_page
    return df.iloc[start:end].reset_index(drop=True)


def generate_summary(df):
    """Generate analytics summaries for dashboard cards and charts."""
    summary = {}

    if df.empty:
        return {
            "total_students": 0,
            "total_visits": 0,
            "unique_websites": 0,
            "avg_visits_per_student": 0,
            "top_websites": {"labels": [], "data": []},
            "active_students": {"labels": [], "data": []},
            "visits_over_time": {"labels": [], "data": []}
        }

    # General stats
    summary["total_students"] = df["Username_TRNO"].nunique()
    summary["total_visits"] = int(df["Total_Visits"].sum())
    summary["unique_websites"] = df["Website_Address"].nunique()
    summary["avg_visits_per_student"] = round(df["Total_Visits"].mean(), 2)

    # Top websites
    top_websites = (
        df.groupby("Website_Address")["Visits_to_Website"]
          .sum()
          .sort_values(ascending=False)
          .head(10)
          .reset_index()
    )
    summary["top_websites"] = {
        "labels": top_websites["Website_Address"].tolist(),
        "data": top_websites["Visits_to_Website"].astype(int).tolist()
    }

    # Most active students
    top_users = (
        df.groupby("Username_TRNO")["Total_Visits"]
          .sum()
          .sort_values(ascending=False)
          .head(10)
          .reset_index()
    )
    summary["active_students"] = {
        "labels": top_users["Username_TRNO"].tolist(),
        "data": top_users["Total_Visits"].astype(int).tolist()
    }

    # Visits over time
    if "Last_Visit_Time" in df and not df["Last_Visit_Time"].isna().all():
        visits_time = (
            df.groupby(df["Last_Visit_Time"].dt.date)["Total_Visits"]
              .sum()
              .reset_index()
              .sort_values("Last_Visit_Time")
        )
        summary["visits_over_time"] = {
            "labels": visits_time["Last_Visit_Time"].astype(str).tolist(),
            "data": visits_time["Total_Visits"].astype(int).tolist()
        }
    else:
        summary["visits_over_time"] = {"labels": [], "data": []}

    return summary
