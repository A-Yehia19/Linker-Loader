import binascii
from tkinter import *
import pandas as pd
import sys
import math
from pandastable import Table
from PyQt5.QtWidgets import QApplication, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt

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


def sic():
    src = open("input.txt", "r")
    outSrc = open("intermidiate_file.txt", "w")
    lines = src.readlines()
    progStart = ''
    progLen = ''
    for line in lines:
        if line[0] == "T":
            str = line[0] + " " + line[1:7].upper() + " " + line[7:9].upper() + " "
            y = 9
            tmp = len(line[9:]) // 2
            for x in range(tmp):
                str = str + line[y:y + 2] + " "
                y = y + 2
            outSrc.write(str.upper() + "\n")
        if line[0] == 'H':
            progStart = line[7:13].upper()
            progLen = line[13:].upper()
        if line[0] == 'E':
            break
    src.close()
    outSrc.close()

    rowStart = int(progStart[:-1] + "0", 16)
    rowEnd = hex(int(progStart, 16) + int(progLen, 16))[2:-1] + '0'
    rowEnd = int(rowEnd, 16)
    rowEnd += 20
    rows = []
    for x in range(rowStart, rowEnd, 16):
        rows.append(hex(x)[2:].upper().zfill(6))
    df = pd.DataFrame(
        columns=['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '0A', '0B', '0C', '0D', '0E', '0F'],
        index=rows)
    df.fillna("xx", inplace=True)

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

    mem = open("mem.txt", 'w')
    mem.write(df.to_string())
    mem.close()
    # print(rows)
    # print(df)

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
btnSIC = Button(ll_app, text="SIC", width=9, height=2, bg="#e91e63", fg="white", borderwidth=0, command=sic)
btnSIC.pack()
btnSIC.place(x=120, y=120)
################################################################


ll_app.mainloop()