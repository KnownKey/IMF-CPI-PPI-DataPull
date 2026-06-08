// Shared types and data-fetching logic mirroring the Python CLI (app.py).
// IMF data comes from the SDMX 2.1 REST surface; BLS from the public v2 API.

export type SeriesId = "CPI" | "PPI" | "BLS_PPI"

export interface SeriesDefinition {
  id: SeriesId
  name: string
  source: "IMF" | "BLS"
  sourceUrl: string
}

export const SERIES: Record<SeriesId, SeriesDefinition> = {
  CPI: {
    id: "CPI",
    name: "CPI",
    source: "IMF",
    sourceUrl: "https://data.imf.org/en/datasets/IMF.STA:CPI",
  },
  PPI: {
    id: "PPI",
    name: "PPI",
    source: "IMF",
    sourceUrl: "https://data.imf.org/en/datasets/IMF.STA:PPI",
  },
  BLS_PPI: {
    id: "BLS_PPI",
    name: "BLS PPI",
    source: "BLS",
    sourceUrl: "https://www.bls.gov/ppi/",
  },
}

// One observation: a country's index value for a given period.
export interface Observation {
  period: string // e.g. "2024-M01"
  country: string // ISO3, e.g. "USA"
  value: number
}

// A fully assembled, pivoted table ready for the frontend.
export interface SeriesTable {
  seriesId: SeriesId
  name: string
  source: "IMF" | "BLS"
  sourceUrl: string
  countries: string[] // ISO3 codes, column order
  countryNames: Record<string, string> // ISO3 -> full name
  periods: string[] // newest first
  // rows keyed by period -> country -> value
  rows: Record<string, Record<string, number>>
  latestPeriod: string | null
}

const IMF_BASE = "https://api.imf.org/external/sdmx/2.1"

const IMF_KEY_SUFFIX: Record<"CPI" | "PPI", string> = {
  CPI: "CPI._T.IX.M",
  PPI: "PPI.IX.M",
}

// Parse "2024-M01" or "2024" into a comparable Date.
export function parsePeriod(value: string): Date | null {
  const monthMatch = /^(\d{4})-M(\d{2})$/.exec(value)
  if (monthMatch) {
    return new Date(Number(monthMatch[1]), Number(monthMatch[2]) - 1, 1)
  }
  const yearMatch = /^(\d{4})$/.exec(value)
  if (yearMatch) {
    return new Date(Number(yearMatch[1]), 0, 1)
  }
  return null
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
]

export function formatPeriodLabel(value: string): string {
  const parsed = parsePeriod(value)
  if (!parsed) return value
  if (value.includes("-M")) {
    return `${MONTH_NAMES[parsed.getMonth()]} ${parsed.getFullYear()}`
  }
  return String(parsed.getFullYear())
}

// Minimal CSV parser that handles quoted fields with embedded commas/newlines.
function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let field = ""
  let row: string[] = []
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        field += c
      }
    } else if (c === '"') {
      inQuotes = true
    } else if (c === ",") {
      row.push(field)
      field = ""
    } else if (c === "\n") {
      row.push(field)
      rows.push(row)
      row = []
      field = ""
    } else if (c === "\r") {
      // ignore
    } else {
      field += c
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field)
    rows.push(row)
  }
  return rows
}

function buildTable(
  seriesId: SeriesId,
  observations: Observation[],
  countryNames: Record<string, string>,
): SeriesTable {
  const def = SERIES[seriesId]
  const rows: Record<string, Record<string, number>> = {}
  const countrySet = new Set<string>()

  for (const obs of observations) {
    countrySet.add(obs.country)
    if (!rows[obs.period]) rows[obs.period] = {}
    // "first" aggregation, matching pandas pivot_table aggfunc="first"
    if (rows[obs.period][obs.country] === undefined) {
      rows[obs.period][obs.country] = obs.value
    }
  }

  const periods = Object.keys(rows).sort((a, b) => {
    const da = parsePeriod(a)?.getTime() ?? 0
    const db = parsePeriod(b)?.getTime() ?? 0
    return db - da // newest first
  })

  const countries = Array.from(countrySet).sort((a, b) =>
    (countryNames[a] || a).localeCompare(countryNames[b] || b),
  )

  const latestPeriod = periods.length > 0 ? periods[0] : null

  return {
    seriesId,
    name: def.name,
    source: def.source,
    sourceUrl: def.sourceUrl,
    countries,
    countryNames: Object.fromEntries(
      countries.map((c) => [c, countryNames[c] || c]),
    ),
    periods,
    rows,
    latestPeriod,
  }
}

export async function fetchImfSeries(
  seriesId: "CPI" | "PPI",
  countries: string[],
  startPeriod?: string,
  endPeriod?: string,
): Promise<Observation[]> {
  const countryKey = countries.length > 0 ? countries.join("+") : ""
  const key = `${countryKey}.${IMF_KEY_SUFFIX[seriesId]}`
  const params = new URLSearchParams()
  if (startPeriod) params.set("startPeriod", startPeriod)
  if (endPeriod) params.set("endPeriod", endPeriod)
  const qs = params.toString()
  const url = `${IMF_BASE}/data/IMF.STA,${seriesId}/${key}${qs ? `?${qs}` : ""}`

  const res = await fetch(url, {
    headers: { Accept: "application/vnd.sdmx.data+csv" },
  })
  if (!res.ok) {
    throw new Error(`IMF ${seriesId} request failed (${res.status})`)
  }
  const text = await res.text()
  const table = parseCsv(text)
  if (table.length < 2) return []

  const header = table[0]
  const countryIdx = header.indexOf("COUNTRY")
  const periodIdx = header.indexOf("TIME_PERIOD")
  const valueIdx = header.indexOf("OBS_VALUE")
  if (countryIdx < 0 || periodIdx < 0 || valueIdx < 0) {
    throw new Error(`IMF ${seriesId} response missing expected columns`)
  }

  const observations: Observation[] = []
  for (let i = 1; i < table.length; i++) {
    const r = table[i]
    if (r.length <= valueIdx) continue
    const value = Number(r[valueIdx])
    if (!Number.isFinite(value)) continue
    observations.push({
      country: r[countryIdx],
      period: r[periodIdx],
      value,
    })
  }
  return observations
}

const BLS_SERIES_ID = "WPU00000000"
const BLS_START_YEAR = 1913
const BLS_MAX_YEARS = 20

function blsYearRanges(startPeriod?: string, endPeriod?: string): [number, number][] {
  const startYear = startPeriod ? Number(startPeriod.slice(0, 4)) : BLS_START_YEAR
  const endYear = endPeriod ? Number(endPeriod.slice(0, 4)) : new Date().getFullYear()
  const ranges: [number, number][] = []
  let year = startYear
  while (year <= endYear) {
    const rangeEnd = Math.min(year + BLS_MAX_YEARS - 1, endYear)
    ranges.push([year, rangeEnd])
    year = rangeEnd + 1
  }
  return ranges
}

export async function fetchBlsSeries(
  startPeriod?: string,
  endPeriod?: string,
): Promise<Observation[]> {
  const url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
  const apiKey = process.env.BLS_API_KEY || ""
  const observations: Observation[] = []

  for (const [startYear, endYear] of blsYearRanges(startPeriod, endPeriod)) {
    const payload: Record<string, unknown> = {
      seriesid: [BLS_SERIES_ID],
      startyear: String(startYear),
      endyear: String(endYear),
    }
    if (apiKey) payload.registrationkey = apiKey

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`BLS request failed (${res.status})`)
    const json = await res.json()
    if (json.status !== "REQUEST_SUCCEEDED") {
      const msg = Array.isArray(json.message) ? json.message.join("; ") : json.message
      throw new Error(`BLS API error: ${msg || "unknown"}`)
    }
    for (const s of json.Results.series) {
      for (const item of s.data) {
        const value = Number(item.value)
        if (!Number.isFinite(value)) continue
        observations.push({
          period: `${item.year}-${item.period}`,
          country: "USA",
          value,
        })
      }
    }
  }
  return observations
}

let cachedCountryMap: Record<string, string> | null = null

export async function loadCountryMapping(): Promise<Record<string, string>> {
  if (cachedCountryMap) return cachedCountryMap
  const url =
    "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv"
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error(String(res.status))
    const text = await res.text()
    const table = parseCsv(text)
    const header = table[0]
    const nameIdx = header.indexOf("name")
    const alpha3Idx = header.indexOf("alpha-3")
    const map: Record<string, string> = {}
    for (let i = 1; i < table.length; i++) {
      const r = table[i]
      if (r.length <= alpha3Idx) continue
      map[r[alpha3Idx]] = r[nameIdx]
    }
    cachedCountryMap = map
    return map
  } catch {
    return {}
  }
}

export async function fetchSeriesTable(
  seriesId: SeriesId,
  countries: string[],
  startPeriod?: string,
  endPeriod?: string,
): Promise<SeriesTable> {
  const countryNames = await loadCountryMapping()
  if (seriesId === "BLS_PPI") {
    const obs = await fetchBlsSeries(startPeriod, endPeriod)
    return buildTable(seriesId, obs, countryNames)
  }
  const obs = await fetchImfSeries(seriesId, countries, startPeriod, endPeriod)
  return buildTable(seriesId, obs, countryNames)
}
