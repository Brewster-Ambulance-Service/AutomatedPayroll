from sqlalchemy import Column, Integer, String, DateTime, Date, CHAR, Numeric, Text, ForeignKey, create_engine, func, literal, and_, literal_column
from sqlalchemy.orm import declarative_base, sessionmaker
from enum import Enum as PyEnum
from sqlalchemy.types import Enum as SQLEnum
from datetime import date, timedelta
import pandas as pd
import os 
import pickle


"""
Connecting to the Brewster EMS MySQL dataase and creating an engine to it for easy access and use. Also creating a Base to hold and track all of our 
mappings for our database tables. Adding a session object to allows querying changes and pulling from database engine, and communicating with the database.
"""
engine = create_engine("mysql+pymysql://powerbi:7mNWGrMXmguXXYPiUVaqz3Rlc-7bacV@10.25.8.81:3306/traumasoft_brewster")
Session = sessionmaker(bind = engine)
Base = declarative_base()
session = Session()


class timecard_punches(Base):   
    """
    Mapping for the payroll_archive_timecard_punches table from the SQL database, with the relevant variable names that we will be using from the table
    ready to be loaded with the Schema. 
    """
    __tablename__ = 'payroll_archive_timecard_punches'

    id = Column(Integer, primary_key=True)
    date_line = Column(Date)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    user_id = Column(Integer, ForeignKey('user_id'))
    pay_period_id = Column(Integer)
    total_hours = Column(Numeric(10,2))
    shift_assignment_id = Column(Integer, ForeignKey('sched_template_shift_assignments.id'))
    # cost_center_id = Column(Integer, ForeignKey('cost_center.id'))
    # earning_code_id = Column(Integer, ForeignKey('earning_code.id'))

    def __repr__(self):
        return (f"<PayrollArchiveTimecardPunches(id={self.id}, date_line={self.date_line}, "
            f"start_time={self.start_time}, end_time={self.end_time}, type='{self.type}', "
            f"user_id={self.user_id}"
            f"total_hours={self.total_hours}, shift_assignment_id={self.shift_assignment_id})>")


class shift_assignments(Base):
    """
    Mapping for the sched_template_shift_assignments table from the SQL database, with the relevant variable names that we will be using from the table
    ready to be loaded with the Schema. 
    """
    __tablename__ = 'sched_template_shift_assignments'
 
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey('user_id'))
    comments = Column(Text)
    date_line = Column(Date)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    earning_code_id = Column(Integer, ForeignKey('earning_code.id'))
    cost_center_id = Column(Integer, ForeignKey('cost_center.id'))
    # pay_period_id = Column(Integer, ForeignKey('pay_period.id'))

    def __repr__(self):
        return (f"<shift_assignments(id={self.id}, user_id={self.user_id} comments={repr(self.comments)}, date_line={self.date_line}, "
                f"start_time={self.start_time}, end_time={self.end_time})>")
    

class punch_discrepancies(Base): 
    """
    Mapping for the user_punch_discrepancies table from the SQL database, with the relevant variable names that we will be using from the table
    ready to be loaded with the Schema. 
    """
    __tablename__ = 'user_punch_discrepancies'

    id = Column(Integer, primary_key= True)
    user_id = Column(Integer, ForeignKey('user_id'))
    timesheet_id = Column(Integer, ForeignKey(''))
    shift_assignment_id = Column(Integer, ForeignKey('sched_template_shift_assignments.id'))

    def __repr__(self):
        return (f"<punch_discrepancies(id={self.id}, user_id={self.user_id}, timesheet_id={self.timesheet_id}, "
                f"shift_assignment_id={self.shift_assignment_id})>")
    
    class timecards(Base):
        '"Mapping for the timecards table from the SQL database, with the relevant variable names that we will be using from the table'

        __tablename__ = 'sched_timecards'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('user_id'))
        total_hours = Column(Numeric(10,2))

        def __repr__(self):
            return (f"<timecards(id={self.id}, user_id={self.user_id}, total_hours={self.total_hours})>")


#enum class for the false and true values for the disabled column as specified in the data dictionary
class statusEnum(PyEnum):
    true = 'deactive'
    false = 'active'

#users table mapping
class users(Base):
    """
    Mapping for the users table from the SQL database, with the relevant variable names that we will be using from the table
    ready to be loaded with the Schema. 
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    disabled = Column(SQLEnum(statusEnum), default=statusEnum.false, nullable=False)
    # deactivated = Column(Integer) #delete later
    # termination_date = Column(CHAR) #delete laerer
    first_name = Column(String)
    last_name = Column(String)

    def __repr__(self):
     return (f"<User(user_id={self.user_id}, name='{self.first_name} {self.last_name}', "
             f"disabled={self.disabled.name})>")

    

#cutsoff the data results to only the last 60 days to avoid pulling too much data and slowing down the query
cutoff_date = date.today() - timedelta(days=40)

#defines the cache file to store the daily data 
CACHE_FILE = 'daily_cache.pkl'

#loads the cache with the current data and time values
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    return {
        'formatted': None,
        'date': None
    }

#saves the cache
def save_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

#initalizes the cache 

_daily_cache = load_cache()

#uncomment this line to force reset the cache to see c
# _daily_cache['date'] = date(2000, 1, 1)

def get_data():
    """
    Queries the database to create the discrepancies and the formatted combined punch and shift data and formats into a usable dataframe and structure.
    Returns both the formatted combined data and the discrepancies, as a tuple for use in the PayrollAutomation class.
    """
    today = date.today()

    if not isinstance(_daily_cache['date'], date) or _daily_cache['date'] != today:
        print(f"⏳ Refreshing data for {today}...")

        #limits the query to only the last 40 days of data
        cutoff_date = today - timedelta(days=40)

        #Advanced query that properly joins and filters the data from the users, timecard_punches, and shift_assignments tables
        combined = session.query(
            users.user_id,
            func.concat(users.first_name, literal(' '), users.last_name).label('name'),
            timecard_punches.shift_assignment_id,
            timecard_punches.date_line.label('punch_date'),
            # timecard_punches.start_time.label('punch_start'),
            # timecard_punches.end_time.label('punch_end'),
            # shift_assignments.start_time.label('shift_start'),
            # shift_assignments.end_time.label('shift_end'),
            shift_assignments.cost_center_id,
            shift_assignments.earning_code_id,
            shift_assignments.pay_period_id,
            timecard_punches.pay_period_id,
            func.sum(timecard_punches.total_hours).label('total_hours'),
            shift_assignments.comments.label('shift_comments'),
            (
                func.timestampdiff(
                    literal_column('SECOND'),
                    shift_assignments.start_time,
                    shift_assignments.end_time
                ) / 3600.0
            ).label('scheduled_shift_hours')
        ).join(
            timecard_punches, users.user_id == timecard_punches.user_id
        ).join(
            shift_assignments,
            and_(
                users.user_id == shift_assignments.user_id,
                timecard_punches.date_line == shift_assignments.date_line
            )
        ).filter(
            users.disabled == 'false',
            timecard_punches.date_line >= cutoff_date
        ).group_by(
            users.user_id,
            users.first_name,
            users.last_name,
            timecard_punches.shift_assignment_id,
            timecard_punches.date_line,
            timecard_punches.pay_period_id,
            timecard_punches.earning_code_id,
            shift_assignments.cost_center_id,
            # timecard_punches.start_time,
            # timecard_punches.end_time,
            # shift_assignments.start_time,
            # shift_assignments.end_time,
            # shift_assignments.comments
        ).order_by(
            shift_assignments.start_time.asc()
        ).all()

        #proper formatting to make it easier to work with the combined data 
        formatted_combined = [
            {
                # 'user_id': r.user_id,
                'name': r.name,
                # 'shift_assgnment_id': r.shift_assignment_id,
                'date': r.punch_date.strftime('%Y-%m-%d') if r.punch_date else None,
                # 'punch_start': r.punch_start.strftime('%Y-%m-%d %H:%M:%S') if r.punch_start else None,
                # 'punch_end': r.punch_end.strftime('%Y-%m-%d %H:%M:%S') if r.punch_end else None,
                # 'shift_start': r.shift_start.strftime('%Y-%m-%d %H:%M:%S') if r.shift_start else None,
                # 'shift_end': r.shift_end.strftime('%Y-%m-%d %H:%M:%S') if r.shift_end else None,
                # 'earning_code_id': r.earning_code_id if hasattr(r, 'earning_code_id') else None,
                # 'cost_center_id': r.cost_center_id if hasattr(r, 'cost_center_id') else None,
                'pay_period_id': r.pay_period_id if hasattr(r, 'cost_center_id') else None,
                'total_hours': float(r.total_hours) if r.total_hours else 0.0,
                'scheduled_shift_hours': float(r.scheduled_shift_hours) if r.scheduled_shift_hours else 0.0,
                'discrepancy': float(r.scheduled_shift_hours) - float(r.total_hours)
                   if r.scheduled_shift_hours and r.total_hours else None,

                # 'comments': r.shift_comments
            }
            for r in combined
        ]

        #formatting the discrepancies data so that it is easier to work with and better laid out 

        #initalizes and saves the cache to avoid re-querying the database unnecessarily
        _daily_cache['formatted'] = formatted_combined
        _daily_cache['date'] = today

        save_cache(_daily_cache)

    else:
        print(f"✅ Using cached data for {today}...")

    #returns the formatted combined data and the discrepacies from the cache
    return _daily_cache['formatted'], _daily_cache['discrepancies']



def get_formatted_combined_df():
    """
    Returns the formatted combined punch and shift data as a pandas DataFrame.
    """
    formatted, _ = get_data()
    df = pd.DataFrame(formatted)

    # Ensure 'date' is datetime for filtering
    # if not df.empty:
    #     df['date'] = pd.to_datetime(df['date'], errors='coerce')
    #     df['punch_start'] = pd.to_datetime(df['punch_start'], errors='coerce')
    #     df['punch_end'] = pd.to_datetime(df['punch_end'], errors='coerce')
    #     df['shift_start'] = pd.to_datetime(df['shift_start'], errors='coerce')
    #     df['shift_end'] = pd.to_datetime(df['shift_end'], errors='coerce')

    return df


# Now you can work with formatted and discrepancies as neede
# print(get_formatted_combined_df())

"""
This files purpose is to complete the schema and initalization of the important database tables for Automation of Payroll. Allowing for easy querying and data searching through 
the necessary data. 
"""
    