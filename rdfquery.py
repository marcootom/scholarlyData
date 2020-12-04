from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
import rdflib
from gtts import gTTS
import playsound
import speech_recognition as sr
import contextlib
import os
import sys

'''Funzione che elimina gli errori sul terminale (bug della libreria gTTS)'''


@contextlib.contextmanager
def ignore_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)


'''Funzione che riproduce un audio che contiene la stringa text'''


def speak(text):
    with noalsaerr():
        ignore_stderr()
        tts = gTTS(text=text, lang='en')
        filename = 'voice.wav'
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)


'''Funzione che ascolta la frase che dice l'utente e la trasforma in stringa'''


def getAudio():
    with noalsaerr():
        ignore_stderr()
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source, 5)
            said = ""
            try:
                said = r.recognize_google(audio, language='en-US')
                print(said)
            except Exception as e:
                print("Exception: " + str(e))
        return said


# Funzione che recupera la lista delle nazioni
def listaPerTipo(tipo):
    sparql = f'''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                    SELECT ?json_data_name
                    WHERE 
                    {{
                        ?json_data_primaryId db:json_data_name ?json_data_name .
                        ?json_data_primaryId db:json_data_type ?json_data_type .
                        ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                        FILTER (lcase(str(?json_data_type)) = "{tipo.lower()}")
                    }}       
                    '''
    response = g.query(sparql)
    total = []
    for row in response:
        total.append(row.asdict()['json_data_name'].toPython())
    total = list(dict.fromkeys(total))
    total = [each_string.lower() for each_string in total]
    total.sort()
    if '' in total:
        total.remove('')
    return total

def informazioniTotali(nome):
    tipo = ''
    citazioni = ''
    pubblicazioni = ''
    sparql = f'''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_name ?json_data_type (SUM(xsd:integer(?json_data_num_citations)) AS ?totCit) (SUM(xsd:integer(?json_data_num_publications)) AS ?totPub)
                WHERE 
                {{ 
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                    ?json_data_primaryId db:json_data_num_citations ?json_data_num_citations .
                    FILTER (lcase(str(?json_data_name)) = "{nome.lower()}")
                }}
                GROUP BY ?json_data_name'''
    response = g.query(sparql)
    for row in response:
        nome = (row.asdict()['json_data_name'].toPython())
        tipo = (row.asdict()['json_data_type'].toPython())
        citazioni = (row.asdict()['totCit'].toPython())
        pubblicazioni = (row.asdict()['totPub'].toPython())
    article = 'a'
    if tipo == 'author' or tipo == 'institution':
        article = 'an'
    frasedadire = f'''{nome} is {article} {tipo}. The number of citations is {citazioni} and the number of publications is {pubblicazioni}'''
    print(frasedadire)
    speak(frasedadire)

# Questa funzione restituisce il numero di pubblicazioni relative alla nazione che riceve come parametro
def pubblicazioni_per_nome(tipo, dato, nome):
    sparql = f'''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_num_{dato}
                WHERE 
                {{
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_{dato} ?json_data_num_{dato} .
                    FILTER (regex(?json_data_type, "{tipo}")) .
                    FILTER (regex(?json_data_name, "{nome}"))
                }}       
                '''
    response = g.query(sparql)
    total = 0
    for row in response:
        total += int(row.asdict()[f'''json_data_num_{dato}'''].toPython())

    if total != 0:
        frasedadire = f'''The number of {dato} of the {tipo} {nome} is {str(total)}'''
    else:
        frasedadire = 'The question returned no results'
    print(frasedadire)
    speak(frasedadire)

def maggior_pubblicazioni(tipo, dato, ordine):
    if ordine == 'DESC':
        o = "most"
    else:
        o = 'fewest'
    sparql = f'''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_name ?json_data_type (SUM(xsd:integer(?json_data_num_{dato})) AS ?tot)
                WHERE 
                {{
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                    ?json_data_primaryId db:json_data_num_citations ?json_data_num_citations  
                    FILTER( regex(?json_data_type, "{tipo}") )
                }}
                GROUP BY ?json_data_name
                ORDER BY {ordine} (?tot) LIMIT 1                       
            '''
    #fraseDaDire = "Sorry, I can't answer this question"
    response = g.query(sparql)
    string = ''
    number = ''
    for row in response:
        string = row.asdict()['json_data_name'].toPython()
        number = row.asdict()['tot'].toPython()
    fraseDaDire = f'''The {tipo} with the {o} {dato} is {string} with {str(number)} {dato}'''
    print(fraseDaDire)
    speak(fraseDaDire)


# ---------------------Inizio Script------------------------------------

'''Parse del json in rdf'''
g = rdflib.Graph()
g.parse("db.rdf")

# Funzioni per la rimozione degli errori a terminale causati da un bug sulla libreria gTTS
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)


def py_error_handler(filename, line, function, err, fmt):
    pass


c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)


@contextmanager
def noalsaerr():
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
    yield
    asound.snd_lib_error_set_handler(None)


# Inizializzazione dell'assistente Scholarly Data
# Array contenente le categorie contenute nell'rdf
listaTipi = ["author", "conference", "country", "institution", "journal", "topic", "institute"]
# Saluto dell'assistente
print("Hi, I'm Scholarly Data! Give me a question!")
speak("Hi, I'm Scholarly Data! Give me a question!")
risp = 'yes'
first = True
while risp.__contains__('yes'):
    success = False
    if not first:
        print("Ok, give me a question!")
        speak("Ok, give me a question!")
    first = False
    # query = getAudio().lower()
    query = input()
    for t in listaTipi:
        for parola in listaPerTipo(t):
            if query.lower().__contains__(parola):
                if query.lower().__contains__('publications'):
                    pubblicazioni_per_nome(t, 'publications', parola)
                    success = True
                else:
                    if query.lower().__contains__('citations'):
                        pubblicazioni_per_nome(t, 'citations', parola)
                        success = True
                    else:
                        if query.lower() == parola:
                            informazioniTotali(parola)
                            success = True
            if success:
                break
        if query.lower().__contains__(t):
            if query.__contains__('more') or query.lower().__contains__('major') or query.lower().__contains__('most'):
                if query.lower().__contains__('publications'):
                   maggior_pubblicazioni(t, 'publications', 'DESC')
                   success = True
                if query.lower().__contains__('citations'):
                   maggior_pubblicazioni(t, 'citations', 'DESC')
                   success = True
            if query.lower().__contains__('less') or query.lower().__contains__('fewer') or query.lower().__contains__('least'):
                if query.__contains__('publications'):
                    maggior_pubblicazioni(t, 'publications', 'ASC')
                    success = True
                if query.lower().__contains__('citations'):
                    maggior_pubblicazioni(t, 'citations', 'ASC')
                    success = True
    if not success:
        print("Sorry, I can't answer this question")
        speak("Sorry, I can't answer this question")

    print("Do you want to ask me another question?")
    speak("Do you want to ask me another question?")
    # risp = getAudio()
    risp = input()
print('Ok, see you next search! Bye!')
speak('Ok, see you next search! Bye!')
