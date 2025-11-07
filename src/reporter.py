from typing import Any
import openpyxl as px
import datetime as dt


def generate_excel_report(
    analysis_results: list[dict[str, Any]], output_path: str
) -> None:
    workbook = px.Workbook()
    # If there are no results, keep the default sheet and write a small message
    if not analysis_results:
        active = workbook.active
        # mypy/type-checkers sometimes treat active as optional; assert to help them
        assert active is not None
        sheet = active
        sheet.title = "Report"
        sheet.append(["Metric", "Value"])
        sheet.append(["status", "no results"])
    else:
        # Remove the default empty sheet created by openpyxl so it doesn't appear
        # at the beginning of the final workbook.
        active = workbook.active
        if active is not None:
            try:
                workbook.remove(active)
            except Exception:
                # If removal fails for any reason, continue and create sheets as usual
                pass

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
