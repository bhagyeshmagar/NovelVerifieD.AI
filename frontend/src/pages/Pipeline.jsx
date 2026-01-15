import React, { useState, useEffect, useRef } from 'react';
import {
    Play,
    Square,
    RotateCcw,
    Database,
    Cpu,
    Search,
    FileText,
    Terminal
} from 'lucide-react';
import { api } from '../services/api';
import GlassCard from '../components/ui/GlassCard';
import GlassButton from '../components/ui/GlassButton';

const Pipeline = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [logs, setLogs] = useState([]);
    const [progress, setProgress] = useState(0);
    const [currentStage, setCurrentStage] = useState(null);
    const [error, setError] = useState(null);
    const logEndRef = useRef(null);
    const pollInterval = useRef(null);

    // Initial load and polling
    useEffect(() => {
        checkStatus();
        pollInterval.current = setInterval(checkStatus, 1500); // 1.5s poll for responsiveness
        return () => clearInterval(pollInterval.current);
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    const checkStatus = async () => {
        try {
            const data = await api.getPipelineStatus();
            console.log("Pipeline Status:", data); // Debug logging

            // Backend returns: { running: bool, stage: str, progress: int, log: [] }
            setIsRunning(data.running === true);
            setCurrentStage(data.stage || null);
            setProgress(data.progress || 0);
            setError(data.error || null);

            // Backend uses "log" not "logs"
            if (data.log && Array.isArray(data.log)) {
                setLogs(data.log);
            }
        } catch (err) {
            console.error("Poll failed", err);
        }
    };

    const handleStart = async () => {
        try {
            setLogs(["Starting pipeline..."]);
            setProgress(0);
            const result = await api.startPipeline(true); // clean=true
            console.log("Start result:", result);
            if (result.success) {
                setIsRunning(true);
            } else {
                setLogs(prev => [...prev, `Error: ${result.message}`]);
            }
            // Immediately check status
            setTimeout(checkStatus, 500);
        } catch (err) {
            console.error(err);
            setLogs(prev => [...prev, `Error: ${err.message}`]);
        }
    };

    const handleStop = async () => {
        try {
            setLogs(prev => [...prev, "Stopping pipeline..."]);
            const result = await api.stopPipeline();
            console.log("Stop result:", result);
            if (result.success) {
                setIsRunning(false);
                setLogs(prev => [...prev, "Pipeline stopped by user."]);
            } else {
                setLogs(prev => [...prev, `Stop failed: ${result.message}`]);
            }
            checkStatus();
        } catch (err) {
            console.error(err);
            setLogs(prev => [...prev, `Error stopping: ${err.message}`]);
        }
    };

    const handleReset = async () => {
        if (!window.confirm("Are you sure? This will delete all generated data.")) return;
        try {
            const result = await api.resetPipeline();
            if (result.success) {
                setIsRunning(false);
                setLogs([]);
                setProgress(0);
                setCurrentStage(null);
            } else {
                alert(`Reset failed: ${result.message}`);
            }
        } catch (err) {
            console.error(err);
        }
    };

    // Calculate which stages are complete based on progress
    const stageProgress = (stageIdx) => {
        const thresholds = [15, 30, 70, 100]; // Approx % for each visual node
        return progress >= thresholds[stageIdx];
    };

    const stageActive = (stageIdx) => {
        const thresholds = [0, 15, 30, 70];
        const nextThresholds = [15, 30, 70, 100];
        return isRunning && progress >= thresholds[stageIdx] && progress < nextThresholds[stageIdx];
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)] animate-fadeIn pb-8">
            {/* Controls & Status */}
            <GlassCard className="lg:col-span-2 p-8 flex flex-col h-full">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h2 className="text-2xl font-bold mb-1">Verification Pipeline</h2>
                        <p className="text-gray-300">Run the 7-agent architecture to verify claims against novel text.</p>
                    </div>
                    <div className="flex gap-3">
                        {isRunning ? (
                            <GlassButton variant="danger" onClick={handleStop}>
                                <Square size={18} fill="currentColor" /> Stop Pipeline
                            </GlassButton>
                        ) : (
                            <>
                                <GlassButton variant="success" onClick={handleStart} disabled={isRunning}>
                                    <Play size={18} fill="currentColor" /> {progress >= 100 ? 'Run Again' : 'Start Pipeline'}
                                </GlassButton>
                                <GlassButton variant="ghost" onClick={handleReset} disabled={isRunning}>
                                    <RotateCcw size={18} /> Reset
                                </GlassButton>
                            </>
                        )}
                    </div>
                </div>

                {/* Visual Pipeline Graph */}
                <div className="flex-1 relative bg-black/20 rounded-2xl p-8 border border-white/10 overflow-hidden flex flex-col justify-center items-center min-h-[200px]">
                    {/* Connecting Line */}
                    <div className="absolute top-1/2 left-16 right-16 h-1 bg-white/10 -translate-y-1/2 z-0 hidden md:block"></div>

                    {/* Nodes */}
                    <div className="relative z-10 w-full flex flex-col md:flex-row justify-around gap-8 md:gap-4 px-4">
                        {['Ingestion', 'Embedding', 'Reasoning', 'Dossier'].map((step, idx) => {
                            const isActive = stageActive(idx);
                            const isPast = stageProgress(idx);

                            return (
                                <div key={step} className="flex flex-col items-center gap-3 transition-all duration-500 min-w-[80px]">
                                    <div className={`
                                        w-16 h-16 rounded-2xl flex items-center justify-center border-2 shadow-lg backdrop-blur-xl transition-all duration-500
                                        ${isActive
                                            ? 'bg-blue-500/40 border-blue-400 scale-110 shadow-[0_0_30px_rgba(59,130,246,0.5)]'
                                            : isPast
                                                ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                                                : 'bg-white/5 border-white/10 text-gray-500'}
                                    `}>
                                        {idx === 0 && <Database size={24} />}
                                        {idx === 1 && <Cpu size={24} />}
                                        {idx === 2 && <Search size={24} />}
                                        {idx === 3 && <FileText size={24} />}
                                    </div>
                                    <span className={`font-medium tracking-wide text-center text-sm ${isActive ? 'text-blue-300' : isPast ? 'text-emerald-300' : 'text-gray-500'}`}>
                                        {step}
                                    </span>
                                </div>
                            )
                        })}
                    </div>

                    {/* Current Stage Info */}
                    {isRunning && currentStage && (
                        <div className="mt-6 text-center animate-pulse">
                            <span className="text-blue-300 font-mono text-sm tracking-wider">PROCESSING: {currentStage.toUpperCase()}</span>
                        </div>
                    )}

                    {error && (
                        <div className="mt-6 text-center">
                            <span className="text-red-400 font-mono text-sm">ERROR: {error}</span>
                        </div>
                    )}
                </div>

                {/* Progress Bar */}
                <div className="mt-8">
                    <div className="flex justify-between text-sm mb-2 text-gray-300">
                        <span>Progress {isRunning && <span className="text-blue-400 animate-pulse">● Live</span>}</span>
                        <span>{progress}%</span>
                    </div>
                    <div className="h-3 bg-white/10 rounded-full overflow-hidden border border-white/5">
                        <div
                            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out shadow-[0_0_20px_rgba(59,130,246,0.5)]"
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>
                </div>
            </GlassCard>

            {/* Terminal / Logs */}
            <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-2xl text-white flex flex-col" style={{ maxHeight: 'calc(100vh - 160px)' }}>
                <div className="p-4 border-b border-white/10 bg-black/20 flex justify-between items-center flex-shrink-0 rounded-t-2xl">
                    <h3 className="font-mono text-sm text-gray-400 flex items-center gap-2">
                        <Terminal size={14} /> LIVE LOGS
                        {isRunning && <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse ml-2"></span>}
                    </h3>
                    <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                    </div>
                </div>
                <div
                    className="p-4 font-mono text-xs space-y-1 text-gray-300 bg-black/10 rounded-b-2xl overflow-y-auto"
                    style={{ flex: '1 1 0', minHeight: 0 }}
                >
                    {logs.length === 0 && (
                        <span className="text-gray-600 italic">Waiting for pipeline to start...</span>
                    )}
                    {logs.map((log, i) => (
                        <div key={i} className="border-l-2 border-blue-500/30 pl-2 py-0.5 break-words hover:bg-white/5">
                            <span className="text-gray-200">{log}</span>
                        </div>
                    ))}
                    <div ref={logEndRef} />
                </div>
            </div>
        </div>
    );
};

export default Pipeline;
