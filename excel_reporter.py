from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

import config
import openpyxl

def create_excel_report(scheduler, solver):

    filename = "TennisScheduler_Result.xlsx"

    wb = Workbook()

    # ==================================================
    # RIMOZIONE FOGLIO INIZIALE
    # ==================================================

    ws = wb.active
    wb.remove(ws)

    # ==================================================
    # STILI
    # ==================================================

    title_font = Font(
        size=18,
        bold=True
    )

    subtitle_font = Font(
        size=11,
        italic=True
    )

    header_font = Font(
        bold=True
    )

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7"
    )

    ok_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE"
    )

    warning_fill = PatternFill(
        fill_type="solid",
        fgColor="FFF2CC"
    )

    alternate_fill = PatternFill(
        fill_type="solid",
        fgColor="F7F7F7"
    )

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # ==================================================
    # RIEPILOGO
    # ==================================================

    ws = wb.create_sheet("Riepilogo")

    ws["A1"] = "TENNIS SCHEDULER"
    ws["A1"].font = title_font

    ws["A2"] = "Risultato torneo"
    ws["A2"].font = subtitle_font

    ws["A4"] = "Voce"
    ws["B4"] = "Risultato"

    for cell in ws[4]:

        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    selected_matches = sum(
        solver.Value(var)
        for var in scheduler.match_vars.values()
    )

    duplicate_matches = 0

    men_deviation = sum(
        solver.Value(var)
        for var in scheduler.men_deviation_vars.values()
    )

    soft_avoid = sum(
        solver.Value(var)
        for var in scheduler.soft_avoid_vars
    )

    different_opponents = sum(
        solver.Value(var)
        for var in scheduler.opponent_played_vars.values()
    )

    summary = [
        (
            "Partite selezionate",
            f"{selected_matches} / {config.NUM_MATCHES}"
        ),
        (
            "Partite duplicate",
            duplicate_matches
        ),
        (
            "Deviazione uomini",
            men_deviation
        ),
        (
            "Incontri indesiderati",
            soft_avoid
        ),
        (
            "Avversari diversi",
            different_opponents
        ),
        (
            "Verifica finale",
            "OK"
        ),
    ]

    row = 5

    for label, value in summary:

        ws.cell(
            row=row,
            column=1
        ).value = label

        ws.cell(
            row=row,
            column=2
        ).value = value

        ws.cell(
            row=row,
            column=1
        ).border = thin_border

        ws.cell(
            row=row,
            column=2
        ).border = thin_border

        if label == "Verifica finale":

            ws.cell(
                row=row,
                column=2
            ).font = Font(bold=True)

            ws.cell(
                row=row,
                column=2
            ).fill = ok_fill

            ws.cell(
                row=row,
                column=2
            ).alignment = Alignment(
                horizontal="center"
            )

        row += 1

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 20

    ws.sheet_view.showGridLines = False

    # ==================================================
    # PARTITE
    # ==================================================

    ws = wb.create_sheet("Partite")

    headers = [
      "N.",
      "Coppia 1",
      "Coppia 2",
      "Partite per Coppia"
    ]

    for col, header in enumerate(headers, start=1):

        cell = ws.cell(
            row=1,
            column=col
        )

        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    row = 2
    match_number = 1

    for i, match in enumerate(scheduler.matches):

        if solver.Value(scheduler.match_vars[i]):

            ws.cell(
                row=row,
                column=1
            ).value = match_number

            ws.cell(
                row=row,
                column=2
            ).value = str(match.pair1)

            ws.cell(
                row=row,
                column=3
            ).value = str(match.pair2)

            # Numero di partite previsto per ogni coppia
            ws.cell(
                row=row,
                column=4
            ).value = scheduler.target_pair_matches

            for col in range(1, 5):

                cell = ws.cell(
                    row=row,
                    column=col
                )

                cell.border = thin_border

            ws.cell(
                row=row,
                column=1
            ).alignment = Alignment(
                horizontal="center"
            )

            ws.cell(
                row=row,
                column=4
            ).alignment = Alignment(
                horizontal="center"
            )

            row += 1
            match_number += 1

    last_row = row - 1

    if last_row >= 2:

        table = Table(
            displayName="MatchesTable",
            ref=f"A1:D{last_row}"
          )

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = style

        ws.add_table(table)

    ws.freeze_panes = "A2"

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 20

    ws.sheet_view.showGridLines = False

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

        cell = ws.cell(
            row=1,
            column=col
        )

        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    row = 2

    for player in sorted(scheduler.player_count_vars):

        count = solver.Value(
            scheduler.player_count_vars[player]
        )

        if player in config.MEN:

            gender = "M"

            target = scheduler.target_men_matches

            deviation = solver.Value(
                scheduler.men_deviation_vars[player]
            )

        else:

            gender = "F"

            target = scheduler.target_women_matches

            deviation = 0

        values = [
            player,
            gender,
            count,
            target,
            deviation,
        ]

        for col, value in enumerate(values, start=1):

            cell = ws.cell(
                row=row,
                column=col
            )

            cell.value = value
            cell.border = thin_border

            if row % 2 == 0:

                cell.fill = alternate_fill

        # Evidenzia eventuale deviazione

        if deviation != 0:

            ws.cell(
                row=row,
                column=5
            ).fill = warning_fill

        # Allineamento colonne numeriche

        for col in range(2, 6):

            ws.cell(
                row=row,
                column=col
            ).alignment = Alignment(
                horizontal="center"
            )

        row += 1

    last_row = row - 1

    if last_row >= 2:

        table = Table(
            displayName="PlayersTable",
            ref=f"A1:E{last_row}"
        )

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = style

        ws.add_table(table)

    ws.freeze_panes = "A2"

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 14

    ws.sheet_view.showGridLines = False

    # ==================================================
    # AVVERSARI
    # ==================================================

    ws = wb.create_sheet("Avversari")

    headers = [
        "Giocatore",
        "Avversari diversi",
    ]

    for col, header in enumerate(headers, start=1):

        cell = ws.cell(
            row=1,
            column=col
        )

        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

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

        values = [
            player,
            len(opponents),
            
        ]

        for col, value in enumerate(values, start=1):

            cell = ws.cell(
                row=row,
                column=col
            )

            cell.value = value
            cell.border = thin_border

            if row % 2 == 0:

                cell.fill = alternate_fill

        ws.cell(
            row=row,
            column=2
        ).alignment = Alignment(
            horizontal="center"
        )

        row += 1

    last_row = row - 1

    if last_row >= 2:

        table = Table(
            displayName="OpponentsTable",
            ref=f"A1:B{last_row}"
        )

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = style

        ws.add_table(table)

    ws.freeze_panes = "A2"

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 20

    ws.sheet_view.showGridLines = False

    # ==================================================
    # CONTROLLO INTESTAZIONI TABELLE
    # ==================================================

    for ws in wb.worksheets:

        for table in ws.tables.values():

            print(f"\nControllo tabella: {ws.title} / {table.name}")

            min_col, min_row, max_col, max_row = (
                openpyxl.utils.range_boundaries(table.ref)
            )

            for col in range(min_col, max_col + 1):

                value = ws.cell(
                    row=min_row,
                    column=col
                ).value

                print(
                    f"  Colonna {col}: "
                    f"{repr(value)} "
                    f"({type(value).__name__})"
                )

    # ==================================================
    # SALVATAGGIO
    # ==================================================

    wb.save(filename)

    print(
        f"\nFile Excel creato: {filename}"
    )

    return filename
