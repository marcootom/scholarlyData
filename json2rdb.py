import mysql.connector
import pandas as p
import json
import os
from sqlalchemy import create_engine

# Accesso alla cartella contenente i json
mydir = os.listdir('json')
# Ciclo sui file della cartella
for file in mydir:
    json_file = "json/" + file
    #Dal nome del file recupero il nome del nuovo db da creare
    dbname = json_file.split('.')[0].split('/')[1].lower().replace(' ', '')
    dbname = dbname.replace('(', '').replace(')', '')
    #Connessione al db
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="zoradb"
    )
    mycursor = mydb.cursor()
    mycursor.execute("CREATE DATABASE IF NOT EXISTS " + dbname)
    stringadb = 'mysql+mysqldb://root:zoradb@localhost/' + dbname

    engine = create_engine(stringadb, echo=False)

    # Apertura file json e conversione in tipo di dato json
    with open(json_file) as data_file:
        d = json.load(data_file)
        #Recupero solo i dati interessanti
        df = p.json_normalize(d, 'uniqueEntities')
        df = df.drop(['mag_id', 'isVisible'], axis=1)
        #Recupero la lista delle intestazioni di colonna
        listaCampi = df.keys()
        listaTipi = (df.groupby(['type']).sum().index.get_level_values(0).tolist())

        for row in listaTipi:
            auxiliaryDataframe = df.loc[df['type'] == row]
            auxiliaryDataframe.to_sql(name=row, con=engine, if_exists='replace', index=False)
            mycursor.execute("USE " + dbname + ";")
            mycursor.execute("ALTER TABLE " + row + " ADD COLUMN ID INT AUTO_INCREMENT PRIMARY KEY;")
