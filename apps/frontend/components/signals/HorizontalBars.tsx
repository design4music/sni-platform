'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Props {
  data: { label: string; value: number }[];
  color?: string;
}

export default function HorizontalBars({ data, color = '#3b82f6' }: Props) {
  if (!data || data.length === 0) return null;

  // Use log scale for display to reduce visual dominance of top items
  // Keep original values for tooltip
  const maxVal = Math.max(...data.map(d => d.value));
  const logData = data.map(d => ({
    ...d,
    displayValue: maxVal > 0 ? Math.log1p(d.value) : d.value,
  }));

  return (
    <div className="w-full" style={{ height: Math.max(data.length * 28, 120) }}>
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <BarChart data={logData} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 0 }}>
          <XAxis
            type="number"
            dataKey="displayValue"
            hide
          />
          <YAxis
            type="category"
            dataKey="label"
            width={100}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(_dispVal, _name, props) => {
              const original = props.payload?.value;
              return [original, 'Events'];
            }}
          />
          <Bar dataKey="displayValue" radius={[0, 4, 4, 0]} barSize={18} label={(props) => {
            const px = Number(props.x || 0);
            const pw = Number(props.width || 0);
            const py = Number(props.y || 0);
            const ph = Number(props.height || 0);
            const original = data[props.index as number]?.value;
            return (
              <text x={px + pw + 4} y={py + ph / 2} fill="#94a3b8" fontSize={11} dominantBaseline="middle">
                {original}
              </text>
            );
          }}>
            {logData.map((_, i) => (
              <Cell key={i} fill={color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
