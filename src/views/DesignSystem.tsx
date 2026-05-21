import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/Card';
import { Badge } from '../components/Badge';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/Table';
import { Accordion, AccordionItem } from '../components/Accordion';
import { Shield, Sparkles, Layers, Type, Layout, Info } from 'lucide-react';

export const DesignSystem: React.FC = () => {
  return (
    <div className="w-full max-w-7xl mx-auto space-y-12 animate-fade-in-up">
      {/* Header Panel */}
      <div className="text-center space-y-4 pt-6">
        <div className="inline-flex items-center gap-2 bg-navy-800/5 text-navy-800 px-3 py-1.5 rounded-full border border-navy-800/10 text-xs font-semibold uppercase tracking-wider">
          <Shield className="w-3.5 h-3.5" />
          Design System Specifications
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 md:text-5xl lg:text-6xl select-none leading-tight ko-heading">
          Legal Screening Assistant <span className="text-transparent bg-clip-text bg-gradient-to-r from-navy-800 to-indigo-900">Design System</span>
        </h1>
        <p className="max-w-2xl mx-auto text-base text-slate-600">
          A high-fidelity typography, spacing, and component showcase built strictly according to professional legal screening design rules.
        </p>
      </div>

      {/* Grid: Color Palette & Spacing Guidelines */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Colors */}
        <Card variant="dashboard">
          <CardHeader>
            <div className="flex items-center gap-2 text-navy-800 mb-1">
              <Layers className="w-5 h-5" />
              <CardTitle>Color Palette</CardTitle>
            </div>
            <CardDescription>
              A carefully curated Slate & Navy system structured specifically to minimize legal document eye strain.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {/* Background */}
              <div className="flex flex-col p-3 rounded-lg border border-slate-200 bg-slate-50 transition-all hover:scale-[1.02]">
                <div className="w-full h-12 rounded bg-slate-50 border border-slate-200 mb-2"></div>
                <span className="font-semibold text-sm text-slate-900">Slate 50</span>
                <span className="text-xs text-slate-600 font-mono">#F8FAFC</span>
                <span className="text-[10px] bg-slate-200/50 text-slate-700 px-1.5 py-0.5 rounded mt-2 self-start font-medium">Soft Background</span>
              </div>
              {/* Card Surface */}
              <div className="flex flex-col p-3 rounded-lg border border-slate-200 bg-white transition-all hover:scale-[1.02] shadow-sm">
                <div className="w-full h-12 rounded bg-white border border-slate-200 mb-2"></div>
                <span className="font-semibold text-sm text-slate-900">White</span>
                <span className="text-xs text-slate-600 font-mono">#FFFFFF</span>
                <span className="text-[10px] bg-slate-200/50 text-slate-700 px-1.5 py-0.5 rounded mt-2 self-start font-medium">Card / Surfaces</span>
              </div>
              {/* Primary Text */}
              <div className="flex flex-col p-3 rounded-lg border border-slate-200 bg-white transition-all hover:scale-[1.02]">
                <div className="w-full h-12 rounded bg-slate-900 mb-2"></div>
                <span className="font-semibold text-sm text-slate-900">Slate 900</span>
                <span className="text-xs text-slate-600 font-mono">#0F172A</span>
                <span className="text-[10px] bg-slate-900/10 text-slate-800 px-1.5 py-0.5 rounded mt-2 self-start font-medium">Primary Readability</span>
              </div>
              {/* Secondary Text */}
              <div className="flex flex-col p-3 rounded-lg border border-slate-200 bg-white transition-all hover:scale-[1.02]">
                <div className="w-full h-12 rounded bg-slate-600 mb-2"></div>
                <span className="font-semibold text-sm text-slate-900">Slate 600</span>
                <span className="text-xs text-slate-600 font-mono">#475569</span>
                <span className="text-[10px] bg-slate-600/10 text-slate-700 px-1.5 py-0.5 rounded mt-2 self-start font-medium">Subtitles / Info</span>
              </div>
              {/* Brand Accent */}
              <div className="flex flex-col p-3 rounded-lg border border-slate-200 bg-white transition-all hover:scale-[1.02] col-span-2">
                <div className="w-full h-12 rounded bg-navy-800 mb-2 flex items-center justify-center text-white text-xs font-bold font-mono">
                  #1E3A8A
                </div>
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-sm text-slate-900 block">Navy 800 (Brand Accent)</span>
                    <span className="text-xs text-slate-600 font-mono">#1E3A8A</span>
                  </div>
                  <span className="text-[10px] bg-navy-800/10 text-navy-800 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                    Primary CTAs Only
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Spacing & Layout Constraints */}
        <Card variant="dashboard">
          <CardHeader>
            <div className="flex items-center gap-2 text-navy-800 mb-1">
              <Layout className="w-5 h-5" />
              <CardTitle>Spacings & Containers</CardTitle>
            </div>
            <CardDescription>
              We implement exact structural padding guidelines with zero arbitrary custom offsets.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div className="p-6 border border-slate-200 rounded-lg bg-slate-50 relative overflow-hidden">
                <span className="absolute top-2 right-2 text-[10px] font-bold text-navy-800 bg-navy-800/10 px-2 py-0.5 rounded uppercase font-mono">
                  p-6 (24px)
                </span>
                <h4 className="font-semibold text-sm text-slate-900 mb-1">Dashboard Panel Padding</h4>
                <p className="text-xs text-slate-600">
                  Applied strictly to overview grids, cards, tables, and standard lists to maintain structure and scanning speed.
                </p>
              </div>

              <div className="p-8 border border-slate-200 rounded-lg bg-white relative overflow-hidden shadow-sm">
                <span className="absolute top-2 right-2 text-[10px] font-bold text-navy-800 bg-navy-800/10 px-2 py-0.5 rounded uppercase font-mono">
                  p-8 (32px)
                </span>
                <h4 className="font-semibold text-sm text-slate-900 mb-1">Document Viewer Padding</h4>
                <p className="text-xs text-slate-600">
                  Maximized white space applied strictly to contract texts and full-screen reading panes to increase focus.
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-amber-50/50 border border-amber-200 flex gap-3 text-amber-800">
              <Info className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <span className="font-bold block">Tailwind Scale Rule</span>
                <span>We avoid arbitrary custom paddings (e.g. <code>p-[13px]</code>). Only standard Tailwind scale increments are used to guarantee geometric balance across viewports.</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Typography Section */}
      <Card variant="dashboard">
        <CardHeader>
          <div className="flex items-center gap-2 text-navy-800 mb-1">
            <Type className="w-5 h-5" />
            <CardTitle>Typography System</CardTitle>
          </div>
          <CardDescription>
            Optimized for multilingual English/Korean reading using Inter and Pretendard fonts.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-8">
          {/* Headings */}
          <div className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <span className="text-xs font-mono text-slate-600 block mb-2">Korean Heading (-0.02em Letter Spacing)</span>
              <h2 className="text-2xl font-bold text-slate-900 tracking-[-0.02em] leading-snug">
                인공지능 기반 법률 스크리닝 어시스턴트
              </h2>
            </div>
            <div className="border-b border-slate-100 pb-4">
              <span className="text-xs font-mono text-slate-600 block mb-2">English Heading (Default Spacing)</span>
              <h2 className="text-2xl font-bold text-slate-900 leading-snug">
                Automated Risk Detection and Redlining
              </h2>
            </div>
            <div>
              <span className="text-xs font-mono text-slate-600 block mb-2">Weights Specification</span>
              <div className="flex gap-4 items-center">
                <span className="font-light text-slate-900 text-lg">Light (300)</span>
                <span className="font-normal text-slate-900 text-lg">Normal (400)</span>
                <span className="font-semibold text-slate-900 text-lg">SemiBold (600)</span>
                <span className="font-bold text-slate-900 text-lg">Bold (800)</span>
              </div>
            </div>
          </div>

          {/* Legal Text Rule */}
          <div className="p-6 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-xs font-mono text-slate-600 font-bold">15px Legal Text Rule (1.6 line-height)</span>
              <span className="bg-emerald-500/10 text-emerald-700 px-2 py-0.5 rounded text-[10px] font-bold">Target Standard</span>
            </div>
            
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
              <p className="legal-text text-slate-900">
                "Subject to the terms and conditions of this Agreement, the Receiving Party shall maintain the Disclosing Party's Confidential Information in strict confidence and shall not disclose such Confidential Information to any third party without prior written consent."
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs font-mono text-slate-600">
              <div className="space-y-1">
                <span className="font-bold block text-slate-900">Font-Size:</span>
                <span>15px / 0.9375rem</span>
              </div>
              <div className="space-y-1">
                <span className="font-bold block text-slate-900">Line-Height:</span>
                <span>1.6 (leading-relaxed)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Components Catalog */}
      <div>
        <div className="flex items-center gap-2 text-slate-900 mb-6">
          <Sparkles className="w-5 h-5 text-navy-800" />
          <h2 className="text-2xl font-bold tracking-tight">Interactive Components Showcase</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Card & Badges */}
          <div className="space-y-8 md:col-span-2">
            <Card variant="dashboard">
              <CardHeader>
                <CardTitle>Semantic Badges</CardTitle>
                <CardDescription>Distinct status badges representing specific legal risk severity categories.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-3">
                <div className="space-y-2 w-full">
                  <div className="text-xs font-mono text-slate-600">Risk States:</div>
                  <div className="flex flex-wrap gap-2.5">
                    <Badge variant="high">High Risk</Badge>
                    <Badge variant="medium">Medium Risk</Badge>
                    <Badge variant="low">Low Risk</Badge>
                  </div>
                </div>

                <div className="space-y-2 w-full pt-2">
                  <div className="text-xs font-mono text-slate-600">Brand & Actions:</div>
                  <div className="flex flex-wrap gap-2.5">
                    <Badge variant="primary">Brand Accent (Navy 800)</Badge>
                    <Badge variant="secondary">Secondary Info</Badge>
                    <Badge variant="outline">Outline Tag</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Custom Table Component */}
            <div className="space-y-3">
              <span className="text-xs font-mono text-slate-600 block pl-1">Table Component Showcase</span>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Clause Category</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Remedy Difficulty</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-semibold text-slate-900">Liability Limitation</TableCell>
                    <TableCell><Badge variant="high">High</Badge></TableCell>
                    <TableCell className="font-mono text-xs">High Cost</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-slate-900">Survival Clause</TableCell>
                    <TableCell><Badge variant="medium">Medium</Badge></TableCell>
                    <TableCell className="font-mono text-xs">Medium Cost</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-semibold text-slate-900">Governing Law</TableCell>
                    <TableCell><Badge variant="low">Low</Badge></TableCell>
                    <TableCell className="font-mono text-xs">Negligible</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>

          {/* Accordion Component */}
          <Card variant="dashboard" className="h-fit">
            <CardHeader>
              <CardTitle>Interactive Accordion</CardTitle>
              <CardDescription>Useful for collapsible risk descriptions, guidelines, and annotations.</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion>
                <AccordionItem id="acc-1" trigger="How does AI identify contract risks?">
                  Our system evaluates contract text against standard commercial templates, flag phrases (like 'in perpetuity', 'completely unlimited'), and identifies significant deviations from industry standards.
                </AccordionItem>
                <AccordionItem id="acc-2" trigger="Can we edit the suggested revisions?">
                  Yes, each suggestion has a 'Copy Revision' and 'Apply to Draft' capability to streamline your legal review pipeline directly from the dashboard view.
                </AccordionItem>
                <AccordionItem id="acc-3" trigger="What templates are supported?">
                  Currently, our screening engine supports NDAs, SaaS Terms of Service, Consulting Agreements, and standard Vendor Service Level Agreements (SLAs).
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
