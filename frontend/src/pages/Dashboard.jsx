import React, { useEffect, useState } from 'react';
import {
    FileText,
    Activity,
    CheckCircle2,
    XCircle,
    BookOpen
} from 'lucide-react';
import { api } from '../services/api';
import GlassCard from '../components/ui/GlassCard';
import Badge from '../components/ui/Badge';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [recentClaims, setRecentClaims] = useState([]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [statsData, resultsData] = await Promise.all([
                api.getStats(),
                api.getResults()
            ]);
            // Handle error responses from API (404 returns JSON with error key)
            if (!statsData?.error) {
                setStats(statsData);
            }
            // Get last 4 results with null safety
            if (resultsData?.results && Array.isArray(resultsData.results)) {
                setRecentClaims(resultsData.results.slice(0, 4));
            }
        } catch (error) {
            console.error("Failed to load dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-12 text-center text-blue-200 animate-pulse">Loading analytics...</div>;
    if (!stats) return <div className="p-12 text-center text-red-400">Failed to load statistics. Is the backend running?</div>;

    // Calculate percentages for progress bars
    const consistentPct = stats.total > 0 ? (stats.supported / stats.total) * 100 : 0;
    const contradictedPct = stats.total > 0 ? (stats.contradicted / stats.total) * 100 : 0;

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Hero Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <GlassCard className="p-6" hoverEffect>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-blue-200 text-sm font-medium">Claims Verified</p>
                            <h3 className="text-4xl font-bold mt-2">{stats.total}</h3>
                        </div>
                        <div className="p-3 bg-blue-500/20 rounded-xl">
                            <FileText className="w-6 h-6 text-blue-300" />
                        </div>
                    </div>
                    <div className="mt-4 flex items-center text-sm text-blue-200/60">
                        <span className="text-emerald-400 font-bold mr-1">{stats.total} claims</span> processed
                    </div>
                </GlassCard>

                <GlassCard className="p-6" hoverEffect>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-purple-200 text-sm font-medium">Avg Confidence</p>
                            <h3 className="text-4xl font-bold mt-2">{stats.avg_confidence ? (stats.avg_confidence * 100).toFixed(0) : 0}%</h3>
                        </div>
                        <div className="p-3 bg-purple-500/20 rounded-xl">
                            <Activity className="w-6 h-6 text-purple-300" />
                        </div>
                    </div>
                    <div className="mt-4 text-sm text-purple-200/60">
                        {stats.accuracy !== null ? `Accuracy: ${stats.accuracy}%` : 'Across all claims'}
                    </div>
                </GlassCard>

                <GlassCard className="p-6" hoverEffect>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-emerald-200 text-sm font-medium">Consistent</p>
                            <h3 className="text-4xl font-bold mt-2">{stats.supported}</h3>
                        </div>
                        <div className="p-3 bg-emerald-500/20 rounded-xl">
                            <CheckCircle2 className="w-6 h-6 text-emerald-300" />
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-emerald-900/30 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-emerald-400 h-full" style={{ width: `${consistentPct}%` }}></div>
                    </div>
                </GlassCard>

                <GlassCard className="p-6" hoverEffect>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-rose-200 text-sm font-medium">Contradicted</p>
                            <h3 className="text-4xl font-bold mt-2">{stats.contradicted}</h3>
                        </div>
                        <div className="p-3 bg-rose-500/20 rounded-xl">
                            <XCircle className="w-6 h-6 text-rose-300" />
                        </div>
                    </div>
                    <div className="mt-4 w-full bg-rose-900/30 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-rose-400 h-full" style={{ width: `${contradictedPct}%` }}></div>
                    </div>
                </GlassCard>
            </div>

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Activity */}
                <GlassCard className="lg:col-span-2 p-6 h-full">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-semibold">Recent Verifications</h3>
                    </div>
                    <div className="space-y-4">
                        {recentClaims.length === 0 ? (
                            <div className="text-gray-400 italic">No claims processed yet. Run the pipeline to see results.</div>
                        ) : (
                            recentClaims.map((item) => (
                                <div key={item.id} className="group p-4 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all cursor-default">
                                    <div className="flex justify-between items-start gap-4">
                                        <div className="flex-1">
                                            <p className="font-medium text-white group-hover:text-blue-200 transition-colors line-clamp-1">{item.rationale}</p>
                                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                                                <span className="flex items-center gap-1 font-semibold text-blue-300"><BookOpen size={12} /> {item.book_name}</span>
                                                <span>•</span>
                                                <span>ID: #{item.id}</span>
                                                <span>•</span>
                                                <span className="text-white">{item.character}</span>
                                            </div>
                                        </div>
                                        <div className="flex flex-col items-end gap-2">
                                            <Badge type={item.prediction} />
                                            <span className="text-xs text-gray-400 font-mono">Conf: {(item.confidence * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </GlassCard>

                {/* System Health */}
                <div className="space-y-6">
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-semibold mb-4">System Health</h3>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
                                    <span className="text-sm">API Backend</span>
                                </div>
                                <span className="text-xs text-green-300 bg-green-500/10 px-2 py-1 rounded">Online</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
                                    <span className="text-sm">Ollama (Mistral 7B)</span>
                                </div>
                                <span className="text-xs text-green-300 bg-green-500/10 px-2 py-1 rounded">Ready</span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex items-center gap-3">
                                    <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
                                    <span className="text-sm">Vector DB (FAISS)</span>
                                </div>
                                <span className="text-xs text-green-300 bg-green-500/10 px-2 py-1 rounded">Indexed</span>
                            </div>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6 bg-gradient-to-br from-blue-600/20 to-purple-600/20 border-blue-400/20">
                        <h3 className="text-lg font-semibold mb-2">Pathway-based: Pathway</h3>
                        <p className="text-sm text-blue-100/80 mb-4">
                            Real-time document processing enabled using Pathway framework.
                        </p>
                        <div className="flex items-center gap-2 text-xs font-mono text-blue-200">
                            {/* Terminal icon would import from lucide-react if needed, avoiding for brevity */}
                            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                            <span>ingestion_agent.py active</span>
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
