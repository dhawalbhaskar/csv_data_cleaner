#class CSV_Vaidate:
def ReadCSV(csvfile):
    with open(csvfile, "r", encoding="utf-8") as file:
        lines = file.readlines()
    return lines

    

def ValidateCSV():
    pass

line = ReadCSV("/home/nifi/inputdir/emp_detail.csv")
for i in line:
    print (i)

