export default function TranslationNotice({ message }: { message: string }) {
  return (
    <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg px-4 py-3 mb-6">
      <p className="text-yellow-200 text-sm font-medium">
        {message}
      </p>
    </div>
  );
}
