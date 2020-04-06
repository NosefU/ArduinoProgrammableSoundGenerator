#!/usr/bin/env python
# coding=utf-8

import midi
import sys
import math
import subprocess
import datetime


def write_to_clipboard(output):
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))


NOTE_NAME = ['C', 'CS', 'D', 'DS', 'E', 'F', 'FS', 'G', 'GS', 'A', 'AS', 'B']

if len(sys.argv) < 2 or len(sys.argv) >= 4:
    print "Usage: {} <midifile> [-old_method]".format(sys.argv[0])
    sys.exit(2)

old_method = False
if len(sys.argv) == 3:
    if sys.argv[2] == '-old_method':
        old_method = True
    else:
        print "Usage: {} <midifile> [-old_method]".format(sys.argv[0])
        sys.exit(2)

print "\n" * 10
# читаем мидяху
midifile = sys.argv[1]
pattern = midi.read_midifile(midifile)
pattern1 = pattern[1]

# Ищем дорогу с ударными. Ищем трек с midi.events.TrackNameEvent равным Drums
drumTrack = -1
for y in range(len(pattern)):
    for i in range(len(pattern[y])):
        if type(pattern[y][i]) is midi.events.TrackNameEvent:
            if pattern[y][i].text == "Drums":
                drumTrack = y - 1
                break

# Разгребаем мидяху. Шаг первый: просто парсим треки в список
notes = []
step = pattern.resolution / 32 * 4  # откуда взялось 4 я не помню, но 32 (1/32) - это самая короткая нота

for y in range(1, len(pattern)):  # Перебираем все треки мидяхи
    notes.append([])  # При переходе на новый трек добавляем запись (трек) в список notes

    # А теперь бежим по нотам
    for i in range(len(pattern[y])):
        # Если находим ноту - событие midi.events.NoteOnEvent или midi.events.NoteOffEvent
        if (type(pattern[y][i]) is midi.events.NoteOnEvent) or (type(pattern[y][i]) is midi.events.NoteOffEvent):

            # Обрабатываем не кратные шагу ноты
            if pattern[y][i].tick % step != 0:
                print("Warning! Track {} position {} is broken! Tick = {}. Previous tick is {}. "
                      "Trying to set duration to {}".format(y, len(notes[y - 1]),
                                                            pattern[y][i].tick, pattern[y][i - 1].tick,
                                                            (pattern[y][i].tick + pattern[y][i - 1].tick) // step))

                # Складываем тики текущей и предыдущей команды и из них считаем длительность ноты
                duration = (pattern[y][i].tick + pattern[y][i - 1].tick) // step
            else:
                # Если всё норм, то просто считаем длительность из тика текущей ноты
                duration = pattern[y][i].tick // step

            # Если это включалка ноты
            if type(pattern[y][i]) is midi.events.NoteOnEvent:
                # то добавляем в список notes[y-1] (y-1 потому что 0 трек всегда без нот) соответствующую запись
                notes[y - 1].append(dict(step=duration, state='on', pitch=pattern[y][i].data[0]))

            # Если это вЫключалка ноты
            elif type(pattern[y][i]) is midi.events.NoteOffEvent:
                #  то добавляем в список notes[y-1] (y-1 потому что 0 трек всегда без нот) соответствующую запись
                notes[y - 1].append(dict(step=duration, state='off', pitch=pattern[y][i].data[0]))
            else:
                print "o__O   ???"  # Lol :)

# -----------------------------------------------------------------------

# Разгребаем спарсенное. Шаг 2
resultList = []
newResults = []

# Перебираем все треки в списке notes
for y in range(len(notes)):
    if y != drumTrack:  # Трек с ударными оставим напоследок
        resultList.append([])  # При переходе на новый трек добавляем запись (трек) в список resultList
        newResults.append([])  # При переходе на новый трек добавляем запись (трек) в список newResults

        for i in range(len(notes[y])):  # Перебираем каждую ноту (точнее команду) в треке
            if notes[y][i]['state'] == 'on':
                # Специфика миди. Тики (и соотв. шаги) указываются с момента исполнения предыдущей команды. 
                # Соответственно, step текущей ноты на самом деле будет являться длительностью предыдущей.
                # Поэтому если находим включение ноты, то добавляем количество нулевых записей 
                # (предыдущая команда, вЫключение), соответствующее шагу notes[y][i]['step']

                if notes[y][i]['step'] > 148:  # 255 - 107  : максимальное значение uint8_t минус количество нот
                    # смотрим, сколько раз придётся продублировать элементы "255, 0"
                    note_repeats = notes[y][i]['step'] // 148
                    for repeat in range(note_repeats):
                        newResults[len(newResults) - 1].append(255)  # докидываем длину

                if (notes[y][i]['step'] % 148) > 0:
                    newResults[len(newResults) - 1].append(
                        "107 + " + str(notes[y][i]['step'] % 148))  # докидываем длину + 127

                for x in range(notes[y][i]['step']):
                    resultList[len(resultList) - 1].append(0)

            else:
                # А если вЫключение, то добавляем количество нот (предыдущая команда, включение), 
                # соответствующее шагу notes[y][i]['step']

                for x in range(notes[y][i]['step']):
                    # Для человекочитаемого названия нот из миди-номера ноты находим октаву. 
                    # Целочисленное деление на 12 (количество нот в октаве)
                    octave = notes[y][i]['pitch'] // 12 - 1

                    # И название ноты. Остаток от деления на 12 - номер ноты. 
                    # Название берём из списка NOTE_NAME по найденному номеру
                    name = NOTE_NAME[notes[y][i]['pitch'] % 12]

                    # Формируем запись вида Nb_НотаОктава (Nb_F2)
                    resultList[len(resultList) - 1].append("Nb_" + name + str(octave))
                    newResults[len(newResults) - 1].append("Nb_" + name + str(octave))
                    # resultList[len(resultList)-1].append(notes[y][i]['pitch']-12)

# А теперь доберёмся до ударных
# Если дорога ударных есть, то добиваем количество треков до 4, чтобы пятым были ударные (шумы в прошивке)
if drumTrack > -1:
    while len(resultList) < 5:
        resultList.append([])
        newResults.append([])

    # А теперь перебираем  все ноты (команды) в треке ударных так же, как и в остальных треках
    for i in range(len(notes[drumTrack])):
        if notes[drumTrack][i]['state'] == 'on':
            for x in range(notes[drumTrack][i]['step']):
                resultList[4].append(0)

            if notes[drumTrack][i]['step'] > 148:  # 255 - 107  : максимальное значение uint8_t минус количество нот
                # смотрим, сколько раз придётся продублировать элементы "255, 0"
                note_repeats = notes[drumTrack][i]['step'] // 148
                for repeat in range(note_repeats):
                    newResults[len(newResults) - 1].append(255)  # докидываем длину
            if (notes[drumTrack][i]['step'] % 148) > 0:
                newResults[len(newResults) - 1].append(
                    "107 + " + str(notes[drumTrack][i]['step'] % 148))  # докидываем длину + 107

        # здесь пошла обработка нот
        else:
            for x in range(notes[drumTrack][i]['step']):
                octave = notes[drumTrack][i]['pitch'] // 12 - 1
                name = NOTE_NAME[notes[drumTrack][i]['pitch'] % 12]

                # А теперь сортируем инструменты
                # hihat
                if name + str(octave) in ["FS2", "AS2", "GS2", "CS6", "DS6", "F6"]:
                    resultList[4].append("Nb_DS3")
                    newResults[4].append("Nb_DS3")

                # snare
                elif name + str(octave) in ["D2", "E2", "G6", "A6"]:
                    resultList[4].append("Nb_E1")
                    newResults[4].append("Nb_E1")

                # bass drum
                elif name + str(octave) in ["C2", "B1", "B6", "C7"]:
                    resultList[4].append("Nb_CS0")
                    newResults[4].append("Nb_CS0")

                else:
                    resultList[4].append(0)
                    newResults[4].append(0)

# Надо добить трек до длительности, кратной размеру такта
# Для этого находим самый длинный трек и его длину
maxLength = 0
longestTrack = 0
for i in range(len(resultList)):
    if len(resultList[i]) > maxLength:
        maxLength = len(resultList[i])
        longestTrack = i

# Расчитываем длину трека, кратную длине такта, округляя вверх
melodyLength = 32 * int(math.ceil(maxLength / 32.0))


# Ну и наконец-то выводим результат
print "\n\n--------------------------------------"

if old_method:
    # ---------- Вывод старого результата ----------
    result = "const static int MELODY_LENGTH = " + str(melodyLength) + ";\n"
    result += "const static uint8_t melody[NUMBER_OF_CHANNELS][MELODY_LENGTH] PROGMEM =\n{\n "

    # Заполняем массив
    for i in range(len(resultList)):
        result = result + "{ "
        for note in resultList[i]:
            result = result + str(note) + ", "

        # Самый длинный трек добиваем нулями до melodyLength
        if i == longestTrack:
            if melodyLength - len(resultList[i]) > 0:
                result += "0" + ", 0" * (melodyLength - len(resultList[i]) - 1) + " },\n "
            else:
                result = result[:-2] + " },\n "

        elif len(resultList[i]) == 0:
            result += " },\n "

        else:
            result = result[:-2] + " },\n "

    result += "};"

    now = datetime.datetime.today()
    print result + '\n' + now.strftime("%H:%M")
    write_to_clipboard(result + '\n' + now.strftime("%H:%M"))

else:
    # ---------- Вывод нового результата ----------
    result = "const static int MELODY_LENGTH = " + str(melodyLength) + ";\n"
    for i in range(len(newResults)):
        result += "const static int MELODY_CHANNEL_" + str(i) + "_SIZE = " + str(len(newResults[i])) + ";\n"

    for i in range(len(newResults)):
        result += "\nconst static uint8_t melody_channel_" + str(i) + "[MELODY_CHANNEL_" + str(i) + "_SIZE] PROGMEM = {"
        for note in newResults[i]:
            result += str(note) + ", "
        result = result[:-2] + " };\n"

    now = datetime.datetime.today()
    print result + '\n' + now.strftime("%H:%M")
    write_to_clipboard(result + '\n//' + now.strftime("%H:%M"))