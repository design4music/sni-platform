'use client';

import { useState } from 'react';

export default function SourceSuggestionForm() {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const data = {
      outlet: formData.get('outlet'),
      website: formData.get('website'),
      country: formData.get('country'),
      comment: formData.get('comment'),
    };

    try {
      const response = await fetch('/api/suggest-source', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setSubmitted(true);
        e.currentTarget.reset();
      }
    } catch (error) {
      console.error('Failed to submit:', error);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="bg-green-900/20 border border-green-700 rounded-lg p-6 text-center">
        <p className="text-green-400 font-medium mb-2">Thank you for your suggestion!</p>
        <p className="text-dashboard-text-muted text-sm mb-4">
          We'll review your submission and consider adding this source to WorldBrief.
        </p>
        <button
          onClick={() => setSubmitted(false)}
          className="text-blue-400 hover:text-blue-300 text-sm underline"
        >
          Submit another suggestion
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <div>
        <label htmlFor="outlet" className="block text-sm font-medium text-dashboard-text mb-2">
          Outlet Name *
        </label>
        <input
          type="text"
          id="outlet"
          name="outlet"
          required
          className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-2 text-dashboard-text focus:outline-none focus:border-dashboard-text-muted"
          placeholder="e.g., The Guardian"
        />
      </div>

      <div>
        <label htmlFor="website" className="block text-sm font-medium text-dashboard-text mb-2">
          Website *
        </label>
        <input
          type="url"
          id="website"
          name="website"
          required
          className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-2 text-dashboard-text focus:outline-none focus:border-dashboard-text-muted"
          placeholder="https://example.com"
        />
      </div>

      <div>
        <label htmlFor="country" className="block text-sm font-medium text-dashboard-text mb-2">
          Country *
        </label>
        <input
          type="text"
          id="country"
          name="country"
          required
          className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-2 text-dashboard-text focus:outline-none focus:border-dashboard-text-muted"
          placeholder="e.g., United Kingdom"
        />
      </div>

      <div>
        <label htmlFor="comment" className="block text-sm font-medium text-dashboard-text mb-2">
          Comment (optional)
        </label>
        <textarea
          id="comment"
          name="comment"
          rows={3}
          className="w-full bg-dashboard-bg border border-dashboard-border rounded px-4 py-2 text-dashboard-text focus:outline-none focus:border-dashboard-text-muted"
          placeholder="Any additional context..."
        />
      </div>

      <p className="text-sm text-dashboard-text-muted">
        Suggestions are reviewed manually. Inclusion does not imply endorsement.
      </p>

      <button
        type="submit"
        disabled={loading}
        className="bg-dashboard-text text-dashboard-bg px-6 py-2 rounded font-medium hover:bg-white transition-colors disabled:opacity-50"
      >
        {loading ? 'Submitting...' : 'Submit Suggestion'}
      </button>
    </form>
  );
}
