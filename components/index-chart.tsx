"use client"

import { useMemo } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { SeriesTable } from "@/lib/data"
import { formatPeriodLabel, parsePeriod } from "@/lib/data"

const LINE_COLORS = [
  "#0f6e6e",
  "#c2492d",
  "#2f5e8c",
  "#8a6d1f",
  "#5a4b8c",
  "#1f7a4d",
]

interface IndexChartProps {
  table: SeriesTable
  selectedCountries: string[]
}

export function IndexChart({ table, selectedCountries }: IndexChartProps) {
  const data = useMemo(() => {
    const ascending = [...table.periods].sort((a, b) => {
      const ta = parsePeriod(a)?.getTime() ?? 0
      const tb = parsePeriod(b)?.getTime() ?? 0
      return ta - tb
    })
    return ascending.map((period) => {
      const point: Record<string, number | string> = {
        period,
        label: formatPeriodLabel(period),
      }
      for (const country of selectedCountries) {
        const v = table.rows[period]?.[country]
        if (v !== undefined) point[country] = v
      }
      return point
    })
  }, [table, selectedCountries])

  if (selectedCountries.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg border bg-card text-sm text-muted-foreground">
        Select one or more countries below to plot the index.
      </div>
    )
  }

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-semibold text-foreground">
        Index trend{" "}
        <span className="font-normal text-muted-foreground">
          ({table.name})
        </span>
      </h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              minTickGap={40}
              stroke="var(--border)"
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
              stroke="var(--border)"
              width={48}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
              formatter={(value: number, name: string) => [
                value.toFixed(4),
                table.countryNames[name] || name,
              ]}
            />
            {selectedCountries.map((country, i) => (
              <Line
                key={country}
                type="monotone"
                dataKey={country}
                name={country}
                stroke={LINE_COLORS[i % LINE_COLORS.length]}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
        {selectedCountries.map((country, i) => (
          <div key={country} className="flex items-center gap-1.5 text-xs">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: LINE_COLORS[i % LINE_COLORS.length] }}
            />
            <span className="text-muted-foreground">
              {table.countryNames[country] || country}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
