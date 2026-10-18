import React, { useState, useMemo } from 'react';
import { 
  Radio, 
  Search, 
  Filter, 
  ChevronDown, 
  ChevronRight, 
  Copy, 
  Check, 
  Sparkles, 
  ExternalLink,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import CHANGELOG_MARKDOWN from '../CHANGELOG.md?raw';

interface ReleaseSection {
  version: string;
  title: string;
  content: string[];
}

export function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVersion, setSelectedVersion] = useState('all');
  const [copiedVersion, setCopiedVersion] = useState<string | null>(null);
  const [expandedVersions, setExpandedVersions] = useState<Record<string, boolean>>({ 'v3.9.22-beta': true });

  const releases: ReleaseSection[] = useMemo(() => {
    const rawSections = CHANGELOG_MARKDOWN.split(/\n(?=## )/);
    const parsed: ReleaseSection[] = [];

    for (const section of rawSections) {
      const lines = section.trim().split('\n');
      if (lines.length === 0) continue;
      const headerLine = lines[0];
      if (!headerLine.startsWith('## ')) continue;

      const versionMatch = headerLine.match(/##\s+(v[\w.-]+)/);
      const version = versionMatch ? versionMatch[1] : headerLine.replace('## ', '').trim();
      const title = headerLine.replace('## ', '').trim();
      const content = lines.slice(1);

      parsed.push({ version, title, content });
    }
    return parsed;
  }, []);

  const filteredReleases = useMemo(() => {
    return releases.filter(r => {
      if (selectedVersion !== 'all' && r.version !== selectedVersion) {
        return false;
      }
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      if (r.title.toLowerCase().includes(q)) return true;
      return r.content.some(line => line.toLowerCase().includes(q));
    });
  }, [releases, selectedVersion, searchQuery]);

  const toggleExpand = (version: string) => {
    setExpandedVersions(prev => ({
      ...prev,
      [version]: !prev[version]
    }));
  };

  const copyChangelog = (version: string, content: string[]) => {
    const text = `## ${version}\n${content.join('\n')}`;
    navigator.clipboard.writeText(text);
    setCopiedVersion(version);
    setTimeout(() => setCopiedVersion(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/20 selection:text-cyan-300">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white flex items-center justify-center">
              <Radio className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                  Radio & TV Story Segmenter
                </h1>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/80">
                  v3.9.20-beta
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Desktop Suite Release History & Interactive Changelog Inspector
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 w-full md:w-auto">
            <a 
              href="https://github.com/bradlinder/RTVS3" 
              target="_blank" 
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              <span>GitHub Repository</span>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            </a>
            <a 
              href="https://github.com/bradlinder/RTVS3/releases" 
              target="_blank" 
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white shadow-sm shadow-cyan-600/30 transition"
            >
              <span>Releases & Binaries</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl w-full mx-auto px-6 py-8 flex-1 flex flex-col gap-6">
        {/* Architecture & Environment Status Banner */}
        <section className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded">
                  <Cpu className="w-3 h-3" /> Core Engine
                </span>
                <span className="text-xs text-slate-400">Native Python / PySide6 Desktop Application</span>
              </div>
              <p className="text-sm text-slate-300">
                AI-driven audio/video story segmentation, faster-whisper transcription, WeSpeaker voice embedding diarization, and multi-platform broadcast publishing.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/60 border border-slate-700/60 px-3 py-2 rounded-xl">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>WeSpeaker ONNX & MarianMT isolated architecture</span>
            </div>
          </div>
        </section>

        {/* Filter and Search Bar */}
        <section className="flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text"
              placeholder="Search features, fixes, or modules..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5" />
              <span>Filter:</span>
            </div>
            <select
              value={selectedVersion}
              onChange={e => setSelectedVersion(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition cursor-pointer"
            >
              <option value="all">All Releases ({releases.length})</option>
              {releases.map(r => (
                <option key={r.version} value={r.version}>{r.version}</option>
              ))}
            </select>
          </div>
        </section>

        {/* Changelog Accordion List */}
        <section className="space-y-4">
          {filteredReleases.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl bg-slate-900/20">
              <p className="text-slate-400 text-sm">No release notes matched your search query.</p>
              <button 
                onClick={() => { setSearchQuery(''); setSelectedVersion('all'); }}
                className="mt-3 text-xs text-cyan-400 hover:text-cyan-300 underline"
              >
                Reset search filters
              </button>
            </div>
          ) : (
            filteredReleases.map(release => {
              const isExpanded = expandedVersions[release.version] ?? (release.version === 'v3.9.20-beta' || release.version === 'v3.5.34');
              const isLatest = release.version === 'v3.9.20-beta';

              return (
                <article 
                  key={release.version}
                  className={`border rounded-2xl transition-all duration-200 ${
                    isLatest 
                      ? 'border-cyan-800/80 bg-slate-900/70 shadow-lg shadow-cyan-950/20' 
                      : 'border-slate-800 bg-slate-900/30 hover:border-slate-700'
                  }`}
                >
                  <header 
                    onClick={() => toggleExpand(release.version)}
                    className="p-5 flex items-center justify-between cursor-pointer select-none gap-4"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1 rounded-lg bg-slate-800 text-slate-300">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-cyan-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-base font-bold text-white tracking-tight">
                            {release.title}
                          </h2>
                          {isLatest && (
                            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1">
                              <Sparkles className="w-3 h-3" /> Latest Release
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {release.content.filter(l => l.trim().startsWith('- **')).length} major milestone updates
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                      <button
                        onClick={() => copyChangelog(release.version, release.content)}
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-xs flex items-center gap-1.5"
                        title="Copy release notes markdown"
                      >
                        {copiedVersion === release.version ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span className="text-[11px] text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span className="text-[11px]">Copy Markdown</span>
                          </>
                        )}
                      </button>
                    </div>
                  </header>

                  {isExpanded && (
                    <div className="px-6 pb-6 pt-2 border-t border-slate-800/80 text-sm text-slate-300 space-y-3 font-sans leading-relaxed">
                      {release.content.map((line, idx) => {
                        const trimmed = line.trim();
                        if (!trimmed) return null;

                        if (trimmed.startsWith('- **')) {
                          const parts = trimmed.slice(2).split(':**');
                          const title = parts[0]?.replace(/^\*\*/, '');
                          const rest = parts.slice(1).join(':**');

                          return (
                            <div key={idx} className="mt-3 first:mt-1">
                              <h3 className="text-slate-100 font-semibold text-sm flex items-center gap-2 text-cyan-200">
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 inline-block" />
                                {title}
                              </h3>
                              {rest && <p className="text-slate-300 text-xs mt-1 ml-3.5">{rest}</p>}
                            </div>
                          );
                        }

                        if (trimmed.startsWith('- ')) {
                          return (
                            <li key={idx} className="ml-6 text-xs text-slate-300 list-disc marker:text-slate-500">
                              {trimmed.slice(2)}
                            </li>
                          );
                        }

                        if (trimmed.startsWith('  - ')) {
                          return (
                            <li key={idx} className="ml-10 text-xs text-slate-400 list-circle marker:text-slate-600">
                              {trimmed.slice(4)}
                            </li>
                          );
                        }

                        return (
                          <p key={idx} className="text-xs text-slate-300">
                            {trimmed}
                          </p>
                        );
                      })}
                    </div>
                  )}
                </article>
              );
            })
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 px-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>Radio & TV Story Segmenter desktop suite - Built for broadcast journalism.</p>
          <p className="text-slate-600">Live preview dynamically synchronized with repository documentation</p>
        </div>
      </footer>
    </div>
  );
}
