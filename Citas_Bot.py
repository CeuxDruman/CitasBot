#!/usr/bin/python
# -*- coding: utf-8 -*-

import telebot              # Importamos la librer?a
from telebot import types   # Y los tipos especiales de esta
#import telegram
import pymysql
import pymysql.cursors
import time
import re
import sys
import traceback
import datetime

import cnf

testingMode = True # El modo de testing permite que sólo el admin del mismo (admin_id) lo use
TOKEN = cnf.TOKEN
 
bot = telebot.TeleBot(TOKEN) # Creamos un bot con nuestro Token

def listener(messages): # Definimos un listener para los mensajes
                        # este se encargar? de realizar la acci?n que indiquemos
                        # dentro cada vez que el bot reciba un mensaje
    for m in messages:  # Por cada mensaje que recibamos...
        actText = m.text # Texto que env?a el usuario al bot
        chat_id = m.chat.id # Anotamos el ID del chat (cada chat tiene uno ?nico)
        from_id = m.from_user.id
        if m.chat.type == "private":
            print('(' + str(time.strftime('%H:%M')) + ')[' + str(chat_id) + ']: ' + actText)
        else:
            print('(' + str(time.strftime('%H:%M')) + '){' + str(chat_id) + '}[' + str(from_id) + ']: ' + actText)
 
bot.set_update_listener(listener) # Indicamos a la librer?a que lo que hemos definido antes se encargar? de los mensajes

# Connect to the database
connection = pymysql.connect(host=cnf.mysql['host'],
                                user=cnf.mysql['user'],
                                password=cnf.mysql['password'],
                                db=cnf.mysql['db'],
                                charset=cnf.mysql['charset'],
                                cursorclass=pymysql.cursors.DictCursor)

try:
    #with connection.cursor() as cursor:
    #    # Create a new record
    #    sql = "INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)"
    #    cursor.execute(sql, ('webmaster@python.org', 'very-secret'))

    ## connection is not autocommit by default. So you must commit to save
    ## your changes.
    connection.commit()

    #with connection.cursor() as cursor:
    #    # Read a single record
    #    sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
    #    cursor.execute(sql, ('webmaster@python.org',))
    #    result = cursor.fetchone()
    #    print(result)

    #session = 0

    #with connection.cursor() as cursor:
    #    sql = "SELECT session FROM `session` WHERE `user`="+m.from_user.username
    #    cursor.execute(sql)
    #    if cursor.rowcount > 0:
    #        row = cursor.fetchone()
    #        while(row):
    #            session = row['session']
    #            row = cursor.fetchone()
    #    else:
    #        sql = ("INSERT INTO session (user, session)"
				#    "VALUES (" + m.from_user.id + ", " + 0 + ")")

    #if session == 1:

    #@bot.message_handler(func=lambda m: str(m.text).startswith('Día:'))
    #def command_citascrear(message):
    #    if testing(message):
    #        chat_id = message.chat.id
    #        from_id = message.from_user.id

    #        dia = 
    #        hora = 
    #        lugar = 
    #        direccion = 
    #        interesado = 
    #        acompanantes = 

    #        sql = ("INSERT INTO cita (dia, hora, motivo, lugar, direccion, interesado, acompanantes, creador, alarmaDia, alarmaHora)"
				#"VALUES ('" + dia + "', '" + hora + "', '" + motivo + "', '" + lugar + "', '" + direccion + "', '" + interesado + "', '" + acompanantes + "',  '" + from_id + "', false, false)")
    #        with connection.cursor() as cursor:
    #            cursor.execute(sql)
    #            if cursor.connection == True:
    #                reply = "¡Cita creada!"
    #            else:
    #                reply = "¡Ups! Algo ha fallado mientras creaba tu Cita. Inténtalo de nuevo más tarde o avisa a mi creador."
    #        bot.send_message(chat_id, reply)

    #else:

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

    operation_dict = {}
    # -----------------------------
    
    @bot.message_handler(commands=['ayuda'])
    def command_ayuda(message):
        if testing(message):
            chat_id = message.chat.id
            reply = ("/citashoy: Muestra todas las citas del grupo programadas para el día actual."
			    "\n\n/citassemana: Muestra todas las citas del grupo programadas para la semana actual."
				"\n\n/citasfechas: Muestra todas las citas del grupo programadas para la fecha dada (Ejemplo: \"/citasfecha 12/04/2016\") o entre las 2 fechas dadas. (Ejemplo: \"/citasfechas 12/04/2016 a 20/04/2016\")"
				"\n\n/citastodas: Muestra un resumen de todas las citas del grupo."
				"\n\n/citasmostrar: Muestra una cita en concreto dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasmostrar 1\")"
				# Personalizar los siguientes comandos para que SOLO lo puedan mostrar los admins.
				"\n\n/citascrear: Permite crear una nueva cita."
				"\n\n/citasmodificar: Permite modificar una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasmodificar 1\")"
				"\n\n/citaseliminar: Permite eliminar por completo una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citaseliminar 1\")"
				"\n\n/citasasitir: Permite añadirte como acompañante a una cita dado el \"Número de cita\" de la misma. (Ejemplo: \"/citasacompañar 1\")"
				"\n\nPuedes cancelar operaciones en curso mediante el comando /cancelar ."
                )
            bot.send_message(chat_id, reply)
    
    @bot.message_handler(commands=['citasmostrar'])
    def command_citasmostrar(message):
        if testing(message): #and session(message):
            chat_id = message.chat.id
            text = message.text
            cita_id = text.replace("/citasmostrar@Citas_Bot", "")
            cita_id = cita_id.replace("/citasmostrar", "")
            cita_id = cita_id.replace(" ", "")

            if cita_id == "":
                bot.send_message(chat_id, "Debes indicar el \"Número de cita\" de la cita que quieres mostrar, por ejemplo: \"/citasmostrar 6\"")
            elif not cita_id.isdigit():
                bot.send_message(chat_id, "Debes indicar un \"Número de cita\" numérico válido, por ejemplo: \"/citasmostrar 6\"")
            else:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM `cita` WHERE `id`="+cita_id
                    cursor.execute(sql)
                    if cursor.rowcount > 0:
                        row = cursor.fetchone()
                        while(row):

                            if row['hora'] is None:
                                hora = ""
                            else:
                                hora = str(row['hora'])[:5]

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

    @bot.message_handler(commands=['citashoy'])
    def command_citashoy(message):
        if testing(message): #and session(message):
            chat_id = message.chat.id
            text = message.text

            fechaHoy = time.strftime('%Y-%m-%d')

            #match = re.search('(\d){2}\/(\d){2}\/(\d){4}', text)

            with connection.cursor() as cursor:
                sql = "SELECT * FROM `cita` WHERE DATE_FORMAT(`dia`, '%Y-%m-%d')=STR_TO_DATE('"+str(fechaHoy)+"', '%Y-%m-%d')" # CURDATE()
                cursor.execute(sql)
                if cursor.rowcount > 0:
                    row = cursor.fetchone()
                    reply = "Citas programadas para hoy:\n"
                    while(row):
                        if row['hora'] is None:
                            hora = ""
                        else:
                            hora = str(row['hora'])[:5]

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
    
    @bot.message_handler(commands=['citastodas'])
    def command_citastodas(message):
        if testing(message): #and session(message):
            chat_id = message.chat.id
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `cita`"
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

    # ------------------- START: /citascrear ----------------------- #

    @bot.message_handler(commands=['citascrear'])
    def command_citascrear(message):
        try:
            if testing(message): #and session(message):
                chat_id = message.chat.id
                from_username = message.from_user.username

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
                #try:
                while chat_id in operation_dict:
                    if time.time() - operation_dict[chat_id] > 360:
                        del operation_dict[chat_id]
                        del cita_dict[chat_id]
                        bot.reply_to(message, "Operación cancelada.")
                        break
                    time.sleep(1)
                #except Exception as e:
                #    pass
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

                match = re.search('(\d){2}\/(\d){2}\/(\d){4}', dia)
                if not match:
                    bot.reply_to(message, "Debes introducir una fecha válida con el formato: " + str(time.strftime('%d/%m/%Y')))
                    msg = bot.send_message(chat_id, "¿Para qué <b>fecha</b>?",parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_dia_step)
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
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') # \n'+str(e)

    def process_hora_step(message):
        try:
            chat_id = message.chat.id
            if chat_id in operation_dict:
                
                hora = message.text

                if hora != "/saltar":

                    match = re.search('(\d){2}:(\d){2}', hora)
                    
                    if not match:
                        bot.reply_to(message, "Debes introducir una hora válida con el formato: " + str(time.strftime('%H:%M')))
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
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    def process_motivo_step(message):
        try:
            chat_id = message.chat.id
            if chat_id in operation_dict:
                
                motivo = message.text

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
                #dia = cita.dia

                #hora = cita.hora
                #if hora is None:
                #    hora = ""

                #motivo = cita.motivo

                #bot.send_message(chat_id, "De acuerdo, tu Cita es el día "+dia+" a las "+hora+" con el motivo \""+motivo+"\"")
                #del operation_dict[chat_id]
                #del cita_dict[chat_id]
            else:
                return

        except Exception as e:
            if chat_id in operation_dict:
                del operation_dict[chat_id]
                if chat_id in cita_dict:
                    del cita_dict[chat_id]
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    def process_lugar_step(message):
        try:
            chat_id = message.chat.id
            if chat_id in operation_dict:
                
                lugar = message.text

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
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    def process_direccion_step(message):
        try:
            chat_id = message.chat.id
            if chat_id in operation_dict:
                
                direccion = message.text

                if direccion != "/saltar":

                    match = len(direccion) <= 100

                    if not match:
                        bot.reply_to(message, "El lugar no puede ser mayor de 100 caracteres.")
                        bot.send_message(chat_id, '¿Cuál es la <b>dirección</b>? /saltar',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_direccion_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.direccion = direccion

                    msg = bot.reply_to(message, '¿Quién es el <b>interesado</b>? /yo',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_interesado_step)

                else:

                    msg = bot.reply_to(message, '¿Quién es el <b>interesado</b>? /yo',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_interesado_step)

            else:
                return

        except Exception as e:
            if chat_id in operation_dict:
                del operation_dict[chat_id]
                if chat_id in cita_dict:
                    del cita_dict[chat_id]
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    def process_interesado_step(message):
        try:
            chat_id = message.chat.id
            from_username = message.from_user.username
            if chat_id in operation_dict:
                
                interesado = message.text

                if interesado != "/yo":

                    match = len(interesado) <= 45

                    if not match:
                        bot.reply_to(message, "El interesado no puede ser mayor de 45 caracteres.")
                        bot.send_message(chat_id, '¿Quién es el <b>interesado</b>? /yo',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_interesado_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.interesado = interesado

                    msg = bot.reply_to(message, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_acompanantes_step)

                else:

                    cita = cita_dict[chat_id]
                    cita.interesado = "@" + from_username

                    msg = bot.reply_to(message, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                    bot.register_next_step_handler(msg, process_acompanantes_step)

            else:
                return

        except Exception as e:
            if chat_id in operation_dict:
                del operation_dict[chat_id]
                if chat_id in cita_dict:
                    del cita_dict[chat_id]
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    def process_acompanantes_step(message):
        try:
            chat_id = message.chat.id
            from_id = message.from_user.id
            if chat_id in operation_dict:
                
                acompanantes = message.text

                if acompanantes != "/saltar":

                    match = len(acompanantes) <= 100

                    if not match:
                        bot.reply_to(message, "Los acompañantes no pueden ser mayor de 100 caracteres.")
                        bot.send_message(chat_id, '¿Quiénes son los <b>acompañantes</b>? /saltar',parse_mode="HTML")
                        bot.register_next_step_handler(message, process_acompanantes_step)
                        return

                    cita = cita_dict[chat_id]
                    cita.acompanantes = acompanantes

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
                        sql += "', '" + cita.direccion + "', '" + cita.interesado

                    if cita.acompanantes is None:
                        sql += "',  '" + str(from_id) + "', false, false)"
                    else:
                        sql += "', '" + cita.acompanantes + "',  '" + str(from_id) + "', false, false)"

                    
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        id = cursor.lastrowid
                        connection.commit()

                        #if cursor.connection == True:

                        #    with connection.cursor() as cursor:
                                #sql = "SELECT * FROM `cita` WHERE `creador`="+str(from_id)+" ORDER BY `id` DESC LIMIT 1"
                                #cursor.execute(sql)
                                #if cursor.rowcount > 0:
                                #    row = cursor.fetchone()
                                #    while(row):
                                #        id = str(row['id'])
                                #        row = cursor.fetchone()
                                #else:
                                #    reply = "¡Ups! Algo ha fallado mientras creaba tu Cita"+u"\U0001F605 Inténtalo de nuevo más tarde o avisa a mi creador."
                                #    del operation_dict[chat_id]
                                #    del cita_dict[chat_id]
                                

                        reply = "¡Hecho!, tu Cita se ha creado con el \"Número de cita\" <b>"+str(id)+"</b>"
                        del operation_dict[chat_id]
                        del cita_dict[chat_id]
                        #else:
                        #    reply = "¡Ups! Algo ha fallado mientras creaba tu Cita"+u"\U0001F605 Inténtalo de nuevo más tarde o avisa a mi creador."
                        #    del operation_dict[chat_id]
                        #    del cita_dict[chat_id]
                    bot.send_message(chat_id, reply,parse_mode="HTML")

                    #if cita.hora is None:
                    #    cita.hora = "<no indicada>"
                    #if cita.direccion is None:
                    #    cita.direccion = "<no indicada>"
                    #if cita.acompanantes is None:
                    #    cita.acompanantes = "<no indicados>"

                    #bot.send_message(chat_id, "De acuerdo, tu Cita es el día "+cita.dia+" a las "+cita.hora+" en "+cita.lugar+", dirección: "+cita.direccion+" con interesado: "+cita.interesado+" y acompañantes: "+cita.acompanantes)
                    #del operation_dict[chat_id]
                    #del cita_dict[chat_id]

                else:

                    cita = cita_dict[chat_id]

                    #msg = bot.reply_to(message, '¿Cuál es el <b>motivo</b>?',parse_mode="HTML")
                    #bot.register_next_step_handler(msg, process_motivo_step)

                    #if cita.hora is None:
                    #    cita.hora = "<no indicada>"
                    #if cita.direccion is None:
                    #    cita.direccion = "<no indicada>"
                    #if cita.acompanantes is None:
                    #    cita.acompanantes = "<no indicados>"

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
                        sql += "', '" +  cita.motivo + "', '" +  cita.lugar
                    else:
                        sql += "', '" +  cita.hora + "', '" +  cita.motivo + "', '" +  cita.lugar

                    if cita.direccion is None:
                        sql += "', '" +  cita.interesado
                    else:
                        sql += "', '" +  cita.direccion + "', '" +  cita.interesado

                    if cita.acompanantes is None:
                        sql += "',  '" + str(from_id) + "', false, false)"
                    else:
                        sql += "', '" +  cita.acompanantes + "',  '" + str(from_id) + "', false, false)"


                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                        id = cursor.lastrowid
                        connection.commit()

                        #if cursor.connection == True:

                        #    with connection.cursor() as cursor:
                        #        sql = "SELECT * FROM `cita` WHERE `creador`="+str(from_id)+" ORDER BY `id` DESC LIMIT 1"
                        #        cursor.execute(sql)
                        #        if cursor.rowcount > 0:
                        #            row = cursor.fetchone()
                        #            while(row):
                        #                id = str(row['id'])
                        #                row = cursor.fetchone()
                        #        else:
                        #            reply = "¡Ups! Algo ha fallado mientras creaba tu Cita "+u"\U0001F605 Inténtalo de nuevo más tarde o avisa a mi creador."
                        #            del operation_dict[chat_id]
                        #            del cita_dict[chat_id]

                        reply = "¡Hecho!, tu Cita se ha creado con el \"Número de cita\" <b>"+str(id)+"</b>"
                        del operation_dict[chat_id]
                        del cita_dict[chat_id]
                        #else:
                        #    reply = "¡Ups! Algo ha fallado mientras creaba tu Cita "+u"\U0001F605 Inténtalo de nuevo más tarde o avisa a mi creador."
                        #    del operation_dict[chat_id]
                        #    del cita_dict[chat_id]
                    bot.send_message(chat_id, reply,parse_mode="HTML")

                    #bot.send_message(chat_id, "De acuerdo, tu Cita es el día "+cita.dia+" a las "+cita.hora+" en "+cita.lugar+", dirección: "+cita.direccion+" con interesado: "+cita.interesado+" y acompañantes: "+cita.acompanantes)
                    
            else:
                return

        except Exception as e:
            if chat_id in operation_dict:
                del operation_dict[chat_id]
                if chat_id in cita_dict:
                    del cita_dict[chat_id]
            bot.reply_to(message, 'Algo ha salido mal, hemos tenido que cancelar tu operación '+u'\U0001F622') #\n'+str(e))

    # ------------------- END: /citascrear ----------------------- #

    @bot.message_handler(commands=['cancelar'])
    def command_cancelar(message):
        if testing(message): #and session(message):
            chat_id = message.chat.id
            #from_id = message.from_user.id

            if chat_id in operation_dict:
                del operation_dict[chat_id]
                if chat_id in cita_dict:
                    del cita_dict[chat_id]
                bot.send_message(chat_id, "Operación cancelada.")


            #session = 0
            #with connection.cursor() as cursor:
            #    sql = "SELECT session FROM `session` WHERE `user`="+str(message.from_user.id)
            #    cursor.execute(sql)
            #    if cursor.rowcount > 0:
            #        row = cursor.fetchone()
            #        while(row):
            #            session = row['session']
            #            row = cursor.fetchone()
            #if session is not 0:
            #    sql = "UPDATE session SET session="+str(0)+" WHERE user="+from_id
            #    with connection.cursor() as cursor:
            #        cursor.execute(sql)
            #        if cursor.connection == True:
            #            reply = "Tu operación actual ha sido cancelada."
            #        else:
            #            reply = "No hemos podido cancelar tu operación, intentalo de nuevo más tarde."
            #    bot.forward_message(chat_id, chat_id, message.id)

    def testing(message):
        chat_id = message.chat.id
        if chat_id != cnf.admin_id and testingMode == True:
            bot.send_message(chat_id, 'Sorry @' + message.from_user.username + '!, I\'m actually re-writing my bot from PHP to Python! It\'ll be able soon! (:')
            return False
        else:
            return True

    #def session(message):
    #    #session = 0
    #    chat_id = message.chat.id
    #    with connection.cursor() as cursor:
    #        session = 0
    #        sql = "SELECT session FROM `session` WHERE `user`="+str(message.from_user.id)
    #        cursor.execute(sql)
    #        if cursor.rowcount > 0:
    #            row = cursor.fetchone()
    #            while(row):
    #                session = row['session']
    #                row = cursor.fetchone()
    #        else:
    #            sql = ("INSERT INTO session (user, session)"
				#        "VALUES (" + str(message.from_user.id) + ", " + str(0) + ")")
    #            with connection.cursor() as cursor:
    #                cursor.execute(sql)
    #                connection.commit()

    #            #    if cursor.connection == True:
    #            #        reply = "¡Cita creada!"
    #            #    else:
    #            #        reply = "¡Ups! Algo ha fallado mientras creaba tu Cita. Inténtalo de nuevo más tarde o avisa a mi creador."
    #            #bot.send_message(chat_id, reply)
    #    if session == 0:
    #        return True
    #    else:
    #        sessionAction(message, session)
    #        return False
        
    #def sessionAction(message, session):

    #    if session == 1: # ESPERANDO A QUE CITA SEA ENVIADA PARA CREARLA
    #        if str(message.text).startswith('Día:'):
    #            bot.send_message(chat_id, "¡Perfecto!")
    #        else:
    #            bot.send_message(chat_id, "Por favor, envíame la cita con el formato que te envíe. Es importante que no cambies el formato. (Puedes cancelar la operación con el comando /cancelar )")
    #    #elif session == 2:


    

    bot.polling(none_stop=True)       # E iniciamos nuestro bot para que est? atento a los mensajes
except Exception as e:
    bot.send_message(cnf.admin_id, '¡Me he caído! '+u'\U0001F631\n'+str(e))

finally:
    connection.close()