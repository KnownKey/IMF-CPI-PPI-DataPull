"use client"

import { useEffect, useMemo, useState } from "react"
import useSWR from "swr"
import { AlertCircle, BarChart3, Database } from "lucide-react"
import { Controls, type Filters } from "@/components/controls"
import { IndexChart } from "@/components/index-chart"
import { DataTable } from "@/components/data-table"
import type { SeriesTable } from "@/lib/data"
import { formatPeriodLabel } from "@/lib/data"

interface ApiResponse {
  table: SeriesTable
  generatedAt: string
}

const fetcher = async (url: string): Promise<ApiResponse> => {
  const res = await fetch(url)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request failed (${res.status})`)
  }
  return res.json()
}

function buildQuery(filters: Filters): string {
  const params = new URLSearchParams()
  params.set("series", filters.series)
  if (filters.series !== "BLS_PPI" && filters.countries.trim()) {
    params.set("countries", filters.countries.trim())
  }
  if (filters.startPeriod.trim()) params.set("startPeriod", filters.startPeriod.trim())
  if (filters.endPeriod.trim()) params.set("endPeriod", filters.endPeriod.trim())
  return params.toString()
}

export default function HomePage() {
  const [filters, setFilters] = useState<Filters>({
    series: "CPI",
    countries: "USA, CAN, GBR, DEU, JPN",
    startPeriod: "2015-M01",
    endPeriod: "",
  })
  // The query that has actually been submitted (drives fetching).
  const [activeQuery, setActiveQuery] = useState<string | null>(null)
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])
  const [exporting, setExporting] = useState(false)

  const { data, error, isLoading } = useSWR<ApiResponse>(
    activeQuery ? `/api/data?${activeQuery}` : null,
    fetcher,
    { revalidateOnFocus: false },
  )

  const table = data?.table

  // Default chart selection: first few countries once data arrives.
  useEffect(() => {
    if (table) {
      setSelectedCountries(table.countries.slice(0, 5))
    }
  }, [table])

  const handleSubmit = () => {
    setActiveQuery(buildQuery(filters))
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const params = new URLSearchParams()
      params.set("series", filters.series)
      if (filters.series !== "BLS_PPI" && filters.countries.trim()) {
        params.set("countries", filters.countries.trim())
      }
      if (filters.startPeriod.trim()) params.set("startPeriod", filters.startPeriod.trim())
      if (filters.endPeriod.trim()) params.set("endPeriod", filters.endPeriod.trim())
      const res = await fetch(`/api/export?${params.toString()}`)
      if (!res.ok) throw new Error("Export failed")
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, "")
      a.download = `IMF_CPI_PPI_Raw_${date}.xlsx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      // surfaced via alert; keep it simple
      alert("Could not generate the Excel file. Please try again.")
    } finally {
      setExporting(false)
    }
  }

  const toggleCountry = (country: string) => {
    setSelectedCountries((prev) =>
      prev.includes(country)
        ? prev.filter((c) => c !== country)
        : [...prev, country],
    )
  }

  const latestLabel = useMemo(
    () => (table?.latestPeriod ? formatPeriodLabel(table.latestPeriod) : null),
    [table],
  )

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 md:py-12">
      <header className="mb-8">
        <div className="mb-2 flex items-center gap-2 text-primary">
          <BarChart3 className="h-5 w-5" aria-hidden />
          <span className="text-xs font-semibold uppercase tracking-wider">
            IMF · BLS Price Indices
          </span>
        </div>
        <h1 className="text-pretty text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          CPI &amp; PPI Data Explorer
        </h1>
        <p className="mt-2 max-w-2xl text-pretty leading-relaxed text-muted-foreground">
          Browse raw monthly Consumer and Producer Price Index data sourced
          directly from the IMF SDMX and BLS public APIs. Filter by country and
          period, visualize trends, then export everything to a styled Excel
          workbook.
        </p>
      </header>

      <div className="mb-6">
        <Controls
          filters={filters}
          onChange={setFilters}
          onSubmit={handleSubmit}
          onExport={handleExport}
          loading={isLoading}
          exporting={exporting}
        />
      </div>

      {!activeQuery && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 py-16 text-center">
          <Database className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden />
          <p className="text-sm font-medium text-foreground">No data loaded yet</p>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Choose a series and filters above, then select{" "}
            <span className="font-semibold text-foreground">Fetch data</span> to
            load observations.
          </p>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-lg border bg-card p-4 text-sm">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-accent" aria-hidden />
          <div>
            <p className="font-semibold text-foreground">Couldn&apos;t load data</p>
            <p className="mt-0.5 text-muted-foreground">{error.message}</p>
          </div>
        </div>
      )}

      {table && !error && (
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border bg-card px-4 py-3 text-sm">
            <div>
              <span className="text-muted-foreground">Source: </span>
              <a
                href={table.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-primary hover:underline"
              >
                {table.source}
              </a>
            </div>
            <div>
              <span className="text-muted-foreground">Latest observation: </span>
              <span className="font-medium text-foreground">
                {latestLabel || "—"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Countries: </span>
              <span className="font-medium text-foreground">
                {table.countries.length}
              </span>
            </div>
          </div>

          <IndexChart table={table} selectedCountries={selectedCountries} />
          <DataTable
            table={table}
            selectedCountries={selectedCountries}
            onToggleCountry={toggleCountry}
          />
        </div>
      )}

      <footer className="mt-12 border-t pt-6 text-xs text-muted-foreground">
        Data values are unrebased IMF/BLS observations; no model calculations
        are applied. IMF CPI/PPI via the SDMX 2.1 REST API · BLS PPI series
        WPU00000000 (All Commodities).
      </footer>
    </main>
  )
}
