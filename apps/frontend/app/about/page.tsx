import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';

export const metadata: Metadata = {
  title: 'About',
  description: 'WorldBrief organizes global reporting into structured briefings by geography and theme. Built by Maksim Micheliov.',
  alternates: { canonical: '/about' },
};

export default function AboutPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">About WorldBrief</h1>
        <div className="prose prose-invert prose-lg max-w-none space-y-6">
          <p className="text-lg text-dashboard-text-muted leading-relaxed">
            WorldBrief is a global news intelligence platform. It continuously aggregates reporting from over 210 international sources, processes it through a multi-stage AI pipeline, and organizes it into structured briefings by country, region, and theme.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            The goal is to solve a specific problem: the volume of global reporting has never been higher, but it is fragmented across regions, languages, and platforms. It has become difficult to answer basic questions -- what is happening, where, and how different issues connect. WorldBrief provides that orientation.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">How It Works</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            The system ingests reporting from 210+ sources across 60+ countries. Incoming material passes through automated classification, geographic mapping, and AI-driven clustering that groups related coverage into coherent events.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            Events are organized across five thematic tracks -- Geopolitics, Security, Economy, Society, and Environment -- and surfaced through country pages, region pages, and a global trending view.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            For a detailed look at the pipeline, methodology, and design decisions, see{' '}
            <Link href="/methodology" className="text-blue-400 hover:underline">Methodology</Link>.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">What WorldBrief Is Not</h2>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is intentionally limited in scope. It is:
          </p>
          <ul className="text-dashboard-text-muted leading-relaxed">
            <li><strong>not an opinion outlet</strong> and does not promote a political position,</li>
            <li><strong>not a prediction engine</strong> and does not forecast outcomes,</li>
            <li><strong>not a replacement for original journalism.</strong></li>
          </ul>
          <p className="text-dashboard-text-muted leading-relaxed">
            All summaries are derived from existing reporting, and source links are provided to enable independent verification and further reading.
          </p>

          <h2 className="text-2xl font-bold text-dashboard-text mt-8 mb-4">From the Founder</h2>
          <div className="float-left mr-6 mb-4 w-[120px] sm:w-[200px]">
            <Image
              src="/maksim.webp"
              alt="Maksim Micheliov"
              width={200}
              height={200}
              className="rounded-full border-2 border-dashboard-border w-full h-auto"
            />
            <a
              href="https://www.linkedin.com/in/mmdesign/"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center text-xs text-blue-400 hover:underline mt-2"
            >
              LinkedIn
            </a>
          </div>
          <p className="text-dashboard-text-muted leading-relaxed">
            My name is Maksim Micheliov. I built WorldBrief because I wanted a tool that did not exist -- something that could take the full breadth of global reporting and compress it into a structured, navigable picture of what is happening in the world.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            The project started as a personal research tool and evolved over nearly a year of iterative development into a full pipeline: ingestion, classification, clustering, summarization, and analysis. Every design decision -- from source selection to how events are grouped -- reflects a deliberate choice about how to organize information for clarity rather than engagement.
          </p>
          <p className="text-dashboard-text-muted leading-relaxed">
            WorldBrief is driven by method, not commentary. The machine I have built is the product. My interest is in analytical adequacy: structuring information so that it supports better judgment in complex environments. If you find that useful, I am glad to have you here.
          </p>

          <div className="mt-12 pt-8 border-t border-dashboard-border">
            <p className="text-sm text-dashboard-text-muted">
              Questions or feedback?{' '}
              <a href="mailto:contact@worldbrief.org" className="text-blue-400 hover:underline">
                contact@worldbrief.org
              </a>
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
