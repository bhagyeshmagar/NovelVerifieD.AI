import React, { useState, useEffect } from 'react';
import { Search, ExternalLink, X, BookOpen, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';
import GlassButton from '../components/ui/GlassButton';

const Results = () => {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedClaim, setSelectedClaim] = useState(null);

    useEffect(() => {
        loadResults();
    }, []);

    const loadResults = async () => {
        try {
            const data = await api.getResults();
            setResults(data.results || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const filteredResults = results.filter(r => {
        const matchesSearch = r.rationale?.toLowerCase().includes(search.toLowerCase()) ||
            r.character?.toLowerCase().includes(search.toLowerCase());
        return matchesSearch;
    });

    return (
        <div className="h-full flex flex-col animate-fadeIn pb-8">
            <div className="flex flex-col md:flex-row justify-between items-end mb-6 gap-4">
                <div>
                    <h2 className="text-2xl font-bold mb-2">Analysis Results</h2>
                    <p className="text-gray-300">Output generated from <code className="bg-white/10 px-1.5 py-0.5 rounded text-sm">results.csv</code></p>
                </div>

                <div className="relative w-full md:w-96">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search claims..."
                        className="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-2.5 text-white focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-all"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
            </div>

            <GlassCard className="flex-1 overflow-hidden flex flex-col">
                <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-left border-collapse min-w-[800px]">
                        <thead>
                            <tr className="border-b border-white/10 bg-white/5 text-gray-300 text-sm uppercase tracking-wider">
                                <th className="p-4 font-medium">ID</th>
                                <th className="p-4 font-medium">Character / Book</th>
                                <th className="p-4 font-medium w-1/3">Rationale</th>
                                <th className="p-4 font-medium">Verdict</th>
                                <th className="p-4 font-medium">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                <tr><td colSpan="5" className="p-8 text-center text-gray-400">Loading results...</td></tr>
                            ) : filteredResults.length === 0 ? (
                                <tr><td colSpan="5" className="p-8 text-center text-gray-400">No results found.</td></tr>
                            ) : (
                                filteredResults.map((row) => (
                                    <tr key={row.id} className="hover:bg-white/5 transition-colors text-sm text-gray-200 group">
                                        <td className="p-4 font-mono text-gray-400">#{row.id}</td>
                                        <td className="p-4">
                                            <div className="font-bold text-white text-base">{row.character}</div>
                                            <div className="text-xs text-blue-300 flex items-center gap-1 mt-1">
                                                <BookOpen size={10} /> {row.book_name}
                                            </div>
                                        </td>
                                        <td className="p-4 text-gray-300">
                                            <p className="line-clamp-2">{row.rationale}</p>
                                        </td>
                                        <td className="p-4">
                                            <div className="flex flex-col gap-1">
                                                <Badge type={row.prediction} />
                                                <span className="text-[10px] text-gray-500 font-mono pl-1">Conf: {(row.confidence * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <button
                                                onClick={() => setSelectedClaim(row)}
                                                className="text-blue-300 hover:text-white transition-colors flex items-center gap-1 text-xs font-bold uppercase tracking-wide opacity-70 group-hover:opacity-100"
                                            >
                                                Details <ExternalLink size={12} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </GlassCard>

            {/* Detail Modal */}
            {selectedClaim && (
                <DetailModal
                    claim={selectedClaim}
                    onClose={() => setSelectedClaim(null)}
                />
            )}
        </div>
    );
};

const DetailModal = ({ claim, onClose }) => {
    const [dossier, setDossier] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadDossier = async () => {
            try {
                const data = await api.getDossier(claim.id);
                setDossier(data.content);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        loadDossier();
    }, [claim]);

    // Close on escape key
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200"
            onClick={onClose}
        >
            <div
                className="glass-panel w-full max-w-5xl max-h-[85vh] flex flex-col shadow-2xl border-white/10 bg-[#0f172a]"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <div>
                        <div className="text-xs font-mono text-gray-400 mb-1">CLAIM ID: {claim.id}</div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                            Verification Analysis
                            <Badge type={claim.prediction} />
                        </h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {/* Key Info Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-white/5 p-5 rounded-xl border border-white/5">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Character</h3>
                            <div className="text-white font-bold text-xl">{claim.character}</div>
                        </div>
                        <div className="bg-white/5 p-5 rounded-xl border border-white/5">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Book</h3>
                            <div className="text-white font-bold text-xl">{claim.book_name}</div>
                        </div>
                        <div className="bg-white/5 p-5 rounded-xl border border-white/5">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Confidence</h3>
                            <div className={`text-3xl font-black ${claim.confidence > 0.8 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                {(claim.confidence * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>

                    <div className="mb-10">
                        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <AlertCircle size={16} /> Reasoning Logic
                        </h3>
                        <p className="text-lg text-gray-200 leading-relaxed bg-white/5 p-8 rounded-xl border border-white/5 shadow-inner">
                            {claim.rationale}
                        </p>
                    </div>

                    <div className="prose prose-invert max-w-none prose-headings:text-white prose-a:text-blue-400 prose-strong:text-white prose-blockquote:border-blue-400">
                        <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Full Evidence Dossier</h3>
                        {loading ? (
                            <div className="space-y-4 animate-pulse">
                                <div className="h-4 bg-white/5 rounded w-3/4"></div>
                                <div className="h-4 bg-white/5 rounded w-1/2"></div>
                                <div className="h-64 bg-white/5 rounded"></div>
                            </div>
                        ) : dossier ? (
                            <div className="bg-white/5 p-8 rounded-xl border border-white/5">
                                <ReactMarkdown>{dossier}</ReactMarkdown>
                            </div>
                        ) : (
                            <div className="text-gray-500 italic border border-dashed border-white/20 p-8 rounded-xl text-center">
                                No detailed dossier available for this claim.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Results;
