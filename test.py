from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://igkyezeo:nrzV9tYWcAMR2mHBPEfGWBP5li0osjsL@abul.db.elephantsql.com/igkyezeo")
engine.connect()
print(engine)