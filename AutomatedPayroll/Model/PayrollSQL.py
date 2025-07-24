from sqlalchemy import Column, Integer, String, DateTime, Date, CHAR, Numeric, Text, ForeignKey, create_engine, func, literal
from sqlalchemy.orm import declarative_base, sessionmaker
from enum import Enum as PyEnum
from sqlalchemy.types import Enum as SQLEnum
from datetime import date, timedelta
import pandas as pd
import os
import pickle

# Database connection
engine = create_engine("mysql+pymysql://powerbi:7mNWGrMXmguXXYPiUVaqz3Rlc-7bacV@10.25.8.81:3306/traumasoft_brewster")
Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()

# Model definitions
class timecard_punches(Base):
    __tablename__ = 'payroll_archive_timecard_punches'
    id = Column(Integer, primary_key=True)
    date_line = Column(Date)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user_id'))
    pay_period_id = Column(Integer)
    total_hours = Column(Numeric(10, 2))

class punch_discrepancies(Base):
    __tablename__ = 'user_punch_discrepancies'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_id'))
    timesheet_id = Column(Integer)

    class timecards(Base):
        __tablename__ = 'sched_timecards'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('user_id'))
        total_hours = Column(Numeric(10, 2))

class statusEnum(PyEnum):
    true = 'deactive'
    false = 'active'

class users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    disabled = Column(SQLEnum(statusEnum), default=statusEnum.false, nullable=False)
    first_name = Column(String)
    last_name = Column(String)

# Cache config
cutoff_date = date.today() - timedelta(days=40)
CACHE_FILE = 'daily_cache.pkl'

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    return {'formatted': None, 'date': None}

def save_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

_daily_cache = load_cache()

def get_data():
    """
    Queries total punch hours per user per date, avoiding duplication from shift assignments.
    Returns tuple: (formatted_data, discrepancies)
    """
    today = date.today()

    if not isinstance(_daily_cache['date'], date) or _daily_cache['date'] != today:
        print(f"⏳ Refreshing data for {today}...")

        results = session.query(
            users.user_id,
            func.concat(users.first_name, literal(' '), users.last_name).label('name'),
            timecard_punches.date_line,
            func.sum(timecard_punches.total_hours).label('total_hours')
        ).join(
            timecard_punches, users.user_id == timecard_punches.user_id
        ).filter(
            users.disabled == 'false',
            timecard_punches.date_line >= cutoff_date
        ).group_by(
            users.user_id,
            users.first_name,
            users.last_name,
            timecard_punches.date_line
        ).order_by(
            timecard_punches.date_line.asc(),
            users.user_id.asc()
        ).all()

        formatted_combined = [
            {
                'user_id': r.user_id,
                'name': r.name,
                'date': r.date_line.strftime('%Y-%m-%d') if r.date_line else None,
                'total_hours': float(r.total_hours) if r.total_hours else 0.0
            }
            for r in results
        ]

        _daily_cache['formatted'] = formatted_combined
        _daily_cache['date'] = today
        _daily_cache['discrepancies'] = None

        save_cache(_daily_cache)

    else:
        print(f"✅ Using cached data for {today}...")

    return _daily_cache['formatted'], _daily_cache['discrepancies']

def get_formatted_combined_df():
    """
    Returns the formatted combined punch data as a pandas DataFrame.
    """
    formatted, _ = get_data()
    df = pd.DataFrame(formatted)
    return df

def print_total_hours_by_user_date():
    """
    Prints all total hours by user and date in a readable DataFrame format.
    """
    formatted, _ = get_data()
    df = pd.DataFrame(formatted)

    if not df.empty:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.colheader_justify', 'center')
    pd.set_option('display.precision', 2)

    print(df)

# Run the main output
print_total_hours_by_user_date()
