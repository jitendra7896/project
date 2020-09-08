import openpyxl
from string import ascii_uppercase
def somefun(df3,tstr,x):
    rows=len(df3.index)
    df3.drop([0], inplace=True)
    df3.drop(df3.columns[df3.columns.str.contains('unnamed', case=False)], axis=1, inplace=True)
    df3.to_excel(tstr,index=False)
    wb = openpyxl.load_workbook(filename=tstr)
    worksheet = wb.active
    for column in ascii_uppercase:
        if (column == 'A'):
            worksheet.column_dimensions[column].width = 8
        elif(column == 'AA'):
            worksheet.column_dimensions[column].width=80
        else:
            worksheet.column_dimensions[column].width = 30
    for row in range(rows):
        if (row == 1):
            worksheet.row_dimensions[row].height = 25
        else:
            worksheet.row_dimensions[row].height = 90

    wb.save(tstr)



'''workbook=xlsxwriter.Workbook(tstr)
    wa=workbook.add_worksheet(x)
    n=len(df3.columns)
    wa.set_column(0,n,30)
    wa.set_default_row(30)
    workbook.close()
    
    #df3.to_excel(tstr, index=False)'''