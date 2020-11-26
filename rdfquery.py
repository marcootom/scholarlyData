from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll
import rdflib
from gtts import gTTS
from googletrans import Translator
from googletrans import constants
import playsound
import speech_recognition as sr

import contextlib
import os
import sys

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


translator = Translator(service_urls=constants.DEFAULT_SERVICE_URLS)
g = rdflib.Graph()
g.parse("db.rdf")


def speak(text):
    with noalsaerr():
        ignore_stderr()
        tts = gTTS(text=text, lang='en')
        filename = 'voice.wav'
        tts.save(filename)
        playsound.playsound(filename)
        os.remove(filename)


def getAudio():
    with noalsaerr():
        ignore_stderr()
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source)
            said = ""

            try:
                said = r.recognize_google(audio, language='en-US')
                print(said)
            except Exception as e:
                print("Exception: " + str(e))
        return said


# Questa funzione restituisce il numero di pubblicazioni relative alla nazione che riceve come parametro
def pubblicazioni_per_nazione(stringname):
    sparql = '''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_num_publications
                WHERE 
                {
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                    FILTER (regex(?json_data_type, "country")) .
                    FILTER (regex(?json_data_name, "''' + stringname + '''"))
                }       
                '''
    response = g.query(sparql)
    total = 0
    for row in response:
        total += int(row.asdict()['json_data_num_publications'].toPython())

    if total != 0:
        return 'The number of publications in ' + stringname.capitalize() + ' is ' + str(total)
    else:
        return 'The question returned no results'


def maggior_pubblicazioni(stringtype):

    sparql = '''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_name ?json_data_type (SUM(xsd:integer(?json_data_num_publications)) AS ?tot)
                WHERE 
                {
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                    ?json_data_primaryId db:json_data_num_citations ?json_data_num_citations  
                    FILTER( regex(?json_data_type, "''' + stringtype + '''") )
                }
                GROUP BY ?json_data_name
                ORDER BY DESC(?tot) LIMIT 1                       
            '''
    fraseDaDire = "Sorry, I can't answer this question"
    response = g.query(sparql)
    string = ''
    number = ''
    for row in response:
        string = row.asdict()['json_data_name'].toPython()
        number = row.asdict()['tot'].toPython()
    if stringtype.capitalize() == 'Author':
        fraseDaDire = "The author who has published the most is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Conference':
        fraseDaDire = "The conference with the most publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Country':
        fraseDaDire = "The country with the most publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Institution':
        fraseDaDire = "The institution with the most publications is" + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Journal':
        fraseDaDire = "The journal with the most publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Topic':
        fraseDaDire = "The topic with the most publications is " + string + " with " + str(number) + " publications"
    speak(fraseDaDire)


def minor_pubblicazioni(stringtype):

    sparql = '''PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
                SELECT ?json_data_name ?json_data_type (SUM(xsd:integer(?json_data_num_publications)) AS ?tot)
                WHERE 
                {
                    ?json_data_primaryId db:json_data_name ?json_data_name .
                    ?json_data_primaryId db:json_data_type ?json_data_type .
                    ?json_data_primaryId db:json_data_num_publications ?json_data_num_publications .
                    ?json_data_primaryId db:json_data_num_citations ?json_data_num_citations  
                    FILTER( regex(?json_data_type, "''' + stringtype + '''") )
                }
                GROUP BY ?json_data_name
                ORDER BY ASC(?tot) LIMIT 1                       
            '''
    response = g.query(sparql)
    fraseDaDire = "Sorry, I can't answer this question"
    string = ''
    number = ''
    for row in response:
        string = row.asdict()['json_data_name'].toPython()
        number = row.asdict()['tot'].toPython()
    if stringtype.capitalize() == 'Author':
        fraseDaDire = "The least published author is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Conference':
        fraseDaDire = "The conference with the fewest publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Country':
        fraseDaDire = "The country with the fewest publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Institution':
        fraseDaDire = "The institution with the fewest publications is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Journal':
        fraseDaDire = "The least published magazine is " + string + " with " + str(number) + " publications"
    if stringtype.capitalize() == 'Topic':
        fraseDaDire = "The topic with fewer publications is " + string + " with " + str(number) + " publications"
    speak(fraseDaDire)


# ---------------------Inizio Script------------------------------------

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

speak("Hi, I'm Scholarly Data! Give me a question!")
risp = 'yes'
first = True
while risp.__contains__('yes'):
    if not first:
        speak("Ok, give me a question!")
    first = False
    query = getAudio()

    if query.__contains__('how many publications have there been in '):
        split = query.split(' ')
        string = split[7]
        if len(split) > 8:
            string = string + ' ' + split[8]
        result = pubblicazioni_per_nazione(string)
        print(result)
        speak(result)
    else:
        if query.__contains__('has published more'):
            '''Query: which ...'''
            maggior_pubblicazioni(query.split(' ')[1])
        else:
            if query.__contains__('has published less'):
                '''Query: which ...'''
                minor_pubblicazioni(query.split(' ')[1])
            else:
                speak("Sorry, I can't answer this question")

    speak("Do you want to ask me another question?")
    risp = getAudio()
speak('Ok, see you next search! Bye!')
