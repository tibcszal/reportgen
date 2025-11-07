from typing import Any
import openpyxl as px
import datetime as dt


def generate_excel_report(
    analysis_results: list[dict[str, Any]], output_path: str
) -> None:
    workbook = px.Workbook()
    for result in analysis_results:
        sheet = workbook.create_sheet(title=result["test_name"])
        sheet.append(["Metric", "Value"])
        for key, value in result.items():
            if key == "test_name":
                continue
            sheet.append([key, str(value)])
    workbook.save(
        f"{output_path}/report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
