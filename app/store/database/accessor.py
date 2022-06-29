from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# an Engine, which the Session will use for connection
# resources
engine = create_engine('postgresql+psycopg2://igkyezeo:nrzV9tYWcAMR2mHBPEfGWBP5li0osjsL@abul.db.elephantsql.com/igkyezeo')

# create session and add objects
with Session(engine) as session:
    session.add(some_object)
    session.add(some_other_object)
    session.commit()