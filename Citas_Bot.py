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
        print('[' + str(chat_id) + ']: ' + actText) # Y lo imprimimos en consola
 
bot.set_update_listener(listener) # Indicamos a la librer?a que lo que hemos definido antes se encargar? de los mensajes

# Connect to the database
try:
    connection = pymysql.connect(host=cnf.mysql['host'],
                                 user=cnf.mysql['user'],
                                 password=cnf.mysql['password'],
                                 db=cnf.mysql['db'],
                                 charset=cnf.mysql['charset'],
                                 cursorclass=pymysql.cursors.DictCursor)
except:
    bot.send_message(cnf.admin_id, "¡No puedo conectarme a la BBDD!")
#    bot.send_message(cnf.admin_id, "|".join(traceback.print_exc(file=sys.stdout)))

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
    
    @bot.message_handler(commands=['ayuda'])
    def command_citascrear(message):
        if testing(message):
            chat_id = message.chat.id
            reply = ("/citashoy: Muestra todas las citas del grupo programadas para el día actual."
			    "\n\n/citassemana: Muestra todas las citas del grupo programadas para la semana actual."
				"\n\n/citasfechas: Muestra todas las citas del grupo programadas entre las 2 fechas. (Ejemplo: \"/citasfechas 12/04/2016 a 20/04/2016\")"
				"\n\n/citasfecha: Muestra todas las citas del grupo programadas para la fecha indicada. (Ejemplo: \"/citasfecha 12/04/2016\")"
				"\n\n/citastodas: Muestra un resumen de todas las citas del grupo."
				"\n\n/citasmostrar: Muestra una cita en concreto dado el ID de la misma. (Ejemplo: \"/citasmostrar 1\")"
				# Personalizar los siguientes comandos para que SOLO lo puedan mostrar los admins.
				"\n\n/citascrear: Permite crear una nueva cita."
				"\n\n/citasmodificar: Permite modificar una cita dado el ID de la misma. (Ejemplo: \"/citasmodificar 1\")"
				"\n\n/citaseliminar: Permite eliminar por completo una cita dado el ID de la misma. (Ejemplo: \"/citaseliminar 1\")"
				"\n\n/citasacompañar: Permite añadirte como acompañante a una cita dado el ID de la misma. (Ejemplo: \"/citasacompañar 1\")"
				"\n\n"
                )
            bot.send_message(chat_id, reply)
    
    @bot.message_handler(commands=['citasmostrar'])
    def command_citascrear(message):
        if testing(message):
            chat_id = message.chat.id
            text = message.text
            cita_id = text.replace("/citasmostrar@Citas_Bot", "")
            cita_id = cita_id.replace("/citasmostrar", "")
            cita_id = cita_id.replace(" ", "")

            if cita_id == "":
                bot.send_message(chat_id, "Debes indicar el ID de la cita que quieres mostrar, por ejemplo: \"/citasmostrar 6\"")
            elif not cita_id.isdigit():
                bot.send_message(chat_id, "Debes indicar un ID numérico válido, por ejemplo: \"/citasmostrar 6\"")
            else:
                with connection.cursor() as cursor:
                    sql = "SELECT * FROM `cita` WHERE `id`="+cita_id
                    cursor.execute(sql)
                    if cursor.rowcount > 0:
                        row = cursor.fetchone()
                        while(row):
                            reply = ("ID: <b>" + str(row['id']) + "</b>\n"
						        "Día: " + row['dia'] + "\n"
						        "Hora: " + row['hora'] + "\n"
						        "Motivo: " + row['motivo'] + "\n"
						        "Lugar: " + row['lugar'] + "\n"
						        "Dirección: " + row['direccion'] + "\n"
						        "Interesado: " + row['interesado'] + "\n"
						        "Acompañantes: " + row['acompanantes'] + "\n"
                                )
                            row = cursor.fetchone()
                        bot.send_message(chat_id, reply,parse_mode="HTML")
                    else:
                        bot.send_message(chat_id, "No hay ninguna cita con el id <b>"+cita_id+"</b>.",parse_mode="HTML")

    @bot.message_handler(commands=['citashoy'])
    def command_citascrear(message):
        if testing(message):
            chat_id = message.chat.id
            text = message.text

            fechaHoy = str(time.strftime("%d/%m/%Y"))

            #match = re.search('(\d){2}\/(\d){2}\/(\d){4}', text)

            #if not match:
            #    bot.send_message(chat_id, "Debes indicar una fecha : \"/citasmostrar 6\"")
            #elif not cita_id.isdigit():
            #    bot.send_message(chat_id, "Debes indicar un ID numérico válido, por ejemplo: \"/citasmostrar 6\"")
            #else:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `cita` WHERE `dia`='"+fechaHoy+"'"
                cursor.execute(sql)
                if cursor.rowcount > 0:
                    row = cursor.fetchone()
                    reply = "Citas programadas para hoy:\n"
                    while(row):
                        reply += "----------------------"
                        reply += ("ID: <b>" + str(row['id']) + "</b>\n"
						    "Día: " + row['dia'] + "\n"
						    "Hora: " + row['hora'] + "\n"
						    "Motivo: " + row['motivo'] + "\n"
						    "Lugar: " + row['lugar'] + "\n"
						    "Dirección: " + row['direccion'] + "\n"
						    "Interesado: " + row['interesado'] + "\n"
						    "Acompañantes: " + row['acompanantes'] + "\n"
                            )
                        row = cursor.fetchone()
                    bot.send_message(chat_id, reply,parse_mode="HTML")
                else:
                    bot.send_message(chat_id, "No hay ninguna cita programada para hoy.")
    
    @bot.message_handler(commands=['citastodas'])
    def command_citastodas(message):
        if testing(message):
            chat_id = message.chat.id
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `cita`"
                cursor.execute(sql)
                if cursor.rowcount > 0:
                    reply = "¡Resumen de todas las citas:\n"
                    row = cursor.fetchone()
                    while(row):
                        reply += "[<b>" + str(row['id']) + "</b>](" + row['dia'] + ") " + row['motivo'] + "\n"
                        row = cursor.fetchone()
                    bot.send_message(chat_id, reply,parse_mode="HTML")
                else:
                    bot.send_message(chat_id, "No hay ninguna cita creada.")

    def testing(message):
        chat_id = message.chat.id
        if chat_id != cnf.admin_id and testingMode == True:
            bot.send_message(chat_id, 'Sorry @' + message.from_user.username + '!, I\'m actually re-writing my bot from PHP to Python! It\'ll be able soon! (:')
            return False
        else:
            return True

    

    bot.polling(none_stop=True)       # E iniciamos nuestro bot para que est? atento a los mensajes
except:
    bot.send_message(cnf.admin_id, "¡Ha habido un error durante mi ejecución!")
#    bot.send_message(cnf.admin_id, "|".join(traceback.print_exc(file=sys.stdout)))

finally:
    connection.close()