import binascii
from tkinter import *
import pandas as pd
import sys
import math
from pandastable import Table
from PyQt5.QtWidgets import QApplication, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt


# hex to signed integer
def hextosigned(val):
    b = bytes(val, 'utf-8')
    ba = binascii.a2b_hex(b)
    return int.from_bytes(ba, byteorder='big', signed=True)


# signed integer to hex
def tohex(val, nbits):
    return hex((val + (1 << nbits)) % (1 << nbits))

class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None


def sicXE():
    startAddress = '004000'
    order = 'proga progb progc'.upper()
    order = order.split(sep=' ')
    ############################################### ordering ###########################################
    programs = {}
    program = []
    name = ''
    src = open('input.txt', 'r')
    lines = src.readlines()
    for line in lines:
        if line[0] == 'H':
            name = line[1:7].strip()
        program.append(line)
        if line[0] == 'E':
            programs[name] = program
            program = []

    # PROGC PROGB PROGA

    outOrdered = open('orderedInput.txt', 'w')
    for prog in order:
        hte = programs[prog]
        for line in hte:
            outOrdered.write(line.upper())
    outOrdered.close()
    ##################################### ext symbol table and intermidiate ##############################

    src = open('orderedInput.txt', 'r')
    lines = src.readlines()
    ext_sym = {}
    sym = open('Ext_Sym_Table.txt', 'w')
    outSrc = open("intermidiate_file.txt", "w")
    modSrc = open("Mrecords.txt", 'w')
    sym.write("Symbol Addres\n")

    progAddress = startAddress
    progEnd = ''
    for line in lines:
        if line[0] == 'H':
            ln = line[13:]
            progEnd = int(progAddress, 16) + int(ln, 16)
            progEnd = hex(progEnd)[2:].zfill(6)
            ext_sym[line[1:7].strip()] = progAddress.zfill(6)
            sym.write(line[1:7] + " " + progAddress.zfill(6) + "\n")
        if line[0] == 'E':
            progAddress = progEnd
        if line[0] == 'D':
            dlen = len(line[1:])
            idx = 1
            for i in range(dlen // 12):
                s = line[idx:idx + 12]
                symbol = s[:6]
                address = s[6:]
                address = int(address, 16) + int(progAddress, 16)
                address = hex(address)[2:].zfill(6)
                ext_sym[symbol.strip()] = address
                idx += 12
                sym.write(symbol + ' ' + address + '\n')
        if line[0] == "T":
            tmpaddress = line[1:7]
            tmpaddress = int(tmpaddress, 16) + int(progAddress, 16)
            tmpaddress = hex(tmpaddress)[2:].upper().zfill(6)
            str = line[0] + " " + tmpaddress + " " + line[7:9] + " "
            y = 9
            tmp = len(line[9:]) // 2
            for x in range(tmp):
                str = str + line[y:y + 2] + " "
                y = y + 2
            outSrc.write(str + "\n")
        if line[0] == "M":
            tmpaddress = line[1:7]
            tmpaddress = int(tmpaddress, 16) + int(progAddress, 16)
            tmpaddress = hex(tmpaddress)[2:].upper().zfill(6)
            str = line[0] + " " + tmpaddress + " " + line[7:9] + " " + line[9] + " " + line[10:]
            modSrc.write(str)

    sym.close()
    outSrc.close()
    modSrc.close()

    ################################## generate dataframe ########################
    rowStart = int(startAddress[:-1] + "0", 16)
    rowEnd = progEnd[:-1] + '0'
    rowEnd = int(rowEnd, 16) + 32
    rows = []
    for x in range(rowStart, rowEnd, 16):
        rows.append(hex(x)[2:].upper().zfill(6))
    df = pd.DataFrame(
        columns=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '0A', '0B', '0C', '0D', '0E', '0F'],
        index=rows)
    df.fillna("xx", inplace=True)

    ################################## load in memory ###############################
    openinter = open("intermidiate_file.txt", "r").readlines()
    for t in openinter:
        rec = t.split(sep=" ")
        inst = rec[3:-1]
        startTrec = rec[1]
        row = startTrec[:-1] + '0'
        col = '0' + startTrec[5]
        for i in inst:
            df.at[row, col] = i
            if col == '0F':
                col = '00'
                row = int(row, 16) + 16
                row = hex(row)[2:].upper().zfill(6)
            else:
                col = int(col, 16) + 1
                col = hex(col)[2:].upper().zfill(2)

    #################################### M records #############################

    Mrec = open("Mrecords.txt", "r").readlines()
    for t in Mrec:
        rec = t.split(sep=" ")
        MAddress = rec[1]
        hexes = int(rec[2], 16)
        bytes = math.ceil(hexes / 2)
        row = MAddress[:-1] + '0'
        col = '0' + MAddress[5]

        toModify = ''
        for i in range(bytes):
            toModify += df.at[row, col]
            if col == '0F':
                col = '00'
                row = int(row, 16) + 16
                row = hex(row)[2:].upper().zfill(6)
            else:
                col = int(col, 16) + 1
                col = hex(col)[2:].upper().zfill(2)
        if hexes % 2 == 1:
            toModify = toModify[1:]
            if bin(int(toModify, 16))[2:].zfill(hexes * 4)[0] == '0':
                toModify = '0' + toModify
            else:
                toModify = 'F' + toModify
        toModify = hextosigned(toModify)
        value = hextosigned(ext_sym[rec[4].strip()])
        modified = ''
        if rec[3] == '+':
            modified = toModify + value
        else:
            modified = toModify - value
        modified = tohex(modified, 8 * bytes)[2:].upper().zfill(2 * bytes)

        # rewrite in memory
        row = MAddress[:-1] + '0'
        col = '0' + MAddress[5]
        for i in range(0, 2 * bytes, 2):
            if hexes % 2 == 1 and i == 0:
                oldVal = df.at[row, col]
                newVal = oldVal[0] + modified[1]
                df.at[row, col] = newVal
            else:
                df.at[row, col] = modified[i:i + 2]

            if col == '0F':
                col = '00'
                row = int(row, 16) + 16
                row = hex(row)[2:].upper().zfill(6)
            else:
                col = int(col, 16) + 1
                col = hex(col)[2:].upper().zfill(2)

    #################################### generate memory ########################
    mem = open("mem.txt", 'w')
    mem.write(df.to_string())
    mem.close()
    df.insert(0, "address", rows, True)
    app = QApplication(sys.argv)
    model = pandasModel(df)
    view = QTableView()
    view.setModel(model)
    view.resize(857, 40 * (len(rows) + 1))

    for i in range(17):
        view.resizeColumnToContents(i)

    view.show()
    sys.exit(app.exec_())
    #############################################################


############################## GUI ##############################
# create the main app window
ll_app = Tk()
# app label
ll_app.title("linker loader  app")
# window dimensions
ll_app.geometry("340x200")

labell = Label(ll_app, text="Choose the type of your app :", height=2, font=("Berlin Sans FB", 13))
labell.pack()  # place the label inyo the main window
# fg--> loon el 5at

btnSICXE = Button(ll_app, text="SICXE", width=9, height=2, bg="#e91e63", fg="white", borderwidth=0, command=sicXE)
btnSICXE.pack()
btnSICXE.place(x=120, y=120)
################################################################


ll_app.mainloop()
