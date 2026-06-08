"use client"

import type { SeriesTable } from "@/lib/data"
import { formatPeriodLabel } from "@/lib/data"

interface DataTableProps {
  table: SeriesTable
  selectedCountries: string[]
  onToggleCountry: (country: string) => void
}

export function DataTable({
  table,
  selectedCountries,
  onToggleCountry,
}: DataTableProps) {
  const selected = new Set(selectedCountries)

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold text-foreground">
          {table.name} raw index data
        </h3>
        <span className="text-xs text-muted-foreground">
          {table.periods.length} periods · {table.countries.length} countries
        </span>
      </div>
      <div className="table-scroll max-h-[28rem] overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10 bg-muted">
            <tr>
              <th className="sticky left-0 z-20 border-b border-r bg-muted px-3 py-2 text-left font-semibold text-foreground">
                Period
              </th>
              {table.countries.map((country) => {
                const active = selected.has(country)
                return (
                  <th
                    key={country}
                    className="whitespace-nowrap border-b px-3 py-2 text-right font-semibold"
                  >
                    <button
                      type="button"
                      onClick={() => onToggleCountry(country)}
                      title={`Toggle ${table.countryNames[country] || country} in chart`}
                      className={`max-w-[10rem] truncate rounded px-1.5 py-0.5 text-right transition-colors ${
                        active
                          ? "bg-primary text-primary-foreground"
                          : "text-foreground hover:bg-card"
                      }`}
                    >
                      {table.countryNames[country] || country}
                    </button>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {table.periods.map((period, rowIdx) => (
              <tr
                key={period}
                className={rowIdx % 2 === 0 ? "bg-card" : "bg-background"}
              >
                <td className="sticky left-0 z-10 whitespace-nowrap border-r bg-inherit px-3 py-1.5 font-medium text-foreground">
                  {formatPeriodLabel(period)}
                </td>
                {table.countries.map((country) => {
                  const v = table.rows[period]?.[country]
                  return (
                    <td
                      key={country}
                      className={`whitespace-nowrap px-3 py-1.5 text-right font-mono tabular-nums ${
                        selected.has(country)
                          ? "text-foreground"
                          : "text-muted-foreground"
                      }`}
                    >
                      {v === undefined ? "—" : v.toFixed(4)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
