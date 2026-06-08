import { NextResponse } from "next/server"
import { fetchSeriesTable, SERIES, type SeriesId } from "@/lib/data"

export const dynamic = "force-dynamic"
export const maxDuration = 60

function parseCountries(value: string | null): string[] {
  if (!value) return []
  return value
    .split(",")
    .map((c) => c.trim().toUpperCase())
    .filter(Boolean)
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const seriesParam = (searchParams.get("series") || "CPI").toUpperCase()
  const startPeriod = searchParams.get("startPeriod") || undefined
  const endPeriod = searchParams.get("endPeriod") || undefined
  const countries = parseCountries(searchParams.get("countries"))

  const seriesId = seriesParam === "BLS_PPI" ? "BLS_PPI" : seriesParam
  if (!(seriesId in SERIES)) {
    return NextResponse.json(
      { error: `Unknown series "${seriesParam}"` },
      { status: 400 },
    )
  }

  try {
    const table = await fetchSeriesTable(
      seriesId as SeriesId,
      countries,
      startPeriod,
      endPeriod,
    )
    return NextResponse.json({ table, generatedAt: new Date().toISOString() })
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error"
    return NextResponse.json({ error: message }, { status: 502 })
  }
}
