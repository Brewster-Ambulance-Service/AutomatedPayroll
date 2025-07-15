from sqlalchemy import Column, Integer, String, DateTime, Date, CHAR, Numeric, Text, ForeignKey, create_engine, func, literal, and_
from sqlalchemy.orm import declarative_base, sessionmaker
from enum import Enum as PyEnum
from sqlalchemy.types import Enum as SQLEnum
from datetime import date, timedelta

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
    type = Column(String(40))
    deleted = Column(CHAR(1))
    user_id = Column(Integer, ForeignKey('user_id'))
    pay_period_id = Column(Integer)
    total_hours = Column(Numeric(10,2))
    shift_assignment_id = Column(Integer, ForeignKey('sched_template_shift_assignments.id'))

    def __repr__(self):
        return (f"<PayrollArchiveTimecardPunches(id={self.id}, date_line={self.date_line}, "
            f"start_time={self.start_time}, end_time={self.end_time}, type='{self.type}', "
            f"deleted='{self.deleted}', user_id={self.user_id}, pay_period_id={self.pay_period_id}, "
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
    punchout_ts = Column(Integer)
    punchin_early = Column(Integer)
    punchin_late = Column(Integer)
    punchout_early = Column(Integer)
    punchout_late = Column(Integer)
    punchin_form_incomplete = Column(Integer)
    punchout_form_incomplete = Column(Integer)

    def __repr__(self):
        return (f"<punch_discrepancies(id={self.id}, user_id={self.user_id}, timesheet_id={self.timesheet_id}, "
                f"shift_assignment_id={self.shift_assignment_id}, punchout_ts={self.punchout_ts}, "
                f"punchin_early={self.punchin_early}, punchin_late={self.punchin_late}, "
                f"punchout_early={self.punchout_early}, punchout_late={self.punchout_late}, "
                f"punchin_form_incomplete={self.punchin_form_incomplete}, "
                f"punchout_form_incomplete={self.punchout_form_incomplete})>")

#enum class for the false and true values for the disabled column as specified in the data dictionary
class statusEnum(PyEnum):
    true = 'deactive'
    false = 'active'

class users(Base):
    """
    Mapping for the users table from the SQL database, with the relevant variable names that we will be using from the table
    ready to be loaded with the Schema. 
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    disabled = Column(SQLEnum(statusEnum), default=statusEnum.false, nullable=False)
    deactivated = Column(Integer)
    termination_date = Column(CHAR)
    first_name = Column(String)
    last_name = Column(String)

    def __repr__(self):
     return (f"<User(user_id={self.user_id}, name='{self.first_name} {self.last_name}', "
             f"disabled={self.disabled.name}, deactivated={self.deactivated}, "
             f"termination_date={self.termination_date})>")

    

#cutsoff the data results to only the last 60 days to avoid pulling too much data and slowing down the query
cutoff_date = date.today() - timedelta(days=60)

"""
Querying the database to get the combined data from users, timecard_punches, and shift_assignments tables.
This query retrieves user information, punch details, shift assignments, and calculates total hours worked for each user in the last 60 days.
"""
combined = session.query(
    users.user_id,
    func.concat(users.first_name, literal(' '), users.last_name).label('name'),
    timecard_punches.shift_assignment_id,
    timecard_punches.date_line.label('punch_date'),
    timecard_punches.start_time.label('punch_start'),
    timecard_punches.end_time.label('punch_end'),
    shift_assignments.start_time.label('shift_start'),
    shift_assignments.end_time.label('shift_end'),
    func.sum(timecard_punches.total_hours).label('total_hours'),
    shift_assignments.comments.label('shift_comments')
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
    timecard_punches.date_line >= cutoff_date  # ✅ Filter added here
).group_by(
    users.user_id,
    users.first_name,
    users.last_name,
    timecard_punches.shift_assignment_id,
    timecard_punches.date_line,
    timecard_punches.start_time,
    timecard_punches.end_time,
    shift_assignments.start_time,
    shift_assignments.end_time,
    shift_assignments.comments
).all()
"""
formats the punch data into a more readable format, converting dates and times to strings and handling null values.
This is useful for displaying the data in a user-friendly manner, such as in a report or a user interface.
"""
formatted_combined = [
    {
        'user_id': r.user_id,
        'name': r.name,
        'shift_assignment_id': r.shift_assignment_id,
        'date': r.punch_date.strftime('%Y-%m-%d') if r.punch_date else None,
        'punch_start': r.punch_start.strftime('%Y-%m-%d %H:%M:%S') if r.punch_start else None,
        'punch_end': r.punch_end.strftime('%Y-%m-%d %H:%M:%S') if r.punch_end else None,
        'shift_start': r.shift_start.strftime('%Y-%m-%d %H:%M:%S') if r.shift_start else None,
        'shift_end': r.shift_end.strftime('%Y-%m-%d %H:%M:%S') if r.shift_end else None,
        'total_hours': float(r.total_hours) if r.total_hours else 0.0,
        'comments': r.shift_comments
    }
    for r in combined
]
# Uncomment the following lines to print the formatted results
# for a in formatted_combined:
#     print(a)
def get_formatted_combined():
    """
    Returns the formatted combined data for payroll processing.
    This function can be used to retrieve the processed data for further operations or reporting.
    """
    return formatted_combined


"""
This files purpose is to complete the schema and initalization of the important database tables for Automation of Payroll. Allowing for easy querying and data searching through 
the necessary data. 
"""
    