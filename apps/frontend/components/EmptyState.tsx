interface EmptyStateProps {
  title: string;
  description?: string;
}

export default function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="text-center py-12 bg-dashboard-surface border border-dashboard-border rounded-lg">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {description && (
        <p className="text-dashboard-text-muted">{description}</p>
      )}
    </div>
  );
}
