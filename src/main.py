import openpyxl as px
import datetime as dt

def main():
    workbook = px.Workbook()

    workbook.save("sample.xlsx")

if __name__ == "__main__":
    main()