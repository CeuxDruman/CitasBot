# <p align="center">CitasBot
This Telegram Bot will let group admins create, modify, delete, etc... any kind of meeting. Other users will be able to show group meetings, filter them by date, meeting number, etc... In adition, all members will receive a notification one day and one hour before the meeting date as a reminder.

## Currently avalaible commands
* __/citastodas__: Muestra un resumen de todas las citas.
* __/citasmostrar__: Muestra una cita en detalle dado el "Número de cita" de la misma.
* __/citashoy__: Muestra las citas programadas para hoy en detalle.
* __/citascrear__: Crea una cita paso a paso.
* __/citaseliminar__: Elimina una cita dado el "Número de cita" de la misma.
* __/citasmodificar__: Modifica una cita dado el "Número de cita" de la misma.
* __/citasfechas__: Muestra las citas programadas para la/s fecha/s indicada/s en detalle.
* __/citassemana__: Muestra las citas programadas para la semana actual en detalle.

## Commands currently in development
* __/citasasistir__: Apuntarse como acompañante a una cita, dado el "Número de cita" de la misma.

## Features currently in development
* __1 day before notification__: Users will receive a notification reminding they have a meeting the next day.
* __1 hour before notification__: Users will receive a notification reminding they have a meeting in one hour.


## How to deal with Emojis and strange characters in MySQL
You need to make some modifications in your MySQL database in order to deal especially with Emojis (but also with some special characters).

Basically, you have to change your tables and columns charset to "utf-8", as we configured on our python Bot, in the columns that have free text entry:
```
ALTER TABLE cita charset=utf8mb4,
MODIFY COLUMN motivo VARCHAR(45) CHARACTER SET utf8mb4 NOT NULL,
MODIFY COLUMN lugar VARCHAR(50) CHARACTER SET utf8mb4 NOT NULL,
MODIFY COLUMN direccion VARCHAR(100) CHARACTER SET utf8mb4,
MODIFY COLUMN interesado VARCHAR(45) CHARACTER SET utf8mb4 NOT NULL,
MODIFY COLUMN acompanantes VARCHAR(100) CHARACTER SET utf8mb4;
```

But this is not all, make sure in your python Bot you decode your "message text" before inserting it into the database, just in case your message isn't completely a string:
```
if not isinstance(cita.motivo, str):
	cita.motivo = cita.motivo.decode('utf-8')
```

You don't have to take any special care when retrieving your data from the database.

## Example
I have my own Bot running 24/7 exactly with this code, please [check it out](http://telegram.me/Citas_Bot)!

## Contact
Please, feel free to contact me by my GitHub profile methods or by [chatting me on Telegram](http://telegram.me/CeuxDruman) for any doubt or question about my Bot functionality or code.