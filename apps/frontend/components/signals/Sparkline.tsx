'use client';

import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface Props {
  data: { week: string; count: number }[];
  color?: string;
  width?: number;
  height?: number;
}

export default function Sparkline({ data, color = '#3b82f6', width = 100, height = 28 }: Props) {
  if (!data || data.length < 2) return null;

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="count"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
