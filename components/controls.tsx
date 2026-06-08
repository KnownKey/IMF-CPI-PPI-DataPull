"use client"

import { Download, Loader2, Search } from "lucide-react"

export interface Filters {
  series: "CPI" | "PPI" | "BLS_PPI"
  countries: string
  startPeriod: string
  endPeriod: string
}

interface ControlsProps {
  filters: Filters
  onChange: (filters: Filters) => void
  onSubmit: () => void
  onExport: () => void
  loading: boolean
  exporting: boolean
}

const SERIES_OPTIONS: { value: Filters["series"]; label: string; hint: string }[] = [
  { value: "CPI", label: "IMF CPI", hint: "Consumer Price Index" },
  { value: "PPI", label: "IMF PPI", hint: "Producer Price Index" },
  { value: "BLS_PPI", label: "BLS PPI", hint: "US All Commodities" },
]

export function Controls({
  filters,
  onChange,
  onSubmit,
  onExport,
  loading,
  exporting,
}: ControlsProps) {
  const isBls = filters.series === "BLS_PPI"

  return (
    <form
      className="rounded-lg border bg-card p-5"
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit()
      }}
    >
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <label className="mb-1.5 block text-sm font-medium text-foreground">
            Data series
          </label>
          <div className="flex gap-1 rounded-md border bg-muted p-1">
            {SERIES_OPTIONS.map((opt) => {
              const active = filters.series === opt.value
              return (
                <button
                  key={opt.value}
                  type="button"
                  title={opt.hint}
                  onClick={() => onChange({ ...filters, series: opt.value })}
                  className={`flex-1 rounded px-2 py-1.5 text-xs font-semibold transition-colors ${
                    active
                      ? "bg-card text-primary shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label
            htmlFor="countries"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Countries (ISO3)
          </label>
          <input
            id="countries"
            type="text"
            placeholder={isBls ? "USA only" : "e.g. USA, CAN, GBR"}
            value={isBls ? "USA" : filters.countries}
            disabled={isBls}
            onChange={(e) => onChange({ ...filters, countries: e.target.value })}
            className="w-full rounded-md border bg-card px-3 py-2 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
          />
          <p className="mt-1 text-xs text-muted-foreground">
            {isBls ? "BLS series is US-only." : "Leave blank for all available countries."}
          </p>
        </div>

        <div>
          <label
            htmlFor="start"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Start period
          </label>
          <input
            id="start"
            type="text"
            placeholder="2000-M01 or 2000"
            value={filters.startPeriod}
            onChange={(e) => onChange({ ...filters, startPeriod: e.target.value })}
            className="w-full rounded-md border bg-card px-3 py-2 font-mono text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary"
          />
        </div>

        <div>
          <label
            htmlFor="end"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            End period
          </label>
          <input
            id="end"
            type="text"
            placeholder="2026-M03 or 2026"
            value={filters.endPeriod}
            onChange={(e) => onChange({ ...filters, endPeriod: e.target.value })}
            className="w-full rounded-md border bg-card px-3 py-2 font-mono text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-primary"
          />
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-2 sm:flex-row">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Search className="h-4 w-4" aria-hidden />
          )}
          {loading ? "Loading data..." : "Fetch data"}
        </button>
        <button
          type="button"
          onClick={onExport}
          disabled={exporting}
          className="inline-flex items-center justify-center gap-2 rounded-md border bg-card px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-60"
        >
          {exporting ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <Download className="h-4 w-4" aria-hidden />
          )}
          {exporting ? "Building Excel..." : "Export to Excel"}
        </button>
      </div>
    </form>
  )
}
