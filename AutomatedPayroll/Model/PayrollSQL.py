from sqlalchemy import (
    TEXT, Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Text,
    create_engine, and_, func
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import Enum as SQLEnum
from enum import Enum as PyEnum
from datetime import date, timedelta
import pandas as pd
import os

import pickle
import sys

# === Add for PyInstaller compatibility ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === Use this for cache access ===
CACHE_FILE = resource_path("TEST_cache.pkl")
# CSV_FILE = resource_path("TEST.csv")  # Optional

# Database connection
DATABASE_URL = "mysql+pymysql://powerbi:7mNWGrMXmguXXYPiUVaqz3Rlc-7bacV@10.25.8.81:3306/traumasoft_brewster"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Database models
class timecard_punches(Base):
    __tablename__ = 'payroll_archive_timecard_punches'
    id = Column(Integer, primary_key=True)
    date_line = Column(Date)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    pay_period_id = Column(Integer)
    earning_code_id = Column(Integer)
    cost_center_id = Column(Integer, ForeignKey('cost_centers.id'))
    total_hours = Column(Numeric(10, 2))
    # division_id = Column(Integer)

class statusEnum(PyEnum):
    true = 'deactive'
    false = 'active'

class users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    disabled = Column(SQLEnum(statusEnum), default=statusEnum.false, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    # user_division = Column(Text)
    supervisor_id = Column(Integer)
    # user_division = Column(Text)

class shifts(Base):
    __tablename__ = 'sched_template_shift_assignments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    date_line = Column(Date)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    division_id = Column(Integer)

class cost_centers(Base):
    __tablename__ = 'cost_centers'
    id = Column(Integer, primary_key=True)
    name = Column(String)

# pickle.dump({"date": "2000-01-01", "data": []}, open(CACHE_FILE, "wb"))
# === Cache management ===
if not os.path.exists(CACHE_FILE):
    pickle.dump({"date": "2000-01-01", "data": []}, open(CACHE_FILE, "wb"))

def is_cache_fresh():
    if not os.path.exists(CACHE_FILE):
        return False
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)
    return cache.get("date") == str(date.today())

def save_cache(df):
    cache = {
        "date": str(date.today()),
        "data": df.to_dict(orient="records")
    }
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)

def load_cache():
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)
    return pd.DataFrame(cache["data"])


# === Data export ===
def export():
    if is_cache_fresh():
        print("Using cached data...")
        df = load_cache()
    else:
        print("Querying fresh data from database...")
        cutoff_date = date.today() - timedelta(days=40)

        shift_subq = (
            session.query(
                shifts.user_id,
                shifts.date_line,
                shifts.division_id,
                func.min(shifts.start_time).label("scheduled_start"),
                func.max(shifts.end_time).label("scheduled_end")
            )
            .group_by(shifts.user_id, shifts.date_line)
        ).subquery()

        query = (
            session.query(
                (users.first_name + " " + users.last_name).label("employee_name"),
                timecard_punches.id,
                timecard_punches.user_id,
                timecard_punches.date_line,
                timecard_punches.earning_code_id,
                timecard_punches.cost_center_id,
                cost_centers.name.label("cost_center_name"),  # Added line
                timecard_punches.pay_period_id,
                timecard_punches.total_hours.label("actual_hours"),
                shift_subq.c.scheduled_start,
                shift_subq.c.scheduled_end
            )
            .join(users, timecard_punches.user_id == users.user_id)
            .outerjoin(shift_subq, and_(
                shift_subq.c.user_id == timecard_punches.user_id,
                shift_subq.c.date_line == timecard_punches.date_line
            ))
            .outerjoin(cost_centers, timecard_punches.cost_center_id == cost_centers.id)  # Join cost_centers
            .filter(timecard_punches.date_line >= cutoff_date)
        )

        df = pd.read_sql(query.statement, engine)

        df['scheduled_hours'] = (
            pd.to_datetime(df['scheduled_end']) - pd.to_datetime(df['scheduled_start'])
        ).dt.total_seconds() / 3600

        df['discrepancy'] = df['actual_hours'] - df['scheduled_hours']

        save_cache(df)

    print("Data export complete (returned as DataFrame)")
    return df


