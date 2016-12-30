#!/usr/bin/python
# -*- coding: utf-8 -*-

from telebot import TeleBot, types
import pymysql
import pymysql.cursors
import time
import re
import sys
import traceback
from datetime import date, timedelta, datetime
import threading

import cnf

testingMode = False # El modo de testing permite que sólo el admin del mismo (conf.admin_id) lo use mediante chat privado con él.
stop = False
attemps = 0 # Número de intentos de reinicio del Bot REALIZADOS tras una pérdida de conexión total a Internet.
maxAttemps = 25 # Número MÁXIMO de intentos de reinicio del Bot tras una pérdida de conexión total a Internet.
notifications = True # Mientras sea True, cada 5 minutos el bot comprobará si dentro de 1 hora o de 1 día hay citas programadas e informará a los creadores de estas mediante un mensaje.
notificationsCheck = 300 # Cada X segundos se comprobará si hay Citas que notificar, donde X es esta cifra.

TOKEN = cnf.TOKEN
 
bot = TeleBot(TOKEN)

def listener(messages):

    if stop:
        print("BOT APAGADO")
        sys.exit()

    for m in messages:
        actText = m.text
        chat_id = m.chat.id
        from_id = m.from_user.id
        if m.chat.type == "private":
            if m.content_type == "text":
                print('(' + str(time.strftime('%d/%m/%Y %H:%M')) + ')[' + str(chat_id) + ']: ' + str(actText.encode('ascii', 'backslashreplace'))[2:-1])
            else:
                print('(' + str(time.strftime('%d/%m/%Y %H:%M')) + ')[' + str(chat_id) + ']: ' + "\""+m.content_type+"\"")
        else:
            if m.content_type == "text":
                print('(' + str(time.strftime('%d/%m/%Y %H:%M')) + '){' + str(chat_id) + '}[' + str(from_id) + ']: ' + str(actText.encode('ascii', 'backslashreplace'))[2:-1])
            else:
                print('(' + str(time.strftime('%d/%m/%Y %H:%M')) + '){' + str(chat_id) + '}[' + str(from_id) + ']: ' + "\""+m.content_type+"\"")
 
bot.set_update_listener(listener)

connection = None

def database_connection():
            global connection
            connection = pymysql.connect(host=cnf.mysql['host'],
                                            user=cnf.mysql['user'],
                                            password=cnf.mysql['password'],
                                            db=cnf.mysql['db'],
                                            charset=cnf.mysql['charset'],
                                            cursorclass=pymysql.cursors.DictCursor)

def testing(message):
    chat_id = message.chat.id
    if chat_id != cnf.admin_id and testingMode == True:
        if message.from_user.username:
            bot.send_message(chat_id, u'\U0001F6B7'+' ¡Lo siento @' + message.from_user.username + ', ahora mismo estoy mejorando el bot! Estará disponible en breve (:')
        else:
            bot.send_message(chat_id, u'\U0001F6B7'+' ¡Lo siento ' + message.from_user.first_name + ', ahora mismo estoy mejorando el bot! Estará disponible en breve (:')
        return False
    else:
        return True

def run_notifications():

    def check_alarmas():
        if notifications:
            #print('Comprobando alarmas...')
            alarmaHora()
            #print('alarmaHora comprobadas')
            alarmaDia()
            #print('alarmaDia comprobadas')

        t = threading.Timer(float(notificationsCheck), check_alarmas)
        t.start()

    t = threading.Timer(float(notificationsCheck), check_alarmas)
    t.start()

def alarmaDia():
    try:
        fechaHoy = datetime.now()
        fechaManana = fechaHoy + timedelta(days=1)
        strFechaManana = fechaManana.strftime('%Y-%m-%d')

        ids = []

        database_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `cita` WHERE DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(strFechaManana)+"', '%Y-%m-%d') AND alarmaDia=false"
            cursor.execute(sql)
            if cursor.rowcount > 0:
                row = cursor.fetchone()

                while(row):
                    if row['hora'] is None:
                        hora = ""
                    else:
                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                    if row['direccion'] is None:
                        direccion = ""
                    else:
                        direccion = str(row['direccion'])

                    if row['acompanantes'] is None:
                        acompanantes = ""
                    else:
                        acompanantes = str(row['acompanantes'])

                    if row['creador'].startswith('-'):  # Si la cita pertenece a un grupo, supergrupo o canal
                        reply = u"\U000023F0" + " <b>¡No olvidéis que tenéis programada esta cita para " + u"\U0001F4C5" + " mañana!:</b>\n\n"
                    else:                               # Si pertenece a un usuario (chat privado)
                        reply = u"\U000023F0" + " <b>¡No olvides que tienes programada esta cita para " + u"\U0001F4C5" + " mañana!:</b>\n\n"
                    reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                        "Día: <b>" + row['dia'].strftime("%d/%m/%Y") + "</b>\n"
                        "Hora: " + hora + "\n"
                        "Motivo: " + row['motivo'] + "\n"
                        "Lugar: " + row['lugar'] + "\n"
                        "Dirección: " + direccion + "\n"
                        "Interesado: " + row['interesado'] + "\n"
                        "Acompañantes: " + acompanantes + "\n"
                        )
                    bot.send_message(row['creador'], reply, parse_mode="HTML")

                    ids.append(row['id'])

                    row = cursor.fetchone()

        connection.close()

        # Ahora que hemos avisado, marcamos las Citas como avisadas
        if ids:
            database_connection()
            with connection.cursor() as cursor:
                for id in ids:
                    sql = "UPDATE cita SET alarmaDia=true WHERE id="+str(id)
                    cursor.execute(sql)
                    connection.commit()
                        
            connection.close()

    except Exception as e:
        print(str(e))

def alarmaHora():
    try:
        fechaHoy = datetime.now()
        fechaHora = fechaHoy + timedelta(hours=1)
        horaActual = fechaHoy.strftime('%H:%M')
        dentroDeUnaHora = fechaHora.strftime('%H:%M')
        strFechaHoy = fechaHoy.strftime('%Y-%m-%d')

        ids = []

        database_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `cita` WHERE DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(strFechaHoy)+"', '%Y-%m-%d') AND ( `hora` BETWEEN '"+str(horaActual)+"' AND '"+str(dentroDeUnaHora)+"' ) AND alarmaHora=false"
            cursor.execute(sql)
            if cursor.rowcount > 0:
                row = cursor.fetchone()

                while(row):
                    if row['hora'] is None:
                        hora = ""
                    else:
                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                    if row['direccion'] is None:
                        direccion = ""
                    else:
                        direccion = str(row['direccion'])

                    if row['acompanantes'] is None:
                        acompanantes = ""
                    else:
                        acompanantes = str(row['acompanantes'])

                    if row['creador'].startswith('-'):
                        reply = u"\U000023F0" + " <b>¡No olvidéis que tenéis programada esta cita " + u"\U0001F551" + " dentro de una hora!:</b>\n\n"
                    else:
                        reply = u"\U000023F0" + " <b>¡No olvides que tienes programada esta cita " + u"\U0001F551" + " dentro de una hora!:</b>\n\n"
                    reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                        "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                        "Hora: <b>" + hora + "</b>\n"
                        "Motivo: " + row['motivo'] + "\n"
                        "Lugar: " + row['lugar'] + "\n"
                        "Dirección: " + direccion + "\n"
                        "Interesado: " + row['interesado'] + "\n"
                        "Acompañantes: " + acompanantes + "\n"
                        )
                    bot.send_message(row['creador'], reply,parse_mode="HTML")

                    ids.append(row['id'])

                    row = cursor.fetchone()
                    
        connection.close()

        # Ahora que hemos avisado, marcamos las Citas como avisadas
        if ids:
            database_connection()
            with connection.cursor() as cursor:
                for id in ids:
                    sql = "UPDATE cita SET alarmaHora=true WHERE id="+str(id)
                    cursor.execute(sql)
                    connection.commit()
                        
            connection.close()

    except Exception as e:
        print(str(e))


while True:
    try:
        if stop:
            print("BOT APAGADO")
            sys.exit()

        if attemps > 0:
            print("Encendiendo Bot tras " + str(attemps) + " intentos...")
            bot.send_message(cnf.admin_id, 'Bot iniciado de nuevo tras ' + str(attemps) + ' intentos. '+u'\U0001F44D')
        else:
            print("Encendiendo Bot...")
            bot.send_message(cnf.admin_id, 'Bot iniciado de nuevo '+u'\U0001F44D')
        attemps = 0

        print("BOT INICIADO")

        run_notifications()

        # Session handler -------------
        cita_dict = {}

        class Cita:
            def __init__(self, dia):
                self.dia = dia
                self.hora = None
                self.motivo = None
                self.lugar = None
                self.direccion = None
                self.interesado = None
                self.acompanantes = None

        modificar_dict = {}

        class Modificacion:
            def __init__(self, numeroCita):
                self.numeroCita = numeroCita
                self.dato = None

        fechas_dict = {}

        class Fechas:
            def __init__(self, fecha):
                self.fecha = fecha
                self.fechaDB = None

        operation_dict = {}
        # -----------------------------
        
        @bot.message_handler(commands=['start'])
        def command_start(message):
            if testing(message):
                chat_id = message.chat.id
                if message.from_user.username:
                    from_username = message.from_user.username
                    reply = "¡Hola @"+from_username+", empezamos cuando quieras! Si no sabes por dónde empezar usa el comando /ayuda"
                else:
                    first_name = message.from_user.first_name
                    reply = "¡Hola "+first_name+", empezamos cuando quieras! Si no sabes por dónde empezar usa el comando /ayuda"
                bot.reply_to(message, reply)
    
        @bot.message_handler(commands=['ayuda'])
        def command_ayuda(message):
            if testing(message):
                chat_id = message.chat.id
                reply = ("/citashoy: Muestra todas las citas del grupo programadas para el día actual."
                    "\n\n/citassemana: Muestra todas las citas del grupo programadas para la semana actual."
                    "\n\n/citasfechas: Muestra todas las citas del grupo programadas para la fecha dada (Ejemplo: \"/citasfechas 12/04/2016\") o entre las 2 fechas dadas. (Ejemplo: \"/citasfechas 12/04/2016 a 20/04/2016\")"
                    "\n\n/citastodas: Muestra un resumen de todas las citas del grupo."
                    "\n\n/citasmostrar: Muestra una cita en concreto dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasmostrar 1\")"
                    # Personalizar los siguientes comandos para que SOLO lo puedan mostrar los admins.
                    "\n\n/citascrear: Permite crear una nueva cita."
                    "\n\n/citasmodificar: Permite modificar una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasmodificar 1\")"
                    "\n\n/citaseliminar: Permite eliminar por completo una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citaseliminar 1\")"
                    #"\n\n/citasasitir: Permite añadirte como acompañante a una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasacompañar 1\")"
                    # # # #
                    "\n\n<b>NOTA1</b>: Los comandos que requieren de algún dato adicional pueden ser pasados junto con el comando o enviando sólo el comando, en cuyo caso se te preguntará por el dato solicitado a continuación."
                    "\n\n<b>NOTA2</b>: Puedes cancelar operaciones en curso mediante el comando /cancelar ."
                    # # # #
                    "\n\n"+u"\U0001F514"+" Te enviaré un mensaje <b>el día antes</b> y <b>1 hora antes</b> de tu Cita para que no se te olvide."
                    )
                bot.send_message(chat_id, reply,parse_mode="HTML")
    
        @bot.message_handler(commands=['citasmostrar'])
        def command_citasmostrar(message):
            try:
                if testing(message): #and session(message):
                    chat_id = message.chat.id
                    text = message.text
                    cita_id = text.replace("/citasmostrar@Citas_Bot", "")
                    cita_id = cita_id.replace("/citasmostrar", "")
                    cita_id = cita_id.replace(" ", "")

                    if cita_id == "":
                        
                        msg = bot.reply_to(message, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")

                        start = time.time()
                        operation_dict[chat_id] = start

                        bot.register_next_step_handler(msg, process_mostrar_step)

                        # Si al minuto no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                        try:
                            while chat_id in operation_dict:
                                if time.time() - operation_dict[chat_id] > 60:
                                    if chat_id in operation_dict:
                                        del operation_dict[chat_id]
                                    bot.reply_to(message, "Operación cancelada.")
                                    break
                        except Exception as e:
                            pass
                        #time.sleep(60)
                        #if (chat_id in operation_dict): # Si sigue esta sesión activa
                        #    if operation_dict[chat_id] == start: # Si es esta sesión y no otra nueva que haya abierto el usuario después (o antes)
                        #        del operation_dict[chat_id]
                        #        bot.reply_to(message, "Operación cancelada.")

                    elif not cita_id.isdigit():
                        bot.send_message(chat_id, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: \"/citasmostrar 6\"")
                    else:
                        database_connection()
                        with connection.cursor() as cursor:
                            sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND `id`="+cita_id
                            cursor.execute(sql)
                            if cursor.rowcount > 0:
                                row = cursor.fetchone()
                                while(row):

                                    if row['hora'] is None:
                                        hora = ""
                                    else:
                                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                    if row['direccion'] is None:
                                        direccion = ""
                                    else:
                                        direccion = str(row['direccion'])

                                    if row['acompanantes'] is None:
                                        acompanantes = ""
                                    else:
                                        acompanantes = str(row['acompanantes'])

                                    reply = ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                        "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                        "Hora: " + hora + "\n"
                                        "Motivo: " + row['motivo'] + "\n"
                                        "Lugar: " + row['lugar'] + "\n"
                                        "Dirección: " + direccion + "\n"
                                        "Interesado: " + row['interesado'] + "\n"
                                        "Acompañantes: " + acompanantes + "\n"
                                        )
                                    row = cursor.fetchone()
                                bot.send_message(chat_id, reply,parse_mode="HTML")
                            else:
                                bot.send_message(chat_id, "No hay ninguna cita con el \"Número de cita\" <b>"+str(cita_id)+"</b>.",parse_mode="HTML")
                        connection.close()
            except Exception as e:
                bot.reply_to(message, 'Algo ha salido mal al recuperar tu cita '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))

        def process_mostrar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    numeroCita = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        msg = bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_mostrar_step)
                        return

                    match = numeroCita.isdigit()

                    if not match:
                        bot.reply_to(message, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: <b>6</b>",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_mostrar_step)
                        return

                    if chat_id in operation_dict:
                        del operation_dict[chat_id]

                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND `id`="+numeroCita
                        cursor.execute(sql)
                        if cursor.rowcount > 0:
                            row = cursor.fetchone()
                            while(row):

                                if row['hora'] is None:
                                    hora = ""
                                else:
                                    hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                if row['direccion'] is None:
                                    direccion = ""
                                else:
                                    direccion = str(row['direccion'])

                                if row['acompanantes'] is None:
                                    acompanantes = ""
                                else:
                                    acompanantes = str(row['acompanantes'])

                                reply = ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                    "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                    "Hora: " + hora + "\n"
                                    "Motivo: " + row['motivo'] + "\n"
                                    "Lugar: " + row['lugar'] + "\n"
                                    "Dirección: " + direccion + "\n"
                                    "Interesado: " + row['interesado'] + "\n"
                                    "Acompañantes: " + acompanantes + "\n"
                                    )
                                row = cursor.fetchone()
                            bot.send_message(chat_id, reply,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, "No hay ninguna cita con el \"Número de cita\" <b>"+numeroCita+"</b>.",parse_mode="HTML")
                    connection.close()

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.')# \n'+str(e))

        @bot.message_handler(commands=['citashoy'])
        def command_citashoy(message):
            try:
                if testing(message): #and session(message):
                    chat_id = message.chat.id
                    text = message.text

                    fechaHoy = time.strftime('%Y-%m-%d')

                    #match = re.search('(\d){2}\/(\d){2}\/(\d){4}', text)

                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(fechaHoy)+"', '%Y-%m-%d')" # CURDATE()
                        cursor.execute(sql)
                        if cursor.rowcount > 0:
                            row = cursor.fetchone()
                            reply = "Citas programadas para hoy:\n"
                            while(row):
                                if row['hora'] is None:
                                    hora = ""
                                else:
                                    hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                if row['direccion'] is None:
                                    direccion = ""
                                else:
                                    direccion = str(row['direccion'])

                                if row['acompanantes'] is None:
                                    acompanantes = ""
                                else:
                                    acompanantes = str(row['acompanantes'])

                                reply += "----------------------\n"
                                reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                    "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                    "Hora: " + hora + "\n"
                                    "Motivo: " + row['motivo'] + "\n"
                                    "Lugar: " + row['lugar'] + "\n"
                                    "Dirección: " + direccion + "\n"
                                    "Interesado: " + row['interesado'] + "\n"
                                    "Acompañantes: " + acompanantes + "\n"
                                    )
                                row = cursor.fetchone()
                            bot.send_message(chat_id, reply,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, "No hay ninguna cita programada para hoy.")
                    connection.close()
            except Exception as e:
                bot.reply_to(message, 'Algo ha salido mal al recuperar tus citas '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))

        @bot.message_handler(commands=['citassemana'])
        def command_citassemana(message):
            try:
                if testing(message):
                    chat_id = message.chat.id
                    text = message.text

                    year = date.today().year
                    week = datetime.utcnow().isocalendar()[1]

                    d = date(year,1,1)
                    if d.weekday() > 3:
                        d = d + timedelta(7-d.weekday())
                    else:
                        d = d - timedelta(d.weekday())
                    dlt = timedelta(days = (week-1)*7)

                    firstDay = d + dlt
                    lastDay = d + dlt + timedelta(days=6)

                    database_connection()
                    with connection.cursor() as cursor:

                        if chat_id in operation_dict:
                            del operation_dict[chat_id]
                        if chat_id in fechas_dict:
                            del fechas_dict[chat_id]
                            
                        sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND ( DATE_FORMAT(`dia`, '%Y-%m-%d') BETWEEN STR_TO_DATE('"+str(firstDay)+"', '%Y-%m-%d') AND STR_TO_DATE('"+str(lastDay)+"', '%Y-%m-%d') )"

                        cursor.execute(sql)
                        if cursor.rowcount > 0:
                            row = cursor.fetchone()
                            reply = "Citas programadas para esta semana\n"
                            while(row):
                                if row['hora'] is None:
                                    hora = ""
                                else:
                                    hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                if row['direccion'] is None:
                                    direccion = ""
                                else:
                                    direccion = str(row['direccion'])

                                if row['acompanantes'] is None:
                                    acompanantes = ""
                                else:
                                    acompanantes = str(row['acompanantes'])

                                reply += "----------------------\n"
                                reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                    "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                    "Hora: " + hora + "\n"
                                    "Motivo: " + row['motivo'] + "\n"
                                    "Lugar: " + row['lugar'] + "\n"
                                    "Dirección: " + direccion + "\n"
                                    "Interesado: " + row['interesado'] + "\n"
                                    "Acompañantes: " + acompanantes + "\n"
                                    )
                                row = cursor.fetchone()
                            bot.send_message(chat_id, reply,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, "No hay ninguna cita programada para esta semana")
                                
                    connection.close()
            except Exception as e:
                bot.reply_to(message, 'Algo ha salido mal al recuperar tus citas '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))
    
        @bot.message_handler(commands=['citastodas'])
        def command_citastodas(message):
            try:
                if testing(message): #and session(message):
                    chat_id = message.chat.id
                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)
                        cursor.execute(sql)
                        if cursor.rowcount > 0:
                            reply = "Resumen de todas las citas:\n"
                            row = cursor.fetchone()
                            while(row):
                                reply += "[<b>" + str(row['id']) + "</b>](" + row['dia'].strftime("%d/%m/%Y") + ") " + row['motivo'] + "\n"
                                row = cursor.fetchone()
                            bot.send_message(chat_id, reply,parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, "No hay ninguna cita creada.")
                    connection.close()
            except Exception as e:
                bot.reply_to(message, 'Algo ha salido mal al recuperar tus citas '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))

        @bot.message_handler(commands=['citasfechas'])
        def command_citasfechas(message):
            try:
                if testing(message):
                    chat_id = message.chat.id
                    text = message.text
                    fechas = text.replace("/citasfechas@Citas_Bot ", "")
                    fechas = fechas.replace("/citasfechas ", "")
                    fechas = fechas.replace("/citasfechas@Citas_Bot", "")
                    fechas = fechas.replace("/citasfechas", "")

                    if fechas == "":
                        
                        msg = bot.reply_to(message, "¿Para qué fecha? /cancelar",parse_mode="HTML")

                        start = time.time()
                        operation_dict[chat_id] = start

                        bot.register_next_step_handler(msg, process_fecha_step)

                        # Si al minuto no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                        try:
                            while chat_id in operation_dict:
                                if time.time() - operation_dict[chat_id] > 60:
                                    if chat_id in operation_dict:
                                        del operation_dict[chat_id]
                                    bot.reply_to(message, "Operación cancelada.")
                                    break
                        except Exception as e:
                            pass

                    elif not re.search('(\d){1,2}\/(\d){1,2}\/(\d){4}( a (\d){1,2}\/(\d){1,2}\/(\d){4})?', fechas):
                        bot.send_message(chat_id, "Debes introducir una fecha (<b>"+str(time.strftime('%d/%m/%Y'))+"</b>) o dos fechas (<b>13/02/2016 a "+str(time.strftime('%d/%m/%Y'))+"</b>) con los formatos indicados.",parse_mode="HTML")
                    else:

                        database_connection()
                        with connection.cursor() as cursor:
                            if len(fechas) <= 10:

                                day = fechas.split("/",1)[0]
                                month = fechas.split("/",2)[1]
                                year = fechas.split("/",2)[2]

                                match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                                if not match:
                                    bot.send_message(chat_id, "<b>"+fechas+"</b> no es una fecha válida",parse_mode="HTML")
                                    return

                                if len(day) == 1:
                                    day = "0" + day
                                if len(month) == 1:
                                    month = "0" + month

                                fecha = year + "-" + month + "-" + day

                                sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(fecha)+"', '%Y-%m-%d')"
                            else:
                                fecha1 = fechas.split(" a ",1)[0]
                                fecha2 = fechas.split(" a ",1)[1]

                                day = fecha1.split("/",1)[0]
                                month = fecha1.split("/",2)[1]
                                year = fecha1.split("/",2)[2]

                                match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                                if not match:
                                    bot.send_message(chat_id, "<b>"+fecha1+"</b> no es una fecha válida",parse_mode="HTML")
                                    return

                                if len(day) == 1:
                                    day = "0" + day
                                if len(month) == 1:
                                    month = "0" + month

                                fechaUno = year + "-" + month + "-" + day

                                day = fecha2.split("/",1)[0]
                                month = fecha2.split("/",2)[1]
                                year = fecha2.split("/",2)[2]

                                match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                                if not match:
                                    bot.send_message(chat_id, "<b>"+fecha2+"</b> no es una fecha válida",parse_mode="HTML")
                                    return

                                if len(day) == 1:
                                    day = "0" + day
                                if len(month) == 1:
                                    month = "0" + month

                                fechaDos = year + "-" + month + "-" + day

                                sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND ( DATE_FORMAT(`dia`, '%Y-%m-%d') BETWEEN STR_TO_DATE('"+str(fechaUno)+"', '%Y-%m-%d') AND STR_TO_DATE('"+str(fechaDos)+"', '%Y-%m-%d') )"
                            cursor.execute(sql)
                            if cursor.rowcount > 0:
                                row = cursor.fetchone()
                                if len(fechas) <= 10:
                                    reply = "Citas programadas para el día: <b>" + fechas + "</b>\n"
                                else:
                                    reply = "Citas programadas entre los días: <b>" + fecha1 + "</b> y <b>" + fecha2 + "</b>\n"
                                while(row):
                                    if row['hora'] is None:
                                        hora = ""
                                    else:
                                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                    if row['direccion'] is None:
                                        direccion = ""
                                    else:
                                        direccion = str(row['direccion'])

                                    if row['acompanantes'] is None:
                                        acompanantes = ""
                                    else:
                                        acompanantes = str(row['acompanantes'])

                                    reply += "----------------------\n"
                                    reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                        "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                        "Hora: " + hora + "\n"
                                        "Motivo: " + row['motivo'] + "\n"
                                        "Lugar: " + row['lugar'] + "\n"
                                        "Dirección: " + direccion + "\n"
                                        "Interesado: " + row['interesado'] + "\n"
                                        "Acompañantes: " + acompanantes + "\n"
                                        )
                                    row = cursor.fetchone()
                                bot.send_message(chat_id, reply,parse_mode="HTML")
                            else:
                                if len(fechas) <= 10:
                                    bot.send_message(chat_id, "No hay ninguna cita programada para el día <b>" + fechas + "</b>",parse_mode="HTML")
                                else:
                                    bot.send_message(chat_id, "No hay ninguna cita programada entre los días <b>" + fecha1 + "</b> y <b>" + fecha2 + "</b>",parse_mode="HTML")
                                
                        connection.close()
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in fechas_dict:
                    del fechas_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal al recuperar tus citas '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))    \n"+str(exc_tb.tb_lineno) #exc_type, exc_obj, exc_tb = sys.exc_info()

        def process_fecha_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    fecha = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_fecha_step)
                        return

                    match = re.search('(\d){1,2}\/(\d){1,2}\/(\d){4}', fecha)

                    if not match:
                        bot.reply_to(message, "Debes introducir una fecha con el formato: <b>"+str(time.strftime('%d/%m/%Y'))+"</b>",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_fecha_step)
                        return

                    day = fecha.split("/",1)[0]
                    month = fecha.split("/",2)[1]
                    year = fecha.split("/",2)[2]

                    match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                    if not match:
                        bot.reply_to(message, "<b>"+fecha+"</b> no es una fecha válida",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_fecha_step)
                        return

                    if len(day) == 1:
                        day = "0" + day
                    if len(month) == 1:
                        month = "0" + month

                    fechaDB = year + "-" + month + "-" + day

                    fechas = Fechas(fecha)
                    fechas.fechaDB = fechaDB
                    fechas_dict[chat_id] = fechas

                    msg = bot.reply_to(message, "¿Hasta qué fecha? /cancelar (Click en /listo si sólo quieres ver las de la fecha indicada)",parse_mode="HTML")

                    bot.register_next_step_handler(msg, process_fechas_step)

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in fechas_dict:
                    del fechas_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.')# \n'+str(e))

        def process_fechas_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    fecha = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_fechas_step)
                        return

                    if fecha != "/listo":

                        match = re.search('(\d){1,2}\/(\d){1,2}\/(\d){4}', fecha)

                        if not match:
                            bot.reply_to(message, "Debes introducir una fecha con el formato: <b>"+str(time.strftime('%d/%m/%Y'))+"</b>",parse_mode="HTML")
                            msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                            bot.register_next_step_handler(msg, process_fechas_step)
                            return

                        day = fecha.split("/",1)[0]
                        month = fecha.split("/",2)[1]
                        year = fecha.split("/",2)[2]

                        match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                        if not match:
                            bot.reply_to(message, "<b>"+fecha+"</b> no es una fecha válida",parse_mode="HTML")
                            msg = bot.send_message(chat_id, "¿Para qué fecha? /cancelar",parse_mode="HTML")
                            bot.register_next_step_handler(msg, process_fechas_step)
                            return

                        if len(day) == 1:
                            day = "0" + day
                        if len(month) == 1:
                            month = "0" + month

                        fechaDB = year + "-" + month + "-" + day

                        fecha1 = fechas_dict[chat_id].fecha
                        fecha2 = fecha
                        fechaUno =fechas_dict[chat_id].fechaDB
                        fechaDos = fechaDB

                        database_connection()
                        with connection.cursor() as cursor:

                            if chat_id in operation_dict:
                                del operation_dict[chat_id]
                            if chat_id in fechas_dict:
                                del fechas_dict[chat_id]
                            
                            sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND ( DATE_FORMAT(`dia`, '%Y-%m-%d') BETWEEN STR_TO_DATE('"+str(fechaUno)+"', '%Y-%m-%d') AND STR_TO_DATE('"+str(fechaDos)+"', '%Y-%m-%d') )"

                            cursor.execute(sql)
                            if cursor.rowcount > 0:
                                row = cursor.fetchone()
                                reply = "Citas programadas entre los días: <b>" + fecha1 + "</b> y <b>" + fecha2 + "</b>\n"
                                while(row):
                                    if row['hora'] is None:
                                        hora = ""
                                    else:
                                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                    if row['direccion'] is None:
                                        direccion = ""
                                    else:
                                        direccion = str(row['direccion'])

                                    if row['acompanantes'] is None:
                                        acompanantes = ""
                                    else:
                                        acompanantes = str(row['acompanantes'])

                                    reply += "----------------------\n"
                                    reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                        "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                        "Hora: " + hora + "\n"
                                        "Motivo: " + row['motivo'] + "\n"
                                        "Lugar: " + row['lugar'] + "\n"
                                        "Dirección: " + direccion + "\n"
                                        "Interesado: " + row['interesado'] + "\n"
                                        "Acompañantes: " + acompanantes + "\n"
                                        )
                                    row = cursor.fetchone()
                                bot.send_message(chat_id, reply,parse_mode="HTML")
                            else:
                                bot.send_message(chat_id, "No hay ninguna cita programada entre los días <b>" + fecha1 + "</b> y <b>" + fecha2 + "</b>",parse_mode="HTML")
                                
                        connection.close()

                        if chat_id in operation_dict:
                            del operation_dict[chat_id]
                        if chat_id in fechas_dict:
                            del fechas_dict[chat_id]

                    else:

                        database_connection()
                        with connection.cursor() as cursor:

                            fecha = fechas_dict[chat_id].fecha
                            fechaDB = fechas_dict[chat_id].fechaDB

                            if chat_id in operation_dict:
                                del operation_dict[chat_id]
                            if chat_id in fechas_dict:
                                del fechas_dict[chat_id]
                            
                            sql = "SELECT * FROM `cita` WHERE `creador`="+str(chat_id)+" AND DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(fechaDB)+"', '%Y-%m-%d')"

                            cursor.execute(sql)
                            if cursor.rowcount > 0:
                                row = cursor.fetchone()
                                reply = "Citas programadas para el día: <b>" + fecha + "</b>\n"
                                while(row):
                                    if row['hora'] is None:
                                        hora = ""
                                    else:
                                        hora = str(row['hora']).split(":",2)[0] + ":" + str(row['hora']).split(":",2)[1]

                                    if row['direccion'] is None:
                                        direccion = ""
                                    else:
                                        direccion = str(row['direccion'])

                                    if row['acompanantes'] is None:
                                        acompanantes = ""
                                    else:
                                        acompanantes = str(row['acompanantes'])

                                    reply += "----------------------\n"
                                    reply += ("Número de cita: <b>" + str(row['id']) + "</b>\n"
                                        "Día: " + row['dia'].strftime("%d/%m/%Y") + "\n"
                                        "Hora: " + hora + "\n"
                                        "Motivo: " + row['motivo'] + "\n"
                                        "Lugar: " + row['lugar'] + "\n"
                                        "Dirección: " + direccion + "\n"
                                        "Interesado: " + row['interesado'] + "\n"
                                        "Acompañantes: " + acompanantes + "\n"
                                        )
                                    row = cursor.fetchone()
                                bot.send_message(chat_id, reply,parse_mode="HTML")
                            else:
                                bot.send_message(chat_id, "No hay ninguna cita programada para el día <b>" + fecha + "</b>",parse_mode="HTML")
                                
                        connection.close()

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in fechas_dict:
                    del fechas_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.')# \n'+str(e))

        # ------------------- START: /citascrear ----------------------- #

        @bot.message_handler(commands=['citascrear'])
        def command_citascrear(message):
            try:
                if testing(message): #and session(message):
                    chat_id = message.chat.id
                    #from_username = message.from_user.username

                    #sql = "UPDATE session SET session="+str(1)+" WHERE user="+from_id
                    #with connection.cursor() as cursor:
                    #    cursor.execute(sql)
                    #    if cursor.connection == True:
                    #        bot.send_message(chat_id, "Envíame una cita con esta plantilla (puedes copiarla para usarla):")
                    #        bot.send_message(chat_id, "Día: 00/00/0000\nHora: 00:00\nMotivo: El que sea\nLugar: El que sea\nDirección: La que sea\nInteresado: @" + from_username + "\nAcompañantes: @Este, @EsteOtro, @YEste")
                    #    else:
                    #        reply = "¡Ups! Algo ha fallado. Inténtalo de nuevo más tarde o avisa a mi creador."
                    #        bot.forward_message(chat_id, chat_id, message.id)

                    bot.send_message(chat_id, "¡Vamos a crear tu Cita! Recuerda que puedes cancelarla en cualquier momento con /cancelar o saltarte datos no obligatorios con /saltar",parse_mode="HTML")
                    msg = bot.reply_to(message, "¿Para qué <b>fecha</b>?",parse_mode="HTML")

                    operation_dict[chat_id] = time.time()

                    bot.register_next_step_handler(msg, process_dia_step)

                    # Si a los 5 minutos no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                    try:
                        while chat_id in operation_dict:
                            if time.time() - operation_dict[chat_id] > 360:
                                if chat_id in operation_dict:
                                    del operation_dict[chat_id]
                                if chat_id in cita_dict:
                                    del cita_dict[chat_id]
                                bot.reply_to(message, "Operación cancelada.")
                                break
                            #time.sleep(1)
                    except Exception as e:
                        pass
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e)

        def process_dia_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    dia = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, "¿Para qué <b>fecha</b>?",parse_mode="HTML")
                        bot.register_next_step_handler(message, process_dia_step)
                        return

                    match = re.search('(\d){1,2}\/(\d){1,2}\/(\d){4}', dia)

                    if not match:
                        bot.reply_to(message, "Debes introducir una fecha válida con el formato: " + str(time.strftime('%d/%m/%Y')))
                        bot.send_message(chat_id, "¿Para qué <b>fecha</b>?",parse_mode="HTML")
                        bot.register_next_step_handler(message, process_dia_step)
                        return

                    day = dia.split("/",1)[0]
                    month = dia.split("/",2)[1]
                    year = dia.split("/",2)[2]

                    match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                    if len(day) == 1:
                        day = "0" + day
                    if len(month) == 1:
                        month = "0" + month

                    dia = day + "/" + month + "/" + year

                    if not match:
                        bot.reply_to(message,"<b>" + dia + "</b> no es una fecha válida.",parse_mode="HTML")
                        bot.send_message(chat_id, "¿Para qué <b>fecha</b>?",parse_mode="HTML")
                        bot.register_next_step_handler(message, process_dia_step)
                        return

                    cita = Cita(dia)
                    cita_dict[chat_id] = cita

                    msg = bot.reply_to(message, '¿A qué <b>hora</b>? /saltar',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_hora_step)
                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622')# \n'+str(e))

        def process_hora_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    hora = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿A qué <b>hora</b>? /saltar',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_hora_step)
                        return

                    if hora != "/saltar" and hora != "/saltar@Citas_Bot":

                        match = re.search('(\d){1,2}:(\d){1,2}', hora)
                    
                        if not match:
                            bot.reply_to(message, "Debes introducir una hora válida con el formato: " + str(time.strftime('%H:%M')))
                            bot.send_message(chat_id, '¿A qué <b>hora</b>? /saltar',parse_mode="HTML")
                            bot.register_next_step_handler(message, process_hora_step)
                            return

                        horas = hora.split(":",1)[0]
                        minutos = hora.split(":",1)[1]

                        match = int(horas) <= 24 and int(horas) >= 0 and int(minutos) <= 59 and int(minutos) >= 0

                        if len(horas) == 1:
                            horas = "0" + horas
                        if len(minutos) == 1:
                            minutos = "0" + minutos

                        hora = horas + ":" + minutos

                        if not match:
                            bot.reply_to(message, "<b>" + hora + "</b> no es una hora válida.",parse_mode="HTML")
                            bot.send_message(chat_id, '¿A qué <b>hora</b>? /saltar',parse_mode="HTML")
                            bot.register_next_step_handler(message, process_hora_step)
                            return

                        cita = cita_dict[chat_id]
                        cita.hora = hora

                        msg = bot.reply_to(message, '¿Cuál es el <b>motivo</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_motivo_step)

                    else:

                        msg = bot.reply_to(message, '¿Cuál es el <b>motivo</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_motivo_step)

                    #bot.send_message(chat_id, "De acuerdo, tu Cita es el día "+cita.dia+" a las "+cita.hora)
                    #del operation_dict[chat_id]
                    #del cita_dict[chat_id]
                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e))

        def process_motivo_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    motivo = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿Cuál es el <b>motivo</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_motivo_step)
                        return

                    match = len(motivo) <= 45

                    if not match:
                        bot.reply_to(message, "El motivo no puede ser mayor de 45 caracteres.")
                        bot.send_message(chat_id, '¿Cuál es el <b>motivo</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_motivo_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.motivo = motivo

                    msg = bot.reply_to(message, '¿En qué <b>lugar</b>?',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_lugar_step)

                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622')# \n'+str(e))

        def process_lugar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    lugar = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿En qué <b>lugar</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_lugar_step)
                        return

                    match = len(lugar) <= 50

                    if not match:
                        bot.reply_to(message, "El lugar no puede ser mayor de 50 caracteres.")
                        bot.send_message(chat_id, '¿En qué <b>lugar</b>?',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_lugar_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.lugar = lugar

                    msg = bot.reply_to(message, '¿Cuál es la <b>dirección</b>? /saltar',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_direccion_step)
                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e))

        def process_direccion_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    direccion = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿Cuál es la <b>dirección</b>? /saltar',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_direccion_step)
                        return

                    if direccion != "/saltar" and direccion != "/saltar@Citas_Bot":

                        match = len(direccion) <= 100

                        if not match:
                            bot.reply_to(message, "El lugar no puede ser mayor de 100 caracteres.")
                            bot.send_message(chat_id, '¿Cuál es la <b>dirección</b>? /saltar',parse_mode="HTML")
                            bot.register_next_step_handler(message, process_direccion_step)
                            return

                        cita = cita_dict[chat_id]
                        cita.direccion = direccion

                        msg = bot.reply_to(message, '¿Quién es el <b>interesado</b>?',parse_mode="HTML") # /yo
                        bot.register_next_step_handler(msg, process_interesado_step)

                    else:

                        msg = bot.reply_to(message, '¿Quién es el <b>interesado</b>?',parse_mode="HTML") # /yo
                        bot.register_next_step_handler(msg, process_interesado_step)

                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e))

        def process_interesado_step(message):
            try:
                chat_id = message.chat.id
                #from_username = message.from_user.username
                if chat_id in operation_dict:
                
                    interesado = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿Quién es el <b>interesado</b>?',parse_mode="HTML") # /yo
                        bot.register_next_step_handler(message, process_interesado_step)
                        return

                    #if interesado != "/yo":

                    match = len(interesado) <= 45

                    if not match:
                        bot.reply_to(message, "El interesado no puede ser mayor de 45 caracteres.")
                        bot.send_message(chat_id, '¿Quién es el <b>interesado</b>?',parse_mode="HTML") # /yo
                        bot.register_next_step_handler(message, process_interesado_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.interesado = interesado

                    msg = bot.reply_to(message, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_acompanantes_step)

                    #else:

                    #    cita = cita_dict[chat_id]
                    #    cita.interesado = "@" + from_username

                    #    msg = bot.reply_to(message, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                    #    bot.register_next_step_handler(msg, process_acompanantes_step)

                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e))

        def process_acompanantes_step(message):
            try:
                chat_id = message.chat.id
                #from_id = message.from_user.id
                if chat_id in operation_dict:
                
                    acompanantes = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_acompanantes_step)
                        return

                    if acompanantes != "/saltar" and acompanantes != "/saltar@Citas_Bot":

                        match = len(acompanantes) <= 100

                        if not match:
                            bot.reply_to(message, "Los acompañantes no pueden ser mayor de 100 caracteres.")
                            bot.send_message(chat_id, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                            bot.register_next_step_handler(message, process_acompanantes_step)
                            return

                        cita = cita_dict[chat_id]
                        cita.acompanantes = acompanantes

                        if not isinstance(cita.motivo, str):
                            cita.motivo = cita.motivo.decode('utf-8')

                        if not isinstance(cita.lugar, str):
                            cita.lugar = cita.lugar.decode('utf-8')

                        if not isinstance(cita.interesado, str):
                            cita.interesado = cita.interesado.decode('utf-8')

                        sql = "INSERT INTO cita (dia, "
                    
                        if cita.hora is None:
                            sql += "motivo, lugar, "
                        else:
                            sql += "hora, motivo, lugar, "

                        if cita.direccion is None:
                            sql += "interesado, "
                        else:
                            sql += "direccion, interesado, "

                        dia = cita.dia[-4:] + "-" + cita.dia[3:5] + "-" + cita.dia[0:2]

                        if cita.acompanantes is None:
                            sql += "creador, alarmaDia, alarmaHora) VALUES ('" + dia
                        else:
                            sql += "acompanantes, creador, alarmaDia, alarmaHora) VALUES ('" + dia


                        if cita.hora is None:
                            sql += "', '" + cita.motivo + "', '" + cita.lugar
                        else:
                            sql += "', '" + cita.hora + "', '" + cita.motivo + "', '" + cita.lugar

                        if cita.direccion is None:
                            sql += "', '" + cita.interesado
                        else:
                            if not isinstance(cita.direccion, str):
                                cita.direccion = cita.direccion.decode('utf-8')
                            sql += "', '" + cita.direccion + "', '" + cita.interesado

                        if cita.acompanantes is None:
                            sql += "',  '" + str(chat_id) + "', false, false)"
                        else:
                            if not isinstance(cita.acompanantes, str):
                                cita.acompanantes = cita.acompanantes.decode('utf-8')
                            sql += "', '" + cita.acompanantes + "',  '" + str(chat_id) + "', false, false)"

                        if chat_id in operation_dict:
                            del operation_dict[chat_id]
                        if chat_id in cita_dict:
                            del cita_dict[chat_id]

                        database_connection()
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            id = cursor.lastrowid
                            connection.commit()

                            reply = "¡Hecho!, tu Cita se ha creado con el \"Número de cita\" <b>"+str(id)+"</b>"

                        bot.send_message(chat_id, reply,parse_mode="HTML")
                        connection.close()

                    else:

                        cita = cita_dict[chat_id]

                        if not isinstance(cita.motivo, str):
                            cita.motivo = cita.motivo.decode('utf-8')

                        if not isinstance(cita.lugar, str):
                            cita.lugar = cita.lugar.decode('utf-8')

                        if not isinstance(cita.interesado, str):
                            cita.interesado = cita.interesado.decode('utf-8')

                        sql = "INSERT INTO cita (dia, "
                    
                        if cita.hora is None:
                            sql += "motivo, lugar, "
                        else:
                            sql += "hora, motivo, lugar, "

                        if cita.direccion is None:
                            sql += "interesado, "
                        else:
                            sql += "direccion, interesado, "

                        dia = cita.dia[-4:] + "-" + cita.dia[3:5] + "-" + cita.dia[0:2]

                        if cita.acompanantes is None:
                            sql += "creador, alarmaDia, alarmaHora) VALUES ('" + dia
                        else:
                            sql += "acompanantes, creador, alarmaDia, alarmaHora) VALUES ('" + dia


                        if cita.hora is None:
                            sql += "', '" + cita.motivo + "', '" +  cita.lugar
                        else:
                            sql += "', '" +  cita.hora + "', '" + cita.motivo + "', '" +  cita.lugar

                        if cita.direccion is None:
                            sql += "', '" +  cita.interesado
                        else:
                            if not isinstance(cita.direccion, str):
                                cita.direccion = cita.direccion.decode('utf-8')
                            sql += "', '" +  cita.direccion + "', '" +  cita.interesado

                        if cita.acompanantes is None:
                            sql += "',  '" + str(chat_id) + "', false, false)"
                        else:
                            if not isinstance(cita.acompanantes, str):
                                cita.acompanantes = cita.acompanantes.decode('utf-8')
                            sql += "', '" +  cita.acompanantes + "',  '" + str(chat_id) + "', false, false)"

                        if chat_id in operation_dict:
                            del operation_dict[chat_id]
                        if chat_id in cita_dict:
                            del cita_dict[chat_id]

                        database_connection()
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            id = cursor.lastrowid
                            connection.commit()

                            reply = "¡Hecho!, tu Cita se ha creado con el \"Número de cita\" <b>"+str(id)+"</b>"

                        bot.send_message(chat_id, reply,parse_mode="HTML")
                        connection.close()
                    
                else:
                    return

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                    if chat_id in cita_dict:
                        del cita_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.')# \n'+str(e)+"\nQuery: "+sql)

        # ------------------- END: /citascrear ----------------------- #

        # ------------------- START: /citasmodificar ----------------------- #

        @bot.message_handler(commands=['citasmodificar'])
        def command_citasmodificar(message):
            try:
                if testing(message):
                    chat_id = message.chat.id
                    text = message.text
                    cita_id = text.replace("/citasmodificar@Citas_Bot", "")
                    cita_id = cita_id.replace("/citasmodificar", "")
                    cita_id = cita_id.replace(" ", "")

                    if cita_id == "":
                        
                        msg = bot.reply_to(message, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")

                        operation_dict[chat_id] = time.time()

                        bot.register_next_step_handler(msg, process_modificar_step)

                        # Si a los 2 minutos no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                        try:
                            while chat_id in operation_dict:
                                if time.time() - operation_dict[chat_id] > 120:
                                    if chat_id in operation_dict:
                                        del operation_dict[chat_id]
                                    if chat_id in modificar_dict:
                                        del modificar_dict[chat_id]
                                    markup = types.ReplyKeyboardHide(selective=False)
                                    bot.reply_to(message, "Operación cancelada.", reply_markup=markup)
                                    break
                                #time.sleep(1)
                        except Exception as e:
                            pass

                    elif not cita_id.isdigit():
                        bot.send_message(chat_id, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: \"/citasmodificar 6\"")
                    else:

                        # Primero comprobamos que exista una cita con ese ID
                        database_connection()
                        with connection.cursor() as cursor:
                            sql = "SELECT EXISTS(SELECT 1 FROM cita WHERE `creador`="+str(chat_id)+" AND id ='" + str(cita_id) + "' LIMIT 1)"
                            cursor.execute(sql)
                            row = cursor.fetchone()
                            connection.close()
                            #bot.send_message(chat_id, "Aquí tienes: " + str(row.get("EXISTS(SELECT 1 FROM cita WHERE id ='"+str(cita_id)+"' LIMIT 1)")) )
                            if row.get("EXISTS(SELECT 1 FROM cita WHERE `creador`="+str(chat_id)+" AND id ='"+str(cita_id)+"' LIMIT 1)") == 1:

                                modificacion = Modificacion(cita_id)
                                modificar_dict[chat_id] = modificacion

                                markup = types.ReplyKeyboardMarkup()
                                itembtn1 = types.KeyboardButton('Día')
                                itembtn2 = types.KeyboardButton('Hora')
                                itembtn3 = types.KeyboardButton('Motivo')
                                itembtn4 = types.KeyboardButton('Lugar')
                                itembtn5 = types.KeyboardButton('Dirección')
                                itembtn6 = types.KeyboardButton('Interesado')
                                itembtn7 = types.KeyboardButton('Acompañantes')
                                markup.row(itembtn1, itembtn2)
                                markup.row(itembtn3, itembtn4)
                                markup.row(itembtn5, itembtn6)
                                markup.row(itembtn7)
                        
                                msg = bot.reply_to(message, "¿Qué dato quieres modificar de la cita? /cancelar", reply_markup=markup)

                                operation_dict[chat_id] = time.time()

                                bot.register_next_step_handler(msg, process_dato_modificar_step)

                                # Si a los 2 minutos no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                                try:
                                    while chat_id in operation_dict:
                                        if time.time() - operation_dict[chat_id] > 120:
                                            if chat_id in operation_dict:
                                                del operation_dict[chat_id]
                                            if chat_id in modificar_dict:
                                                del modificar_dict[chat_id]
                                            markup = types.ReplyKeyboardHide(selective=False)
                                            bot.reply_to(message, "Operación cancelada.", reply_markup=markup)
                                            break
                                        #time.sleep(1)
                                except Exception as e:
                                    pass

                            else:
                                if chat_id in operation_dict:
                                    del operation_dict[chat_id]
                                if chat_id in modificar_dict:
                                    del modificar_dict[chat_id]
                                bot.send_message(chat_id, "No hay ninguna cita con el \"Número de cita\" <b>"+str(cita_id)+"</b>.",parse_mode="HTML")

            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in modificar_dict:
                    del modificar_dict[chat_id]
                markup = types.ReplyKeyboardHide(selective=False)
                bot.reply_to(message, 'Algo ha salido mal al modificar tu cita '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador', reply_markup=markup)# \n'+str(e))

        def process_modificar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    numeroCita = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        msg = bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_modificar_step)
                        return

                    match = numeroCita.isdigit()

                    if not match:
                        bot.reply_to(message, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: <b>6</b>",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(msg, process_modificar_step)
                        return

                    # Primero comprobamos que exista una cita con ese ID
                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "SELECT EXISTS(SELECT 1 FROM cita WHERE `creador`="+str(chat_id)+" AND id ='" + str(numeroCita) + "' LIMIT 1)"
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        connection.close()
                        #bot.send_message(chat_id, "Aquí tienes: " + str(row.get("EXISTS(SELECT 1 FROM cita WHERE id ='"+str(cita_id)+"' LIMIT 1)")) )
                        if row.get("EXISTS(SELECT 1 FROM cita WHERE `creador`="+str(chat_id)+" AND id ='"+str(numeroCita)+"' LIMIT 1)") == 1:

                            #if chat_id in operation_dict:
                            #    del operation_dict[chat_id]
                            modificacion = Modificacion(numeroCita)
                            modificar_dict[chat_id] = modificacion

                            markup = types.ReplyKeyboardMarkup()
                            itembtn1 = types.KeyboardButton('Día')
                            itembtn2 = types.KeyboardButton('Hora')
                            itembtn3 = types.KeyboardButton('Motivo')
                            itembtn4 = types.KeyboardButton('Lugar')
                            itembtn5 = types.KeyboardButton('Dirección')
                            itembtn6 = types.KeyboardButton('Interesado')
                            itembtn7 = types.KeyboardButton('Acompañantes')
                            markup.row(itembtn1, itembtn2)
                            markup.row(itembtn3, itembtn4)
                            markup.row(itembtn5, itembtn6)
                            markup.row(itembtn7)

                            msg = bot.reply_to(message, "¿Qué dato quieres modificar de la cita? /cancelar", reply_markup=markup)

                            bot.register_next_step_handler(msg, process_dato_modificar_step)

                        else:
                            if chat_id in operation_dict:
                                del operation_dict[chat_id]
                            if chat_id in modificar_dict:
                                del modificar_dict[chat_id]
                            bot.send_message(chat_id, "No hay ninguna cita con el \"Número de cita\" <b>"+str(numeroCita)+"</b>.",parse_mode="HTML")
                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in modificar_dict:
                    del modificar_dict[chat_id]
                markup = types.ReplyKeyboardHide(selective=False)
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.', reply_markup=markup)# \n'+str(e))

        def process_dato_modificar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    dato = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Por favor, selecciona una opción del <b>teclado de botones</b>.",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "¿Qué dato quieres modificar de la cita? /cancelar")
                        bot.register_next_step_handler(msg, process_dato_modificar_step)
                        return

                    match = dato == "Día" or dato == "Hora" or dato == "Motivo" or dato == "Lugar" or dato == "Dirección" or dato == "Interesado" or dato == "Acompañantes"

                    if not match:
                        bot.reply_to(message, "Por favor, selecciona una opción del <b>teclado de botones</b>.",parse_mode="HTML")
                        msg = bot.send_message(chat_id, "¿Qué dato quieres modificar de la cita? /cancelar")
                        bot.register_next_step_handler(msg, process_dato_modificar_step)
                        return

                    #if chat_id in operation_dict:
                    #    del operation_dict[chat_id]

                    if dato == "Día":
                        dato = "dia"

                    elif dato == "Hora":
                        dato = "hora"

                    elif dato == "Motivo":
                        dato = "motivo"

                    elif dato == "Lugar":
                        dato = "lugar"

                    elif dato == "Dirección":
                        dato = "direccion"

                    elif dato == "Interesado":
                        dato = "interesado"

                    elif dato == "Acompañantes":
                        dato = "acompanantes"

                    modificacion = modificar_dict[chat_id]
                    modificacion.dato = dato

                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "SELECT " + dato + " FROM `cita` WHERE `id`="+str(modificacion.numeroCita)+" AND `creador`="+str(chat_id)

                        #if chat_id in modificar_dict:
                        #    del modificar_dict[chat_id]

                        cursor.execute(sql)
                        for (data) in cursor:

                            datoOriginal = data[dato]

                            if datoOriginal is None:
                                datoOriginal = ""
                            else:

                                if dato == "hora":
                                    datoOriginal = str(datoOriginal).split(":",2)[0] + ":" + str(datoOriginal).split(":",2)[1]
                                if dato == "dia":
                                    datoOriginal = datoOriginal.strftime("%d/%m/%Y")

                            markup = types.ReplyKeyboardHide(selective=False)
                            bot.send_message(chat_id, "Esto es lo que hay ahora: <b>" + str(datoOriginal) + "</b>",parse_mode="HTML")

                            msg = bot.reply_to(message, "Introduce el nuevo dato: /cancelar", reply_markup=markup)

                            bot.register_next_step_handler(msg, process_accion_modificar_step)
                        
                    connection.close()

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in modificar_dict:
                    del modificar_dict[chat_id]
                markup = types.ReplyKeyboardHide(selective=False)
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.', reply_markup=markup)# \n'+str(e))

        def process_accion_modificar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    nuevoDato = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                        bot.register_next_step_handler(message, process_accion_modificar_step)
                        return

                    modificacion = modificar_dict[chat_id]
                    numeroCita = modificacion.numeroCita
                    dato = modificacion.dato

                    if dato == "dia":
                        match = re.search('(\d){1,2}\/(\d){1,2}\/(\d){4}', nuevoDato)

                        if not match:
                            bot.reply_to(message, "Debes introducir una fecha válida con el formato: " + str(time.strftime('%d/%m/%Y')))
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        match = message.content_type == "text"

                        day = nuevoDato.split("/",1)[0]
                        month = nuevoDato.split("/",2)[1]
                        year = nuevoDato.split("/",2)[2]

                        match = int(day) <= 31 and int(day) >= 1 and int(month) <= 12 and int(month) >= 1 and int(year) <= 3000 and int(year) >= 0

                        if len(day) == 1:
                            day = "0" + day
                        if len(month) == 1:
                            month = "0" + month

                        nuevoDato = day + "/" + month + "/" + year

                        if not match:
                            bot.reply_to(message,"<b>" + nuevoDato + "</b> no es una fecha válida.",parse_mode="HTML")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        nuevoDato = nuevoDato[-4:] + "-" + nuevoDato[3:5] + "-" + nuevoDato[0:2]

                    elif dato == "hora":
                        match = re.search('(\d){1,2}:(\d){1,2}', nuevoDato)
                    
                        if not match:
                            bot.reply_to(message, "Debes introducir una hora válida con el formato: " + str(time.strftime('%H:%M')))
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        horas = nuevoDato.split(":",1)[0]
                        minutos = nuevoDato.split(":",1)[1]

                        match = int(horas) <= 24 and int(horas) >= 0 and int(minutos) <= 59 and int(minutos) >= 0

                        if len(horas) == 1:
                            horas = "0" + horas
                        if len(minutos) == 1:
                            minutos = "0" + minutos

                        nuevoDato = horas + ":" + minutos

                        if not match:
                            bot.reply_to(message, "<b>" + nuevoDato + "</b> no es una hora válida.",parse_mode="HTML")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                    elif dato == "motivo":
                        match = len(nuevoDato) <= 45

                        if not match:
                            bot.reply_to(message, "El motivo no puede ser mayor de 45 caracteres.")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        if not isinstance(nuevoDato, str):
                            nuevoDato = nuevoDato.decode('utf-8')

                    elif dato == "lugar":
                        match = len(nuevoDato) <= 50

                        if not match:
                            bot.reply_to(message, "El lugar no puede ser mayor de 50 caracteres.")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        if not isinstance(nuevoDato, str):
                            nuevoDato = nuevoDato.decode('utf-8')

                    elif dato == "direccion":
                        match = len(nuevoDato) <= 100

                        if not match:
                            bot.reply_to(message, "El lugar no puede ser mayor de 100 caracteres.")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        if not isinstance(nuevoDato, str):
                            nuevoDato = nuevoDato.decode('utf-8')

                    elif dato == "interesado":
                        match = len(nuevoDato) <= 45

                        if not match:
                            bot.reply_to(message, "El interesado no puede ser mayor de 45 caracteres.")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        if not isinstance(nuevoDato, str):
                            nuevoDato = nuevoDato.decode('utf-8')

                    elif dato == "acompanantes":
                        match = len(nuevoDato) <= 100

                        if not match:
                            bot.reply_to(message, "Los acompañantes no pueden ser mayor de 100 caracteres.")
                            bot.send_message(chat_id, "Introduce el nuevo dato: /cancelar")
                            bot.register_next_step_handler(message, process_accion_modificar_step)
                            return

                        if not isinstance(nuevoDato, str):
                            nuevoDato = nuevoDato.decode('utf-8')

                    if chat_id in operation_dict:
                        del operation_dict[chat_id]
                    if chat_id in modificar_dict:
                        del modificar_dict[chat_id]

                    database_connection()
                    with connection.cursor() as cursor:
                        sql = "UPDATE cita SET "+dato+"='"+nuevoDato+"' WHERE id="+str(numeroCita)+" AND `creador`="+str(chat_id)

                        cursor.execute(sql)
                        modified = cursor.rowcount # SELECT ROW_COUNT()
                        connection.commit()
                        
                    connection.close()

                    if modified == 0:
                        reply = "No hay ninguna cita con el \"Número de cita\" <b>"+str(numeroCita)+"</b>."
                    else:
                        reply = "¡Cita modificada!"

                    bot.send_message(chat_id, reply,parse_mode="HTML")

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                if chat_id in modificar_dict:
                    del modificar_dict[chat_id]
                markup = types.ReplyKeyboardHide(selective=False)
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.', reply_markup=markup)# \n'+str(e))

        # ------------------- END: /citasmodificar ----------------------- #

        @bot.message_handler(commands=['citaseliminar'])
        def command_citaseliminar(message):
            try:
                if testing(message):
                    chat_id = message.chat.id
                    text = message.text
                    cita_id = text.replace("/citaseliminar@Citas_Bot", "")
                    cita_id = cita_id.replace("/citaseliminar", "")
                    cita_id = cita_id.replace(" ", "")

                    if cita_id == "":
                        
                        msg = bot.reply_to(message, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")

                        operation_dict[chat_id] = time.time()

                        bot.register_next_step_handler(msg, process_eliminar_step)

                        # Si al minuto no ha terminado la operación, la cancelamos y borramos los elementos de memoria
                        try:
                            while chat_id in operation_dict:
                                if time.time() - operation_dict[chat_id] > 60:
                                    if chat_id in operation_dict:
                                        del operation_dict[chat_id]
                                    bot.reply_to(message, "Operación cancelada.")
                                    break
                                #time.sleep(1)
                        except Exception as e:
                            pass

                    elif not cita_id.isdigit():
                        bot.send_message(chat_id, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: \"/citaseliminar 6\"")
                    else:
                        sql = "DELETE FROM cita WHERE `creador`="+str(chat_id)+" AND id=" + cita_id

                        database_connection()
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                            deleted = cursor.rowcount # SELECT ROW_COUNT()
                            connection.commit()
                        connection.close()

                        if deleted == 0:
                            reply = "No hay ninguna cita con el \"Número de cita\" <b>"+str(cita_id)+"</b>."
                        else:
                            reply = "¡Cita eliminada!"

                        bot.send_message(chat_id, reply,parse_mode="HTML")
            except Exception as e:
                bot.reply_to(message, 'Algo ha salido mal al eliminar tu cita '+u'\U0001F605' + ' Inténtalo de nuevo más tarde o avisa a mi creador.')# \n'+str(e))

        def process_eliminar_step(message):
            try:
                chat_id = message.chat.id
                if chat_id in operation_dict:
                
                    numeroCita = message.text

                    match = message.content_type == "text"

                    if not match:
                        bot.reply_to(message, "Eh eh, sólo texto por favor.")
                        bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(message, process_eliminar_step)
                        return

                    match = numeroCita.isdigit()

                    if not match:
                        bot.reply_to(message, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: <b>6</b>",parse_mode="HTML")
                        bot.send_message(chat_id, "Dime el <b>Número de cita</b>. /cancelar",parse_mode="HTML")
                        bot.register_next_step_handler(message, process_eliminar_step)
                        return

                    if chat_id in operation_dict:
                        del operation_dict[chat_id]

                    sql = "DELETE FROM cita WHERE id=" + numeroCita + " AND `creador`="+str(chat_id)

                    database_connection()
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        deleted = cursor.rowcount # SELECT ROW_COUNT()
                        connection.commit()
                    connection.close()

                    if deleted == 0:
                        reply = "No hay ninguna cita con el \"Número de cita\" <b>"+str(numeroCita)+"</b>."
                    else:
                        reply = "¡Cita eliminada!"

                    bot.send_message(chat_id, reply,parse_mode="HTML")

                else:
                    return
            except Exception as e:
                if chat_id in operation_dict:
                    del operation_dict[chat_id]
                bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622' + ' Si el problema persiste, por favor avisa a mi creador.')# \n'+str(e))

        @bot.message_handler(commands=['cancelar'])
        def command_cancelar(message):
            if testing(message): #and session(message):
                chat_id = message.chat.id
                #from_id = message.from_user.id

                if chat_id in cita_dict:
                    del cita_dict[chat_id]

                if chat_id in modificar_dict:
                    del modificar_dict[chat_id]

                if chat_id in fechas_dict:
                    del fechas_dict[chat_id]

                if chat_id in operation_dict:
                    del operation_dict[chat_id]

                    markup = types.ReplyKeyboardHide(selective=False)
                    bot.send_message(chat_id, "Operación cancelada.", reply_markup=markup)

        @bot.message_handler(commands=['testingmode'])
        def command_testingmode(message):
            from_id = message.from_user.id
            if from_id == cnf.admin_id:
                global testingMode
                if testingMode == True:
                    testingMode = False
                    bot.send_message(cnf.admin_id, 'testingMode DESACTIVADO '+u'\U0000274E')#\n'+str(e))
                else:
                    testingMode = True
                    bot.send_message(cnf.admin_id, 'testingMode ACTIVADO '+u'\U00002705')# \n'+str(e))

        @bot.message_handler(commands=['notifications']) # Switch notifications
        def command_testingmode(message):
            from_id = message.from_user.id
            if from_id == cnf.admin_id:
                global notifications
                if notifications == True:
                    notifications = False
                    bot.send_message(cnf.admin_id, 'notifications DESACTIVADAS '+u'\U0001F515')#\n'+str(e))
                else:
                    notifications = True
                    bot.send_message(cnf.admin_id, 'notifications ACTIVADAS '+u'\U0001F514')# \n'+str(e))
        
        @bot.message_handler(commands=['stop']) # Emergency STOP
        def command_stop(message):
            from_id = message.from_user.id
            if from_id == cnf.admin_id:
                chat_id = message.chat.id
                global stop
                stop = True

        bot.polling(none_stop=True)

    except Exception as e:
        try:
            print("He fallado! Intentando avisar al administrador por Telegram...")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            bot.send_message(cnf.admin_id, u'\U0001F4A5'+'¡Me he caído! '+u'\U0001F631\n'+str(e)+'\n'+str(exc_tb.tb_lineno))
            bot.send_message(cnf.admin_id, 'Reiniciando en 10 segundos... /stop')
            print("Reporte enviado al administrador.")
            time.sleep(10)
        except Exception as e:
            attemps = attemps + 1
            print("Oh no! No puedo contactar con el administrador! Intento número " + str(attemps) + " de reconectarme.")
            if attemps <= maxAttemps and attemps <= 10: # 10 intentos cada 10 segundos...
                print("Reiniciando en 10 segundos...")
                time.sleep(10)
            elif attemps <= maxAttemps and attemps > 5: # ...luego, el resto de intentos cada 1 minuto...
                print("Reiniciando en 1 minuto...")
                time.sleep(60)
            else: # ...tras los 10 intentos, para el Bot.
                print("Sigo sin poder reconectarme. Apagando Bot... ):")
                stop = True

    finally:
        if connection is not None:
            if connection.open:
                connection.close()
