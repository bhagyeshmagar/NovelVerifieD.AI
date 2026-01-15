import React from 'react';
import { Layers, Database, Brain, FileCheck } from 'lucide-react';

const Docs = () => {
    return (
        <div className="docs-page fade-in">
            <header className="page-header mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Documentation</h1>
                <p className="text-secondary">System architecture and usage guide</p>
            </header>

            <div className="max-w-4xl">
                <div className="glass-panel p-8 mb-8">
                    <h2 className="text-xl font-bold text-white mb-4">Pipeline Architecture</h2>
                    <p className="text-text-secondary mb-6 leading-relaxed">
                        NovelVerified.AI uses a 5-stage pipeline to verify claims against novel texts.
                        The system leverages RAG (Retrieval Augmented Generation) and LLM-based reasoning
                        to produce high-confidence verdicts.
                    </p>

                    <div className="grid grid-cols-2 gap-6">
                        <StageCard
                            icon={<Layers size={24} />}
                            title="1. Ingestion"
                            desc="Chunks novels into overlapping segments and processes claims from CSV."
                        />
                        <StageCard
                            icon={<Database size={24} />}
                            title="2. Retrieval"
                            desc="Uses FAISS to find the most relevant text chunks for each claim."
                        />
                        <StageCard
                            icon={<Brain size={24} />}
                            title="3. Reasoning"
                            desc="Dual-perspective analysis (Support vs Contradiction) using Ollama."
                        />
                        <StageCard
                            icon={<FileCheck size={24} />}
                            title="4. Verdict"
                            desc="Synthesizes analysis into a final verdict with confidence score."
                        />
                    </div>
                </div>

                <div className="glass-panel p-8">
                    <h2 className="text-xl font-bold text-white mb-4">Configuration</h2>
                    <div className="space-y-4">
                        <div className="flex justify-between py-3 border-b border-border-color">
                            <span className="text-text-secondary">LLM Model</span>
                            <span className="text-white font-mono">mistral:7b-instruct-q4_0</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-border-color">
                            <span className="text-text-secondary">Chunk Size</span>
                            <span className="text-white font-mono">300 tokens</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-border-color">
                            <span className="text-text-secondary">Retrieval Top-K</span>
                            <span className="text-white font-mono">5 chunks</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StageCard = ({ icon, title, desc }) => (
    <div className="bg-bg-hover p-4 rounded-lg flex items-start gap-4 border border-border-color">
        <div className="text-accent-primary mt-1">{icon}</div>
        <div>
            <h3 className="text-white font-bold mb-1">{title}</h3>
            <p className="text-sm text-text-secondary">{desc}</p>
        </div>
    </div>
);

export default Docs;
