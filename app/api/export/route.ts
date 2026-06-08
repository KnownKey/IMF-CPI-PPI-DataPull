import { NextResponse } from "next/server"
import * as XLSX from "xlsx"
import {
  fetchSeriesTable,
  formatPeriodLabel,
  parsePeriod,
  SERIES,
  type SeriesId,
  type SeriesTable,
} from "@/lib/data"

export const dynamic = "force-dynamic"
export const maxDuration = 60

function parseCountries(value: string | null): string[] {
  if (!value) return []
  return value
    .split(",")
    .map((c) => c.trim().toUpperCase())
    .filter(Boolean)
}

// Build an AOA (array of arrays) sheet mirroring the Python layout:
// Year | Time | <country columns...> with Country Code + Most Recent Data summary rows.
function tableToAoa(table: SeriesTable): unknown[][] {
  const header: unknown[] = ["Year", "", ...table.countries.map((c) => table.countryNames[c])]
  const codeRow: unknown[] = ["", "Country Code", ...table.countries]

  const mostRecent: unknown[] = ["", "Most Recent Data"]
  for (const country of table.countries) {
    let best: string | null = null
    let bestTime = -Infinity
    for (const period of table.periods) {
      const v = table.rows[period]?.[country]
      if (v === undefined) continue
      const t = parsePeriod(period)?.getTime() ?? -Infinity
      if (t > bestTime) {
        bestTime = t
        best = period
      }
    }
    mostRecent.push(best ? formatPeriodLabel(best) : "")
  }

  const dataRows = table.periods.map((period) => {
    const parsed = parsePeriod(period)
    const year = parsed ? parsed.getFullYear() : ""
    const row: unknown[] = [year, formatPeriodLabel(period)]
    for (const country of table.countries) {
      const v = table.rows[period]?.[country]
      row.push(v === undefined ? null : Math.round(v * 10000) / 10000)
    }
    return row
  })

  return [header, codeRow, mostRecent, ...dataRows]
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const startPeriod = searchParams.get("startPeriod") || undefined
  const endPeriod = searchParams.get("endPeriod") || undefined
  const countries = parseCountries(searchParams.get("countries"))
  const seriesParam = searchParams.get("series")
  const requested: SeriesId[] = seriesParam
    ? (seriesParam.split(",").map((s) => s.trim().toUpperCase()) as SeriesId[])
    : ["CPI", "PPI", "BLS_PPI"]

  try {
    const workbook = XLSX.utils.book_new()
    for (const seriesId of requested) {
      if (!(seriesId in SERIES)) continue
      const table = await fetchSeriesTable(seriesId, countries, startPeriod, endPeriod)
      const aoa = tableToAoa(table)
      const ws = XLSX.utils.aoa_to_sheet(aoa)
      XLSX.utils.book_append_sheet(workbook, ws, `${table.name} Raw Data`)
    }

    if (workbook.SheetNames.length === 0) {
      return NextResponse.json({ error: "No valid series requested" }, { status: 400 })
    }

    const buffer = XLSX.write(workbook, { type: "buffer", bookType: "xlsx" })
    const date = new Date().toISOString().slice(0, 10).replace(/-/g, "")
    return new NextResponse(buffer, {
      headers: {
        "Content-Type":
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="IMF_CPI_PPI_Raw_${date}.xlsx"`,
      },
    })
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error"
    return NextResponse.json({ error: message }, { status: 502 })
  }
}
