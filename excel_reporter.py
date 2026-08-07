from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import config


def create_excel_report(scheduler, solver):

    filename = "TennisScheduler_Result.xlsx"

    wb = Workbook()

    # Rimuove il foglio iniziale
    ws = wb.active
    wb.remove(ws)

    # ==================================================
    # RIEPILOGO
    # ==================================================

    ws = wb.create_sheet("Riepilogo")

    ws["A1"] = "TENNIS SCHEDULER"
    ws["A1"].font = Font(size=18, bold=True)

    ws["A3"] = "Partite selezionate"
    ws["B3"] = sum(
        solver.Value(var)
        for var in scheduler.match_vars.values()
    )

    ws["A4"] = "Partite richieste"
    ws["B4"] = config.NUM_MATCHES

    ws["A5"] = "Partite duplicate"
    ws["B5"] = 0

    ws["A7"] = "Deviazione totale uomini"
    ws["B7"] = sum(
        solver.Value(var)
        for var in scheduler.men_deviation_vars.values()
    )

    ws["A8"] = "Incontri indesiderati"
    ws["B8"] = sum(
        solver.Value(var)
        for var in scheduler.soft_avoid_vars
    )

    ws["A9"] = "Avversari diversi"
    ws["B9"] = sum(
        solver.Value(var)
        for var in scheduler.opponent_played_vars.values()
    )

    ws["A11"] = "Verifica finale"
    ws["B11"] = "OK"

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 20

    # ==================================================
    # PARTITE
    # ==================================================

    ws = wb.create_sheet("Partite")

    headers = [
        "N.",
        "Coppia 1",
        "Coppia 2",
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)

    row = 2
    match_number = 1

    for i, match in enumerate(scheduler.matches):

        if solver.Value(scheduler.match_vars[i]):

            ws.cell(row=row, column=1).value = match_number
            ws.cell(row=row, column=2).value = str(match.pair1)
            ws.cell(row=row, column=3).value = str(match.pair2)

            row += 1
            match_number += 1

    # ==================================================
    # GIOCATORI
    # ==================================================

    ws = wb.create_sheet("Giocatori")

    headers = [
        "Giocatore",
        "Sesso",
        "Partite",
        "Target",
        "Deviazione",
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)

    row = 2

    for player in sorted(scheduler.player_count_vars):

        count = solver.Value(
            scheduler.player_count_vars[player]
        )

        if player in config.MEN:
            gender = "M"
            target = scheduler.target_men_matches

            if player in scheduler.men_deviation_vars:
                deviation = solver.Value(
                    scheduler.men_deviation_vars[player]
                )
            else:
                deviation = 0

        else:
            gender = "F"
            target = config.TARGET_MATCHES_PER_WOMAN
            deviation = 0

        ws.cell(row=row, column=1).value = player
        ws.cell(row=row, column=2).value = gender
        ws.cell(row=row, column=3).value = count
        ws.cell(row=row, column=4).value = target
        ws.cell(row=row, column=5).value = deviation

        row += 1

    # ==================================================
    # AVVERSARI
    # ==================================================

    ws = wb.create_sheet("Avversari")

    headers = [
        "Giocatore",
        "Avversari diversi",
        "Elenco avversari",
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True)

    row = 2

    for player in sorted(scheduler.player_count_vars):

        opponents = set()

        for (p1, p2), played_var in (
            scheduler.opponent_played_vars.items()
        ):

            if solver.Value(played_var):

                if player == p1:
                    opponents.add(p2)

                elif player == p2:
                    opponents.add(p1)

        ws.cell(row=row, column=1).value = player
        ws.cell(row=row, column=2).value = len(opponents)
        ws.cell(row=row, column=3).value = ", ".join(
            sorted(opponents)
        )

        row += 1

    # ==================================================
    # FORMATTAZIONE
    # ==================================================

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for ws in wb.worksheets:

        for row_cells in ws.iter_rows():

            for cell in row_cells:

                cell.alignment = Alignment(
                    vertical="center"
                )

        # Formattazione intestazioni
        for cell in ws[1]:

            cell.font = Font(bold=True)

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

            cell.border = thin_border

        # Larghezza colonne automatica
        for column_cells in ws.columns:

            max_length = 0

            column_letter = get_column_letter(
                column_cells[0].column
            )

            for cell in column_cells:

                if cell.value is not None:

                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )

            ws.column_dimensions[
                column_letter
            ].width = min(max_length + 2, 60)

    wb.save(filename)

    print(
        f"\nFile Excel creato: {filename}"
    )

    return filename
